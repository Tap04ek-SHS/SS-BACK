import io
import asyncio
from telegram import Bot
from telegram.error import TelegramError
import requests
from PIL import Image
class StickerBot:
    def __init__(self, token, owner_user_id, sticker_set_name):
        self.bot = Bot(token=token)
        self.owner_user_id = owner_user_id
        self.sticker_set_name = sticker_set_name

    def _add_sticker(self, image_bytes, emojis):
        print('Adding sticker')
        image = Image.open(io.BytesIO(image_bytes))
        print(f"✅ Формат: {image.format}")
        print(f"📏 Размер: {image.size}")
        print(f"🎨 Режим: {image.mode}")
        print(f"📦 Размер файла: {len(image_bytes)} байт ({len(image_bytes) / 1024:.1f} КБ)")
        try:
            url = f"https://api.telegram.org/bot{self.bot.token}/addStickerToSet"
            files = {
                'png_sticker': ('sticker.png', image_bytes, 'image/png')
            }
            data = {
                'user_id': self.owner_user_id,
                'name': self.sticker_set_name,
                'emojis': emojis
            }
            response = requests.post(url, files=files, data=data)
            result = response.json()

            print(f"Telegram response: {result}")

            if result['ok']:
                print("Goida")
                return True, "✅ Стикер добавлен в пак!"
            else:
                error_msg = result.get('description', 'Unknown Telegram error')
                print(f"Telegram error: {error_msg}")
                return False, f"❌ Ошибка Telegram: {error_msg}"

        except Exception as e:
            print(f"Exception: {str(e)}")
            return False, f"❌ Ошибка: {str(e)}"

BOT_TOKEN = "7348822640:AAE1mnAUdFVVb62DPC5hY_ZedTJ4MT0mPoo"
OWNER_USER_ID = 5219975213
STICKER_SET_NAME = "NASH_SLON_339"

sticker_bot = StickerBot(BOT_TOKEN, OWNER_USER_ID, STICKER_SET_NAME)