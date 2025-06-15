import os
import time
import json
import urllib.parse
import re
from decimal import Decimal, InvalidOperation
import datetime
from typing import List, Optional, Set, Dict, Tuple

from playwright.sync_api import Page, BrowserContext, ElementHandle, Locator

from config.settings import Settings, BossConfig
from utils.playwright_utils import (
    init_playwright, close_playwright, get_page, new_page,
    navigate_to_url, load_cookies, save_cookies, click_element,
    fill_input, wait_for_selector, take_screenshot, scroll_page_down
)
from utils.models import Job
from utils.bot import send_notification
from utils.project_root import DATA_DIR
from utils.job_utils import random_short_delay, format_duration
import scrapers.boss_locators as locators
from services.ai_service import AIService

class BossScraper:
    SITE_NAME = "boss"
    HOME_URL = "https://www.zhipin.com"
    BASE_SEARCH_URL = "https://www.zhipin.com/web/geek/job?"
    LOGIN_URL = "https://www.zhipin.com/web/user/?ka=header-login"
    POST_LOGIN_URL_INDICATOR = "/web/geek/"

    def __init__(self, settings: Settings):
        self.settings = settings; self.config: BossConfig = settings.boss
        self.page: Optional[Page] = None; self.context: Optional[BrowserContext] = None
        self.blacklisted_companies: Set[str] = set(); self.blacklisted_recruiters: Set[str] = set()
        self.blacklisted_jobs: Set[str] = set(); self.applied_jobs_this_run: List[Job] = []
        self.data_json_path = os.path.join(DATA_DIR, "data.json")
        self.current_search_keyword: Optional[str] = None
        self._load_blacklist_data(); self.ai_service = AIService(settings)

    def _load_blacklist_data(self): # Same as previous subtask
        if os.path.exists(self.data_json_path):
            try:
                with open(self.data_json_path, 'r', encoding='utf-8') as f: data = json.load(f)
                self.blacklisted_companies=set(data.get("blackCompanies",[])); self.blacklisted_recruiters=set(data.get("blackRecruiters",[])); self.blacklisted_jobs=set(data.get("blackJobs",[]))
            except Exception as e: print(f"Err loading blacklist: {e}")
    def _save_blacklist_data(self): # Same as previous subtask
        os.makedirs(DATA_DIR, exist_ok=True)
        try:
            with open(self.data_json_path, 'w', encoding='utf-8') as f: json.dump({"blackCompanies": sorted(list(self.blacklisted_companies)), "blackRecruiters": sorted(list(self.blacklisted_recruiters)), "blackJobs": sorted(list(self.blacklisted_jobs))}, f, ensure_ascii=False, indent=4)
        except Exception as e: print(f"Err saving blacklist: {e}")
    def _is_logged_in(self) -> bool: # Same as previous subtask
        if not self.page: return False
        url_ok = self.POST_LOGIN_URL_INDICATOR in self.page.url and "login" not in self.page.url
        if url_ok and ("/web/geek/job" in self.page.url or "/web/geek/chat" in self.page.url or "/web/geek/mine" in self.page.url): return True
        return bool(self.page.query_selector(locators.USER_AVATAR_OR_MENU)?.is_visible(timeout=1000))
    def login(self) -> bool: # Same as previous subtask (simplified)
        if not self.page or not self.context: return False
        if load_cookies(self.context,self.SITE_NAME) and navigate_to_url(self.page, self.HOME_URL+"/web/geek/job-recommend") and time.sleep(1) is None and self._is_logged_in(): return True
        if not navigate_to_url(self.page, self.LOGIN_URL): return False
        if not wait_for_selector(self.page, locators.QR_CODE_IMAGE, 20000): print("QR not found"); return False
        print("QR Scan needed. Waiting 120s..."); st=time.time()
        while time.time()-st < 120:
            if self._is_logged_in(): save_cookies(self.page,self.SITE_NAME); return True
            time.sleep(3)
        return False
    def _get_search_url(self, city:str, kw:str) -> str: # Same
        p={"query":kw,"city":city};sc=self.config.salary;se=self.config.experience
        if sc and sc!="不限":p["salary"]=sc
        if se and "不限" not in se:p["experience"]=se[0] if isinstance(se,list) else se
        return f"{self.BASE_SEARCH_URL}{urllib.parse.urlencode(p)}"
    def _is_target_job(self, jn:str, kw:str)->bool: # Same
        if not jn:return False;jnl=jn.lower();kwl=kw.lower()
        if self.config.key_filter and kwl not in jnl:return False
        aikw=any(k in kwl for k in ["ai","大模型","算法"]);dp=any(d in jnl for d in ["设计","产品","运营"]);eaj=any(a in jnl for a in ["ai","算法"])
        return not(aikw and dp and not eaj)
    def _is_dead_hr(self, act:Optional[str])->bool: # Same
        if not self.config.filter_dead_hr or not act:return False
        return any(ds in act for ds in self.config.dead_status)
    def _parse_salary(self,stxt:str)->Tuple[Optional[Decimal],Optional[Decimal],Optional[int],bool]: #Same
        if not stxt:return None,None,12,False
        stl=stxt.lower();m=12;dly="/day"in stl or"元/天"in stl
        mm=re.search(r'·(\d+)薪|(\d+)薪',stl);
        if mm:m=int(mm.group(1)or mm.group(2));stl=re.sub(r'·?\d+薪',"",stl).strip()
        scl=stl.replace('k','').replace('元/天','').replace('/day','').replace('以上','').replace('以下','');pts=scl.split('-');min_s,max_s=None,None
        try:
            if len(pts)==1:min_s=max_s=Decimal(pts[0].strip())
            elif len(pts)==2:min_s=Decimal(pts[0].strip());max_s=Decimal(pts[1].strip())
            if dly and min_s:cf=Decimal('21.75')/Decimal('1000');min_s*=cf;max_s=(max_s*cf)if max_s else min_s
        except InvalidOperation:return None,None,m,dly
        return min_s,max_s,m,dly
    def _is_salary_not_expected(self,jst:Optional[str])->bool: #Same
        if not jst or not self.config.expected_salary:return False
        emin=Decimal(self.config.expected_salary[0]);emax=Decimal(self.config.expected_salary[1])if len(self.config.expected_salary)>1 else emin
        jmin,jmax,_,_=self._parse_salary(jst)
        if jmin is None:return True
        return not(jmax>=emin and jmin<=emax)

    def _process_job_details_and_apply(self, job: Job, main_page: Page): # Image resume logic added
        if not job.href or not self.context: print("Missing job link/context."); return
        print(f"  Processing: {job.job_name} @ {job.company_name}")
        detail_page = new_page()
        if not detail_page: print("Failed to create new page."); return
        try:
            if not navigate_to_url(detail_page, job.href): detail_page.close(); return
            time.sleep(max(1, self.config.wait_time // 2 if self.config.wait_time else 2))

            job.salary = detail_page.query_selector(locators.JOB_DETAIL_SALARY_TEXT)?.text_content().strip() or job.salary
            job.recruiter = detail_page.query_selector(locators.RECRUITER_INFO_TEXT)?.text_content().strip().split("\n")[0] or "N/A"
            hr_active_time = detail_page.query_selector(locators.HR_ACTIVE_TIME_TEXT)?.text_content().strip()
            job_description = detail_page.query_selector(locators.JOB_DESCRIPTION_TEXT)?.inner_text() or ""
            job.details_extracted = True

            if self._is_dead_hr(hr_active_time) or self._is_salary_not_expected(job.salary) or (job.recruiter and job.recruiter in self.blacklisted_recruiters):
                job.applied_status = "Filtered"; detail_page.close(); return # Add reason to status if needed

            chat_btn = detail_page.query_selector(locators.CHAT_BUTTON) or detail_page.locator('button:has-text("沟通")').first
            if not chat_btn?.is_visible(timeout=1000): job.applied_status="Err:NoChatBtn";detail_page.close();return
            chat_btn.click(); time.sleep(1.5)

            say_hi = self.config.say_hi
            if self.config.enable_ai and self.ai_service: # enable_ai on BossConfig, not global AiConfig.enable_ai for this decision
                custom_greeting = self.ai_service.generate_custom_greeting(job_description, job.job_name or "", say_hi, self.current_search_keyword or "")
                if custom_greeting: say_hi = custom_greeting; print("    Using AI greeting.")
                else: print("    AI no greeting, using default.")

            if not fill_input(detail_page, locators.CHAT_INPUT_TEXTAREA, say_hi): job.applied_status="Err:ChatInput";detail_page.close();return

            # --- IMAGE RESUME LOGIC ---
            if self.config.send_img_resume:
                print("    Attempting to send image resume...")
                resume_filename = self.config.resume_filename or "resume.jpg" # Uses new BossConfig field
                resume_path = os.path.join(DATA_DIR, resume_filename)
                if os.path.exists(resume_path):
                    try:
                        upload_input = detail_page.locator(locators.IMAGE_UPLOAD_INPUT)
                        # Some sites need the input to be forced visible if it's hidden by CSS
                        # Example: upload_input.evaluate('el => el.style.display = "block"')
                        upload_input.set_input_files(resume_path)
                        time.sleep(self.config.wait_time // 2 if self.config.wait_time else 2) # Wait for upload preview
                        print(f"    Image resume '{resume_filename}' set for upload.")
                        # Note: Actual send often happens with text message, or needs separate image send button.
                        # This assumes setting file is part of the send process triggered by text send.
                    except Exception as e_img:
                        print(f"    Error during image resume upload: {e_img}")
                        take_screenshot(detail_page, f"{self.SITE_NAME}_resume_error")
                else:
                    print(f"    Resume file '{resume_filename}' not found at {resume_path}. Skipping image.")
            # --- END IMAGE RESUME LOGIC ---

            send_btn = detail_page.query_selector(locators.SEND_BUTTON_ACTION)
            if not send_btn?.is_enabled(timeout=2000): job.applied_status="Err:SendBtn";detail_page.close();return

            if self.config.debugger: print(f"    DEBUG: Would send: '{say_hi}'")
            else: send_btn.click(); print("    Message sent."); time.sleep(1)

            job.applied_status="Applied"; self.applied_jobs_this_run.append(job)
            print(f"    Applied: {job.job_name}")
        except Exception as e: job.applied_status=f"Err:{e.__class__.__name__}";take_screenshot(detail_page,"job_detail_err")
        finally:
            random_short_delay(1,2); detail_page.close(); main_page.bring_to_front()

    def search_and_process_jobs(self, city:str, kw:str): # Same as previous
        if not self.page:return;print(f"Searching '{kw}' in '{city}'...")
        city_code=self.config.custom_city_code.get(city,city)
        url=self._get_search_url(city_code,kw)
        if not navigate_to_url(self.page,url):return
        time.sleep(1);processed_this_search:Set[str]=set();stale=0;max_s=3;count=0
        while stale<max_s:
            cards=self.page.locator(locators.JOB_CARD_BOX).all();new_cards=0
            for card in cards:
                link_el=card.query_selector(locators.JOB_NAME_LINK);link_raw=link_el.get_attribute("href")if link_el else None
                if not link_raw:continue
                link=urllib.parse.urljoin(self.HOME_URL,link_raw)
                if link in processed_this_search or link in self.blacklisted_jobs:continue
                new_cards+=1;processed_this_search.add(link)
                name_el=card.query_selector(locators.COMPANY_NAME_TEXT);job_name=link_el.text_content().strip()if link_el else"N/A"
                comp_name=name_el.text_content().strip()if name_el else"N/A"
                if comp_name in self.blacklisted_companies or not self._is_target_job(job_name,kw):continue
                area_el=card.query_selector(locators.JOB_AREA_TEXT);tags_el=card.query_selector_all(locators.TAG_LIST_ITEMS)
                job=Job(href=link,job_name=job_name,company_name=comp_name,job_area=area_el.text_content().strip()if area_el else"N/A",company_tag="·".join([t.text_content().strip()for t in tags_el]),site_name=self.SITE_NAME)
                self._process_job_details_and_apply(job,self.page);count+=1;self.blacklisted_jobs.add(link)
                random_short_delay(self.config.wait_time, (self.config.wait_time or 1)+2)
            if new_cards==0:stale+=1
            else:stale=0
            if self.page.query_selector(locators.NO_MORE_JOBS_TEXT)?.is_visible():break
            scroll_page_down(self.page,1,1);time.sleep(max(2,self.config.wait_time or 2))
        print(f"Finished '{kw}' in '{city}'. Processed {count} jobs.")
    def setup_browser(self, headless:Optional[bool]=None): # Same
        eff_hl=not self.config.debugger if headless is None else headless;init_playwright(headless=eff_hl)
        self.page=get_page();self.context=self.page.context if self.page else None
        if not self.page or not self.context:raise Exception("Playwright init fail.")
    def close_browser(self): # Same
        if self.page and self.context:save_cookies(self.page,self.SITE_NAME)
        self._save_blacklist_data();close_playwright()
    def run(self): # Same
        start_t=time.time();self.applied_jobs_this_run=[];self.current_search_keyword=None
        try:
            self.setup_browser()
            if not self.login():send_notification(self.settings,"Boss Login Fail","");return
            send_notification(self.settings,"Boss Login OK","Search started.")
            for city in self.config.city_code:
                for kw in self.config.keywords:self.current_search_keyword=kw;self.search_and_process_jobs(city,kw);random_short_delay(3,7)
            summary=f"Boss run: {format_duration(datetime.datetime.fromtimestamp(start_t),datetime.datetime.now())}, Applied: {len(self.applied_jobs_this_run)} jobs."
            send_notification(self.settings,"Boss Summary",summary+"\nApplied:\n"+"\n".join([f"-{j.job_name}@{j.company_name}"for j in self.applied_jobs_this_run]))
        except Exception as e:send_notification(self.settings,"Boss ERROR",f"{e}"); _=self.page and take_screenshot(self.page,"run_error")
        finally:self.close_browser();print("Boss run complete.")

if __name__ == '__main__': # Same, but ensure resume_filename in dummy config
    import sys; crp=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','..'));sys.path.insert(0,crp) if crp not in sys.path else None
    from config.settings import load_settings;from services.ai_service import AIService
    print("Testing BossScraper with image resume logic...")
    cfg_p=os.path.join(DATA_DIR,'config.yaml');env_p=os.path.join(DATA_DIR,'.env')
    if not os.path.exists(cfg_p):
        os.makedirs(DATA_DIR,exist_ok=True)
        with open(cfg_p,'w',encoding='utf-8')as f:f.write("boss:\n  keywords:['QA']\n  city_code:['上海']\n  custom_city_code:{'上海':'c101020100'}\n  debugger:true\n  wait_time:5\n  send_img_resume:true\n  resume_filename:'test_resume.jpg'\n  enable_ai:false\nai:\n  enable_ai:false\nbot:\n  is_send:false\n")
    if not os.path.exists(env_p):
        os.makedirs(DATA_DIR,exist_ok=True)
        with open(env_p,'w',encoding='utf-8')as f:f.write("API_KEY=DUMMY\n")
    # Create dummy resume for test
    dummy_resume_path = os.path.join(DATA_DIR, "test_resume.jpg")
    if not os.path.exists(dummy_resume_path):
        with open(dummy_resume_path, "w") as f: f.write("dummy resume content for test")
        print(f"Created dummy resume file at {dummy_resume_path}")

    gs=load_settings();scraper=BossScraper(gs);scraper.run()
