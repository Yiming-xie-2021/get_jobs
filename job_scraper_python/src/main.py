import os
import sys

try:
    from config.settings import load_settings
except ImportError as e:
    print(f"Error importing load_settings: {e}")
    print("Current sys.path:", sys.path)
    print("Current working directory:", os.getcwd())
    config_path_to_check = os.path.join(os.path.dirname(__file__), 'config')
    if os.path.exists(config_path_to_check):
        print(f"Contents of {config_path_to_check}: {os.listdir(config_path_to_check)}")
    else:
        print(f"{config_path_to_check} does not exist.")
    sys.exit(1)


def main():
    print("Loading settings from src/main.py...")
    settings = load_settings(config_file_name="config.yaml")
    print("Settings loaded successfully.")

    if settings.boss:
        print(f"Boss keywords: {settings.boss.keywords}")
        print(f"Boss say_hi: {settings.boss.say_hi}")
        print(f"Boss debugger: {settings.boss.debugger}")

    if settings.bot:
        print(f"Bot notifications enabled: {settings.bot.is_send}")

    if settings.hook_url:
        print(f"WeChat Hook URL: {settings.hook_url}")
    else:
        print("WeChat Hook URL not found in .env (this is normal if not set)")

    print("\nPython job scraper project: configuration loaded.")

if __name__ == "__main__":
    main()
