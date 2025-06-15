print("Hello from test_output.py (testing app_config.py with sys.path modification)")
import sys
import os

# Add the current directory (which should be /app/job_scraper_python) to sys.path
# This helps Python find the 'src' package.
sys.path.insert(0, os.getcwd())
print(f"Current working directory: {os.getcwd()}")
print(f"Sys.path: {sys.path}")

print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")


print("Attempting to import project files...")
try:
    print("Attempting: import src.config.app_config as config_module")
    import src.config.app_config as config_module
    print("Successfully imported src.config.app_config as config_module")

    # This is where the print statements from app_config.py should appear if it's executing

    print("Attempting to access config_module.TEST_VAR")
    test_var_val = config_module.TEST_VAR
    print(f"Successfully accessed config_module.TEST_VAR: {test_var_val}")

    print("Attempting: from src.config.app_config import load_settings")
    from src.config.app_config import load_settings
    print("Successfully imported load_settings")

    settings_obj = load_settings(config_path="data/config.yaml")
    print("Successfully called load_settings()")
    if settings_obj.hook_url:
        print(f"Hook URL from test: {settings_obj.hook_url}")

except Exception as e:
    print(f"Error: {e}")

print("Test script finished.")
