import random
import time
import datetime

def get_random_number_in_range(min_val: int, max_val: int) -> int:
    return random.randint(min_val, max_val)

def random_short_delay(min_seconds: float = 0.5, max_seconds: float = 2.0):
    time.sleep(random.uniform(min_seconds, max_seconds))

def format_duration(start_time: datetime.datetime, end_time: datetime.datetime) -> str:
    duration = end_time - start_time
    total_seconds = int(duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

if __name__ == '__main__':
    print(f"Random number: {get_random_number_in_range(1, 10)}")
    print("Delaying for a bit...")
    random_short_delay(0.1,0.2)
    print("Delayed.")
    start = datetime.datetime.now() - datetime.timedelta(hours=1, minutes=30, seconds=15)
    end = datetime.datetime.now()
    print(f"Formatted duration: {format_duration(start, end)}")
