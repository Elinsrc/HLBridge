# SPDX-License-Identifier: MIT
# Copyright (c) 2018-2024 Amano LLC
# Copyright (c) 2025 Elinsrc

from __future__ import annotations

from functools import partial, wraps
from typing import TYPE_CHECKING

from hydrogram import Client, StopPropagation
from hydrogram.enums import ChatType
from hydrogram.types import CallbackQuery, ChatPrivileges, Message

from hlbridge.utils.localization import (
    get_lang,
    get_locale_string,
)
from hlbridge.utils.utils import check_perms

from hlbridge.database.settings import get_settings, user_owner
from hlbridge.database.admins import user_admin

if TYPE_CHECKING:
    from collections.abc import Callable


def require_admin(
    permissions: ChatPrivileges | None = None,
    allow_in_private: bool = False,
    complain_missing_perms: bool = True,
):
    """Decorator that checks if the user is an admin in the chat.

    Parameters
    ----------
    permissions: ChatPrivileges
        The permissions to check for.
    allow_in_private: bool
        Whether to allow the command in private chats or not.
    complain_missing_perms: bool
        Whether to complain about missing permissions or not, otherwise the
        function will not be called and the user will not be notified.

    Returns
    -------
    Callable
        The decorated function.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(client: Client, message: CallbackQuery | Message, *args, **kwargs):
            lang = await get_lang(message)
            s = partial(
                get_locale_string,
                lang,
            )

            if isinstance(message, CallbackQuery):
                sender = partial(message.answer, show_alert=True)
                msg = message.message
            elif isinstance(message, Message):
                sender = message.reply_text
                msg = message
            else:
                raise NotImplementedError(
                    f"require_admin can't process updates with the type '{message.__name__}' yet."
                )

            # We don't actually check private and channel chats.
            if msg.chat.type == ChatType.PRIVATE:
                if allow_in_private:
                    return await func(client, message, *args, *kwargs)
                return await sender(s("cmd_private_not_allowed"))
            if msg.chat.type == ChatType.CHANNEL:
                return await func(client, message, *args, *kwargs)
            has_perms = await check_perms(message, permissions, complain_missing_perms, s)
            if has_perms:
                return await func(client, message, *args, *kwargs)
            return None

        return wrapper

    return decorator


def stop_here(func: Callable) -> Callable:
    async def wrapper(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        finally:
            raise StopPropagation

    return wrapper


def owner_only(func):
    async def wrapper(client, message, *args, **kwargs):
        lang = await get_lang(message)
        s = partial(
            get_locale_string,
            lang,
        )
        settings = await get_settings()
        if not settings["owner_id"]:
            return

        is_owner = await user_owner(message.from_user.id)
        if not is_owner:
            await message.reply_text(s("owner_only"))
            return

        return await func(client, message)

    return wrapper


def admin_only(func):
    async def wrapper(client, message, *args, **kwargs):
        lang = await get_lang(message)
        s = partial(
            get_locale_string,
            lang,
        )
        if not (await user_owner(message.from_user.id) or await user_admin(message.from_user.id)):
            await message.reply_text(s("admin_only"))
            return

        return await func(client, message)

    return wrapper
