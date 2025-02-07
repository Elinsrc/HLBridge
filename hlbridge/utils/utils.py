import re
from datetime import datetime

class Utils:
    @staticmethod
    def get_current_time():
        return datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    @staticmethod
    def remove_color_tags(text):
        return re.sub(r'\^\d', '', text)

    @staticmethod
    def user_msg(message):
        return ' '.join(message.text.split(' ')[1:])

    @staticmethod
    def format_time(seconds):
        seconds = int(float(seconds))
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        remaining_seconds = seconds % 60

        time_components = []
        if days > 0:
            time_components.append(f"{days}d")
        if hours > 0:
            time_components.append(f"{hours}h")
        if minutes > 0:
            time_components.append(f"{minutes}m")
        if remaining_seconds > 0 or not time_components:
            time_components.append(f"{remaining_seconds}s")

        return ' '.join(time_components)
