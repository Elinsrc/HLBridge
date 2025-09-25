# SPDX-License-Identifier: MIT
# Copyright (c) 2018-2024 Amano LLC
# Copyright (c) 2025 Elinsrc

from __future__ import annotations

import yaml
import logging
from collections.abc import Callable
from functools import partial
from pathlib import Path

from hydrogram.enums import ChatType
from hydrogram.types import CallbackQuery, InlineQuery, Message, ChatMemberUpdated

from hlbridge.database.localization import get_db_lang


enabled_locales: list[str] = [
    "en-GB",  # English (United Kingdom)
    "ru-RU",  # Russian
]


default_language: str = "en-GB"


def cache_locales(locales: list[str]) -> dict[str, dict[str, str]]:
    # init ldict with empty dict
    locales_dict = {}

    for locale in locales:
        file = Path("locales", f"{locale}.yml")

        if not file.exists():
            logging.warning(
                "Unable to find locale %s. This locale will fallback to %s",
                locale,
                default_language,
            )
            continue

        locale_keys = yaml.safe_load(file.open("r", encoding="utf8"))

        if "_meta_language_name" not in locale_keys or "_meta_language_flag" not in locale_keys:
            logging.warning(
                "Locale has required keys _meta_language_name or _meta_language_flag missing. This locale will not be loaded."
            )
            continue

        locales_dict[locale] = locale_keys

    return locales_dict


langdict = cache_locales(enabled_locales)


def get_locale_string(
    language: str,
    key: str,
) -> str:
    if "@" in language and language.split("@", 1)[0] in langdict:
        # if an @ (tone modifier) is present, try to get string from parent language if nullish
        string = langdict[language].get(key) or langdict[language.split("@", 1)[0]].get(key)
    else:
        string = langdict[language].get(key)

    # return and fallback if nullish
    return string or langdict[default_language].get(key) or key


Strings = Callable[[str], str]


async def get_lang(message: CallbackQuery | Message | InlineQuery, client = None) -> str:
    if isinstance(message, int):
        chat_id = message
        chat = await client.get_chat(chat_id)
        chat_type = chat.type
        lang = await get_db_lang(chat_id, chat_type)
        return lang if lang in enabled_locales else default_language
    elif isinstance(message, CallbackQuery):
        chat = message.message.chat if message.message else message.from_user
        chat_type = message.message.chat.type if message.message else ChatType.PRIVATE
    elif isinstance(message, Message):
        chat = message.chat
        chat_type = message.chat.type
    elif isinstance(message, InlineQuery):
        chat = message.from_user
        chat_type = ChatType.PRIVATE
    elif isinstance(message, ChatMemberUpdated):
        chat = message.chat
        chat_type = message.chat.type
    else:
        raise TypeError(f"Update type '{message.__name__}' is not supported.")

    lang = await get_db_lang(chat.id, chat_type)

    if chat_type == ChatType.PRIVATE:
        lang = lang or message.from_user.language_code or default_language
    else:
        lang = lang or default_language
    # User has a language_code without hyphen
    if len(lang.split("-")) == 1:
        # Try to find a language that starts with the provided language_code
        for locale_ in enabled_locales:
            if locale_.startswith(lang):
                lang = locale_
    elif lang.split("-")[1].islower():
        lang = lang.split("-")
        lang[1] = lang[1].upper()
        lang = "-".join(lang)
    return lang if lang in enabled_locales else default_language


def use_chat_lang(func: Callable):
    """Decorator to get the chat language and pass it to the function."""

    async def wrapper(client, message, *args, **kwargs):
        lang = await get_lang(message)

        lfunc = partial(get_locale_string, lang)
        return await func(client, message, *args, lfunc, **kwargs)

    return wrapper
