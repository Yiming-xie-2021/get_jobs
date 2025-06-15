import requests
import json
import datetime
import os

# Adjusted import to be relative if 'config' is a sibling package to 'utils' within 'src'
# This assumes 'src' is in Python's path.
from config.settings import Settings

def send_wechat_notification(settings: Settings, title: str, message: str):
    if not settings.bot.is_send or not settings.hook_url:
        print("WeChat notification not sent (disabled or no hook URL).")
        return

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": f"**{title}**\n{message}"
        }
    }
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(settings.hook_url, data=json.dumps(payload), headers=headers, timeout=10)
        response.raise_for_status()
        print(f"WeChat notification sent: {title}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending WeChat notification: {e}")

def send_bark_notification(settings: Settings, title: str, message: str):
    if not settings.bot.is_bark_send or not settings.bark_url:
        print("Bark notification not sent (disabled or no bark URL).")
        return

    # Ensure message and title are URL-encoded for Bark
    bark_api_url = f"{settings.bark_url.rstrip('/')}/{requests.utils.quote(title)}/{requests.utils.quote(message)}"
    try:
        response = requests.get(bark_api_url, timeout=10)
        response.raise_for_status()
        print(f"Bark notification sent: {title}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending Bark notification: {e}")

def send_notification(settings: Settings, title: str, message: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"{message}\n\n*Reported at: {timestamp}*"

    print(f"--- Notification ---")
    print(f"Title: {title}")
    print(f"Message (raw): {message}") # Print raw message for clarity before timestamp
    print(f"Full Message (with timestamp): {full_message}")
    print(f"--------------------")

    send_wechat_notification(settings, title, full_message)
    send_bark_notification(settings, title, full_message)

if __name__ == '__main__':
    print("Testing bot notifications (direct run - output only)...")

    # Create dummy settings for local testing of this script
    # This part will only be executed if bot.py is run directly.
    class DummyBotConfig:
        is_send = True # Test actual sending if URLs are real and you want to test
        is_bark_send = True

    class DummySettingsForBotTest:
        bot = DummyBotConfig()
        # Provide actual URLs via environment variables for real testing if desired
        # e.g. TEST_HOOK_URL="your_actual_wechat_hook" TEST_BARK_URL="your_actual_bark_hook" python src/utils/bot.py
        hook_url = os.getenv("TEST_HOOK_URL")
        bark_url = os.getenv("TEST_BARK_URL")

    test_settings = DummySettingsForBotTest()

    if not test_settings.hook_url:
        print("TEST_HOOK_URL environment variable not set. WeChat test will be a dry run.")
    if not test_settings.bark_url:
        print("TEST_BARK_URL environment variable not set. Bark test will be a dry run.")

    print(f"Attempting WeChat: {test_settings.bot.is_send}, URL: {test_settings.hook_url or 'Not set'}")
    print(f"Attempting Bark: {test_settings.bot.is_bark_send}, URL: {test_settings.bark_url or 'Not set'}")

    send_notification(test_settings, "Test Notification from bot.py", "This is a test message.")
