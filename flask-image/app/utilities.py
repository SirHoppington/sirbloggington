import re

def estimate_reading_time(text: str, WPM: int = 200) -> int:
    total_words = len(re.findall(r'\w+', text))
    time_minute = total_words // WPM + 1
    if time_minute == 0:
        time_minute = 1
    elif time_minute > 60:
        return str(time_minute // 60) + 'h'
    return str(time_minute) + ' min read'