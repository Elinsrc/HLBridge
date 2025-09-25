# SPDX-License-Identifier: MIT
# Copyright (c) 2018-2024 Amano LLC

from __future__ import annotations

from itertools import zip_longest

from hydrogram import Client, filters
from hydrogram.enums import ChatType
from hydrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from hlbridge.database.localization import set_db_lang
from hlbridge.utils.decorators import require_admin
from hlbridge.utils.localization import Strings, langdict, use_chat_lang


def gen_langs_kb():
    return [
        [
            InlineKeyboardButton(
                f"{langdict[lang]['_meta_language_flag']} {langdict[lang]['_meta_language_name']}",
                callback_data=f"set_lang {lang}",
            )
            for lang in langs
            if lang
        ]
        for langs in zip_longest(*[iter(langdict)] * 2)
    ]


@Client.on_callback_query(filters.regex("^chlang$"))
@Client.on_message(filters.command(["setchatlang", "setlang"]) & filters.group)
@require_admin(allow_in_private=True)
@use_chat_lang
async def chlang(c: Client, m: CallbackQuery | Message, s: Strings):
    if isinstance(m, CallbackQuery):
        msg = m.message
        sender = msg.edit_text
    else:
        msg = m
        sender = msg.reply_text

    keyboard = [*gen_langs_kb()]

    if msg.chat.type == ChatType.PRIVATE:
        keyboard.append([InlineKeyboardButton(s("general_back_btn"), callback_data="start_back")])

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    res = (
        s("language_changer_private")
        if msg.chat.type == ChatType.PRIVATE
        else s("language_changer_chat")
    )

    await sender(res, reply_markup=markup)


@Client.on_callback_query(filters.regex("^set_lang "))
@require_admin(allow_in_private=True)
async def set_chat_lang(c: Client, m: CallbackQuery):
    lang = m.data.split()[1]
    await set_db_lang(m.message.chat.id, m.message.chat.type, lang)

    await set_chat_lang_edit(c, m)


@use_chat_lang
async def set_chat_lang_edit(c: Client, m: CallbackQuery, s: Strings):
    if m.message.chat.type == ChatType.PRIVATE:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        s("general_back_btn"),
                        callback_data="start_back",
                    )
                ]
            ]
        )
    else:
        keyboard = None
    await m.message.edit_text(s("language_changed_successfully"), reply_markup=keyboard)
