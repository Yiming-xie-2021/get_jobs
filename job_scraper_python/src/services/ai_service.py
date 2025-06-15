import requests
import json
from typing import Optional, Dict, Any
from config.settings import Settings, AiConfig

class AIService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.ai_config: AiConfig = settings.ai
        self.api_key: Optional[str] = settings.api_key
        self.base_url: Optional[str] = settings.base_url
        self.model: Optional[str] = settings.model

    def generate_custom_greeting(
        self,
        job_description: str,
        job_title: str,
        original_say_hi: str,
        search_keyword: str
    ) -> Optional[str]:

        if not self.ai_config.enable_ai:
            # print("AI service call skipped: AI not enabled in config.") # Can be noisy
            return None

        if not self.api_key or not self.base_url or not self.model:
            print("AI service not configured (missing API key, base URL, or model). Using default greeting.")
            return None

        user_intro_str = str(self.ai_config.introduce if self.ai_config.introduce else "")
        search_keyword_str = str(search_keyword if search_keyword else "")
        job_title_str = str(job_title if job_title else "")
        job_description_str = str(job_description[:1500] if job_description else "")
        original_say_hi_str = str(original_say_hi if original_say_hi else "")

        try:
            prompt = self.ai_config.prompt % (
                user_intro_str, search_keyword_str, job_title_str,
                job_description_str, original_say_hi_str
            )
        except TypeError:
            print("Error formatting AI prompt. Check prompt template & args. Using default."); return None

        payload = {
            "model": self.model, "messages": [
                {"role": "system", "content": "You are a helpful assistant that crafts concise job application greetings. If the job is not a match, respond with only the word 'false'."},
                {"role": "user", "content": prompt}
            ], "max_tokens": 200, "temperature": 0.7
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        try:
            endpoint = self.base_url.rstrip("/")
            if "/v1" in endpoint and not endpoint.endswith("/chat/completions"):
                 endpoint = endpoint + "/chat/completions"

            # print(f"Sending request to AI service at {endpoint} with model {self.model}...") # Debug
            response = requests.post(endpoint, headers=headers, json=payload, timeout=45)
            response.raise_for_status()
            response_data = response.json()

            if response_data.get("choices") and len(response_data["choices"]) > 0:
                content_message = response_data["choices"][0].get("message", {}).get("content")
                if content_message:
                    content_lower_stripped = content_message.lower().strip()
                    if content_lower_stripped in ["false", "\"false\"", "'false'"]:
                        print("AI indicated job is not a good match (returned 'false')."); return None
                    # print(f"AI generated greeting (first 100 chars): {content_message[:100]}...") # Debug
                    return content_message.strip()
                # else: print("AI response content is empty.") # Debug
            # else: print(f"AI response format unexpected: {response_data}") # Debug
        except requests.exceptions.Timeout: print(f"Timeout calling AI service at {endpoint}.")
        except requests.exceptions.RequestException as e: print(f"Error calling AI service: {e}")
        except (json.JSONDecodeError, KeyError) as e: print(f"Error parsing AI service response: {e}")
        return None

if __name__ == '__main__':
    import os, sys
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_script_dir, '..', '..'))
    if project_root not in sys.path: sys.path.insert(0, project_root)
    from config.settings import load_settings
    print("Testing AI Service (direct run)...")
    data_dir_local_test = os.path.join(project_root, 'data')
    config_yaml_path_test = os.path.join(data_dir_local_test, 'config.yaml')
    env_path_test = os.path.join(data_dir_local_test, '.env')
    if not os.path.exists(config_yaml_path_test):
        print(f"Creating dummy {config_yaml_path_test}"); os.makedirs(data_dir_local_test, exist_ok=True)
        with open(config_yaml_path_test, 'w', encoding='utf-8') as f: f.write("ai:\n  enable_ai: true\n  introduce: 'Skills: Py, Java.'\n  prompt: 'Intro: %s. Keyword: %s. Title: %s. JD: %s. Original Hi: %s. Custom greeting or false.'\nbot:\n  is_send: false\n")
    if not os.path.exists(env_path_test):
        print(f"Creating dummy {env_path_test}"); os.makedirs(data_dir_local_test, exist_ok=True)
        with open(env_path_test, 'w', encoding='utf-8') as f: f.write("API_KEY=DUMMY_KEY\nBASE_URL=https://api.example.com/v1\nMODEL=dummy-model\n")
    settings_obj = load_settings(); ai_service_obj = AIService(settings_obj)
    if not settings_obj.ai.enable_ai: print("AI disabled in config.")
    elif "DUMMY_KEY" in (settings_obj.api_key or ""): print("Dummy API key, skipping real AI call.")
    else: print("Attempting real AI call..."); greeting = ai_service_obj.generate_custom_greeting("JD: Python dev needed.", "Sr Py Dev", "Hi.", "Python"); print(f"Test Greeting: {greeting or 'None'}")
