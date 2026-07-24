# scop: kernel min v1.4.5
from __future__ import annotations

import html
from pathlib import Path
import yaml
from telethon import events
from telethon.errors import (
    ChannelInvalidError,
    ChannelPrivateError,
    FloodWaitError,
    RPCError,
)
import asyncio

from core.lib.loader.module_base import ModuleBase, command
from core.lib.loader.module_config import ConfigValue, EntityLike, Integer, ModuleConfig, Row

# Local imports
from randomedits_lib import _MixinUtils

def _load_strings() -> dict[str, dict[str, str]]:
    for root in (Path(__file__).resolve().parent, *(Path(path) for path in globals().get("__path__", ()))):
        path = root / "assets" / "strings_random_media.yaml"
        if path.is_file():
            with path.open("r", encoding="utf-8") as file:
                return yaml.safe_load(file)

    raise FileNotFoundError("assets/strings_random_media.yaml")

class RandomEdits(
    _MixinUtils,
    ModuleBase
    ):

    name = "RandomEdits"
    version = "1.0.5"
    author = "@modulesanhedonuya && porting by @Hairpin00"
    description = {
        "ru": "Отправляет случайный эдит",
        "en": "Sends a random edit",
    }

    strings: dict[str, dict[str, str]] = _load_strings()

    config = ModuleConfig(
        ConfigValue(
            "channel",
            "randomeditsforme",
            description=lambda mod: mod.strings('key_channel'),
            validator=EntityLike(),
        ),
        Row(),
        ConfigValue(
            "sample_limit",
            500,
            description=lambda mod: mod.strings('key_sample_limit'),
            validator=Integer(min=1, max=500),
        ),
    )

    async def on_load(self) -> None:
        await super().on_load()

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
            await asyncio.sleep(3)
            await status.delete()
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
