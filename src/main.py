from src.config.settings import load_settings

def main():
    print("Loading settings...")
    settings = load_settings(config_path="data/config.yaml") # Assuming config.yaml is in data/
    print("Settings loaded.")

    # Example: Accessing a specific config
    if settings.boss:
        print(f"Boss keywords: {settings.boss.keywords}")
        print(f"Boss say_hi: {settings.boss.say_hi}")

    if settings.bot:
        print(f"Bot notifications enabled: {settings.bot.is_send}")

    if settings.hook_url:
        print(f"WeChat Hook URL: {settings.hook_url}")

    print("\nPython job scraper project initialized.")
    print("Next steps would be to implement scraper logic and utilities.")

if __name__ == "__main__":
    main()
