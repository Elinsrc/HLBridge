import re
from datetime import datetime
import logging
from loguru import logger
from subprocess import run


class Utils:
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


class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())


class GitInfo:
    @staticmethod
    def get_commit():
        return (
            run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, check=False)
            .stdout.decode()
            .strip()
            or "None"
        )

    @staticmethod
    def get_version_number():
        return (
            run(["git", "rev-list", "--count", "HEAD"], capture_output=True, check=False)
            .stdout.decode()
            .strip()
            or "0"
        )
