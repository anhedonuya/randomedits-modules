from __future__ import annotations

from typing import Any
from random import choice

class _MixinUtils:

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

__all__ = [
    '_MixinUtils'
]
