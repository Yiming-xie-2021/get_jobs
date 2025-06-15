import yaml
import os
from dotenv import load_dotenv
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
env_path = os.path.join(DATA_DIR, '.env')

if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)

@dataclass
class AiConfig:
    enable_ai: bool = False
    introduce: str = ""
    prompt: str = ""

@dataclass
class BotConfig:
    is_send: bool = False
    is_bark_send: bool = False

@dataclass
class CommonSiteConfig:
    debugger: bool = False
    say_hi: str = "您好,期待可以与您进一步沟通,谢谢！"
    keywords: List[str] = field(default_factory=list)
    city_code: List[str] = field(default_factory=list)
    custom_city_code: Dict[str, str] = field(default_factory=dict)
    experience: List[str] = field(default_factory=list)
    salary: str = "不限"
    degree: List[str] = field(default_factory=list)
    scale: List[str] = field(default_factory=list)
    stage: List[str] = field(default_factory=list)
    expected_salary: List[int] = field(default_factory=list)
    wait_time: int = 10
    filter_dead_hr: bool = True
    send_img_resume: bool = True
    job_type: str = "不限"
    dead_status: List[str] = field(default_factory=lambda: ["2周内活跃","本月活跃","2月内活跃","半年前活跃"])

@dataclass
class BossConfig(CommonSiteConfig):
    next_interval_minutes: Optional[int] = None
    key_filter: Optional[bool] = None
    resume_filename: Optional[str] = "resume.jpg" # Added field

@dataclass
class Job51Config(CommonSiteConfig):
    job_area: List[str] = field(default_factory=list)

@dataclass
class LagouConfig(CommonSiteConfig):
    gj: str = ""

@dataclass
class LiepinConfig(CommonSiteConfig): pass
@dataclass
class ZhilianConfig(CommonSiteConfig): pass

@dataclass
class Settings:
    boss: BossConfig = field(default_factory=BossConfig)
    mobileboss: BossConfig = field(default_factory=BossConfig)
    job51: Job51Config = field(default_factory=Job51Config)
    lagou: LagouConfig = field(default_factory=LagouConfig)
    liepin: LiepinConfig = field(default_factory=LiepinConfig)
    zhilian: ZhilianConfig = field(default_factory=ZhilianConfig)
    ai: AiConfig = field(default_factory=AiConfig)
    bot: BotConfig = field(default_factory=BotConfig)
    hook_url: Optional[str] = os.getenv("HOOK_URL")
    bark_url: Optional[str] = os.getenv("BARK_URL")
    base_url: Optional[str] = os.getenv("BASE_URL")
    api_key: Optional[str] = os.getenv("API_KEY")
    model: Optional[str] = os.getenv("MODEL")

def _recursive_dataclass_parse(config_class, data_dict):
    if not isinstance(data_dict, dict): return data_dict
    field_values = {}
    for f_name, f_type_obj in config_class.__dataclass_fields__.items():
        f_type = f_type_obj.type
        if f_name in data_dict:
            if hasattr(f_type, '__dataclass_fields__'):
                field_values[f_name] = _recursive_dataclass_parse(f_type, data_dict[f_name])
            else: field_values[f_name] = data_dict[f_name]
    return config_class(**field_values)

def load_settings(config_file_name: str = "config.yaml") -> Settings:
    actual_config_path = os.path.join(DATA_DIR, config_file_name)
    raw_config = {}
    if os.path.exists(actual_config_path):
        try:
            with open(actual_config_path, 'r', encoding='utf-8') as f:
                raw_config = yaml.safe_load(f)
            if raw_config is None: raw_config = {}
        except Exception as e:
            print(f"Error loading/parsing YAML from {actual_config_path}: {e}. Using empty config.")
            raw_config = {}
    parsed_settings_data = {}
    for main_key, field_obj in Settings.__dataclass_fields__.items():
        if hasattr(field_obj.type, '__dataclass_fields__'):
            parsed_settings_data[main_key] = _recursive_dataclass_parse(
                field_obj.type, raw_config.get(main_key, {})
            )
    return Settings(**parsed_settings_data)
