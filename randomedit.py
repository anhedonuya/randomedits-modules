# meta name: RandomEdits
# meta developer: @modulesanhedonuya
# meta version: 1.0.1
# scope: hikka_only

from random import choice

from telethon.errors import ChannelInvalidError, ChannelPrivateError, FloodWaitError, RPCError
from telethon.tl.types import Message

from .. import loader, utils


@loader.tds
class RandomEditsMod(loader.Module):
    """Отправляет случайный эдит из указанного Telegram-канала."""

    strings = {
        "name": "RandomEdits",
        "pick": "<a href=\"tg://emoji?id=5427312230767037491\">🤔</a> <b>Ищу случайный эдит...</b>",
        "no_posts": "<a href=\"tg://emoji?id=5210952531676504517\">❌</a> <b>Не удалось найти подходящие посты в канале.</b>",
        "done": "<a href=\"tg://emoji?id=5206607081334906820\">✔️</a> <b>Случайный эдит отправлен.</b>",
        "settings": (
            "<a href=\"tg://emoji?id=5341715473882955310\">⚙️</a> <b>Настройки модуля:</b>\n"
            "<b>Канал:</b> <code>{channel}</code>\n"
            "<b>Глубина выборки:</b> <code>{limit}</code>"
        ),
        "bad_channel": "<a href=\"tg://emoji?id=5210952531676504517\">❌</a> <b>Канал недоступен или указан неверно.</b>",
        "protected": (
            "<a href=\"tg://emoji?id=5274099962655816924\">❗️</a> <b>Telegram запретил повторную отправку этого медиа.</b>\n"
            "<i>Попробуй ещё раз — будет выбран другой пост.</i>"
        ),
        "flood": (
            "<a href=\"tg://emoji?id=5395695537687123235\">🚨</a> <b>Слишком много запросов.</b>\n"
            "<i>Попробуй снова через {seconds} сек.</i>"
        ),
        "rpc_error": "<a href=\"tg://emoji?id=5210952531676504517\">❌</a> <b>Ошибка Telegram:</b> <code>{error}</code>",
        "unknown_error": "<a href=\"tg://emoji?id=5210952531676504517\">❌</a> <b>Неожиданная ошибка:</b> <code>{error}</code>",
    }

    strings_ru = strings

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "channel",
                "randomeditsforme",
                lambda: "Юзернейм или ссылка на канал-источник эдитов",
                validator=loader.validators.String(min_len=3, max_len=128),
            ),
            loader.ConfigValue(
                "sample_limit",
                40,
                lambda: "Сколько последних сообщений канала просматривать при выборе",
                validator=loader.validators.Integer(minimum=5, maximum=200),
            ),
        )
        self.db = None
        self._client = None

    async def client_ready(self, client, db):
        self._client = client
        self.db = db

    def _normalize_channel(self, value: str) -> str:
        value = (value or "").strip()
        if value.startswith("https://t.me/"):
            value = value.split("https://t.me/", maxsplit=1)[1]
        if value.startswith("t.me/"):
            value = value.split("t.me/", maxsplit=1)[1]
        value = value.strip("/@ ")
        return value

    async def _collect_posts(self) -> list[Message]:
        channel = self._normalize_channel(self.config["channel"])
        entity = await self._client.get_entity(channel)
        messages = []

        async for msg in self._client.iter_messages(entity, limit=self.config["sample_limit"]):
            if not isinstance(msg, Message):
                continue
            if getattr(msg, "action", None):
                continue
            if not (msg.media or (msg.message and msg.message.strip())):
                continue
            messages.append(msg)

        return messages

    async def _send_random_post(self, chat_id, reply_to=None):
        posts = await self._collect_posts()
        if not posts:
            return False, self.strings("no_posts")

        post = choice(posts)
        caption = post.message or None

        if post.media:
            await self._client.send_file(
                chat_id,
                file=post.media,
                caption=caption,
                reply_to=reply_to,
            )
        else:
            await self._client.send_message(
                chat_id,
                caption or "",
                reply_to=reply_to,
            )

        return True, None

    @loader.command(
        ru_doc="Отправить случайный эдит из канала-источника",
        en_doc="Send a random edit from the source channel",
    )
    async def randomeditcmd(self, message: Message):
        """Отправить случайный эдит из канала-источника."""
        status = await utils.answer(message, self.strings("pick"))

        try:
            ok, error_text = await self._send_random_post(
                message.peer_id,
                reply_to=getattr(message, "reply_to_msg_id", None),
            )
            if not ok:
                await utils.answer(status, error_text)
                return

            await utils.answer(status, self.strings("done"))
        except (ChannelPrivateError, ChannelInvalidError, ValueError):
            await utils.answer(status, self.strings("bad_channel"))
        except FloodWaitError as e:
            await utils.answer(status, self.strings("flood").format(seconds=e.seconds))
        except RPCError as e:
            error_text = str(e)
            lowered = error_text.lower()
            if "protected" in lowered or "forbidden" in lowered or "copy" in lowered:
                await utils.answer(status, self.strings("protected"))
                return
            await utils.answer(status, self.strings("rpc_error").format(error=utils.escape_html(error_text)))
        except Exception as e:
            await utils.answer(status, self.strings("unknown_error").format(error=utils.escape_html(str(e))))

    @loader.command(
        ru_doc="Показать текущие настройки RandomEdits",
        en_doc="Show current RandomEdits settings",
    )
    async def reditcfgcmd(self, message: Message):
        """Показать текущие настройки модуля."""
        await utils.answer(
            message,
            self.strings("settings").format(
                channel=self._normalize_channel(self.config["channel"]),
                limit=self.config["sample_limit"],
            ),
        )
