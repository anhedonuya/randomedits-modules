# scop: kernel min v1.2.8
from __future__ import annotations

import html
from random import choice
from typing import Any

from telethon import events
from telethon.errors import (
    ChannelInvalidError,
    ChannelPrivateError,
    FloodWaitError,
    RPCError,
)

from core.lib.loader.module_base import ModuleBase, command
from core.lib.loader.module_config import ConfigValue, EntityLike, Integer, ModuleConfig


class RandomEdits(ModuleBase):
    """Отправляет случайный эдит."""

    name = "RandomEdits"
    version = "1.0.2"
    author = "@modulesanhedonuya && porting by @Hairpin00"
    description = {
        "ru": "Отправляет случайный эдит",
        "en": "Sends a random edit",
    }

    strings = {
        "ru": {
            "name": "RandomEdits",
            "pick": '<tg-emoji emoji-id="5427312230767037491">🤔</tg-emoji> <b>Ищу погодь...</b>',
            "no_posts": '<tg-emoji emoji-id="5210952531676504517">❌</tg-emoji> <b>Не удалось найти подходящие эдит.</b>',
            "done": '<tg-emoji emoji-id="5206607081334906820">✔️</tg-emoji> <b>Случайный эдит отправлен ниже.</b>',
            "settings": (
                '<tg-emoji emoji-id="5341715473882955310">⚙️</tg-emoji> <b>Настройки модуля:</b>\n'
                "<b>Канал:</b> <code>{channel}</code>\n"
                "<b>Глубина выборки:</b> <code>{limit}</code>"
            ),
            "bad_channel": '<tg-emoji emoji-id="5210952531676504517">❌</tg-emoji> <b>Канал недоступен или указан неверно.</b>',
            "protected": (
                '<tg-emoji emoji-id="5274099962655816924">❗️</tg-emoji> <b>Telegram запретил повторную отправку этого эдита.</b>\n'
                "<i>Попробуй ещё раз — будет выбран другой эдит.</i>"
            ),
            "flood": (
                '<tg-emoji emoji-id="5395695537687123235">🚨</tg-emoji> <b>Слишком много запросов.</b>\n'
                "<i>Попробуй снова через {seconds} сек.</i>"
            ),
            "rpc_error": '<tg-emoji emoji-id="5210952531676504517">❌</tg-emoji> <b>Ошибка Telegram:</b> <code>{error}</code>',
            "unknown_error": '<tg-emoji emoji-id="5210952531676504517">❌</tg-emoji> <b>Неожиданная ошибка:</b> <code>{error}</code>',
        },
        "en": {
            "name": "RandomEdits",
            "pick": '<tg-emoji emoji-id="5427312230767037491">🤔</tg-emoji> <b>searching...</b>',
            "no_posts": '<tg-emoji emoji-id="5210952531676504517">❌</tg-emoji> <b>No suitable edit were found, sorry.</b>',
            "done": '<tg-emoji emoji-id="5206607081334906820">✔️</tg-emoji> <b>this edit ;).</b>',
            "settings": (
                '<tg-emoji emoji-id="5341715473882955310">⚙️</tg-emoji> <b>Module settings:</b>\n'
                "<b>Channel:</b> <code>{channel}</code>\n"
                "<b>Sample depth:</b> <code>{limit}</code>"
            ),
            "bad_channel": '<tg-emoji emoji-id="5210952531676504517">❌</tg-emoji> <b>Channel is unavailable or invalid.</b>',
            "protected": (
                '<tg-emoji emoji-id="5274099962655816924">❗️</tg-emoji> <b>Telegram blocked forwarding this edit :( </b>\n'
                "<i>Try again — another edit will be selected.</i>"
            ),
            "flood": (
                '<tg-emoji emoji-id="5395695537687123235">🚨</tg-emoji> <b>Too many requests.</b>\n'
                "<i>Try again in {seconds} sec.</i>"
            ),
            "rpc_error": '<tg-emoji emoji-id="5210952531676504517">❌</tg-emoji> <b>Telegram error:</b> <code>{error}</code>',
            "unknown_error": '<tg-emoji emoji-id="5210952531676504517">❌</tg-emoji> <b>Unexpected error:</b> <code>{error}</code>',
        },
    }

    config = ModuleConfig(
        ConfigValue(
            "channel",
            "randomeditsforme",
            description="Юзернейм, ID или ссылка на канал-источник эдитов(лучше не трогать)",
            validator=EntityLike(default="randomeditsforme"),
        ),
        ConfigValue(
            "sample_limit",
            500,
            description="Сколько последних сообщений канала просматривать при выборе",
            validator=Integer(default=500, min=1, max=500),
        ),
    )

    async def on_load(self) -> None:
        config_dict = await self.kernel.get_module_config(self.name, self.config.to_dict())
        self.config.from_dict(config_dict)
        config_dict_clean = {k: v for k, v in self.config.to_dict().items() if v is not None}
        if config_dict_clean:
            await self.kernel.save_module_config(self.name, config_dict_clean)
        self.kernel.store_module_config_schema(self.name, self.config)

    def _normalize_channel(self, value: Any) -> str:
        channel = str(value or "").strip()
        for prefix in ("https://t.me/", "http://t.me/", "t.me/"):
            if channel.startswith(prefix):
                channel = channel.split(prefix, maxsplit=1)[1]
                break
        return channel.strip("/@ ")

    async def _collect_posts(self) -> list[Any]:
        channel = self._normalize_channel(self.config["channel"])
        entity = await self.kernel.client.get_entity(channel)
        messages: list[Any] = []

        async for msg in self.kernel.client.iter_messages(
            entity,
            limit=self.config["sample_limit"],
        ):
            if getattr(msg, "action", None):
                continue
            text = (getattr(msg, "message", None) or "").strip()
            if not (getattr(msg, "media", None) or text):
                continue
            messages.append(msg)

        return messages

    async def _send_random_post(self, chat_id: Any, reply_to: int | None = None) -> tuple[bool, str | None]:
        posts = await self._collect_posts()
        if not posts:
            return False, self.strings("no_posts")

        post = choice(posts)
        caption = getattr(post, "message", None) or None
        media = getattr(post, "media", None)

        if media:
            await self.kernel.client.send_file(
                chat_id,
                file=media,
                caption=caption,
                reply_to=reply_to,
                parse_mode="html",
            )
        else:
            await self.kernel.client.send_message(
                chat_id,
                caption or "",
                reply_to=reply_to,
                parse_mode="html",
            )

        return True, None

    async def _edit_status(self, event: Any, text: str) -> Any:
        if hasattr(event, "edit") and callable(event.edit):
            return await event.edit(text, parse_mode="html")
        return await self.answer(event, text, parse_mode="html")

    @command(
        "randomedit",
        doc={
            "ru": "отправить случайный эдит",
            "en": "send a random edit",
        },
    )
    async def cmd_randomedit(self, event: events.NewMessage.Event) -> None:
        status = await self._edit_status(event, self.strings("pick"))

        try:
            ok, error_text = await self._send_random_post(
                event.chat_id,
                reply_to=getattr(event, "reply_to_msg_id", None),
            )
            if not ok:
                await self._edit_status(status, error_text or self.strings("no_posts"))
                return

            await self._edit_status(status, self.strings("done"))
        except (ChannelPrivateError, ChannelInvalidError, ValueError) as exc:
            self.log.warning("RandomEdits source channel is unavailable: %s", exc)
            await self._edit_status(status, self.strings("bad_channel"))
        except FloodWaitError as exc:
            self.log.warning("RandomEdits hit Telegram flood wait: %s", exc)
            await self._edit_status(
                status,
                self.strings("flood").format(seconds=getattr(exc, "seconds", 0)),
            )
        except RPCError as exc:
            self.log.warning("RandomEdits Telegram RPC error: %s", exc)
            error_text = str(exc)
            lowered = error_text.lower()
            if "protected" in lowered or "forbidden" in lowered or "copy" in lowered:
                await self._edit_status(status, self.strings("protected"))
                return
            await self._edit_status(
                status,
                self.strings("rpc_error").format(error=html.escape(error_text)),
            )
        except Exception as exc:
            self.log.exception("Unexpected RandomEdits error")
            await self._edit_status(
                status,
                self.strings("unknown_error").format(error=html.escape(str(exc))),
            )
