import os
import requests
from typing import Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StickerBot:
    def __init__(self, token: str, owner_user_id: int, sticker_set_name: str):
        self.token = token
        self.owner_user_id = owner_user_id
        self.sticker_set_name = sticker_set_name
        self.base_url = f"https://api.telegram.org/bot{token}"

    def add_sticker(self, image_bytes: bytes, emojis: str = '🖼️') -> Tuple[bool, str]:
        """Добавляет стикер в стикерпак (с автоматическим созданием пака)"""
        try:
            # Сначала пробуем добавить в существующий пак
            files = {'png_sticker': ('sticker.png', image_bytes, 'image/png')}
            data = {
                'user_id': self.owner_user_id,
                'name': self.sticker_set_name,
                'emojis': emojis
            }

            response = requests.post(
                f"{self.base_url}/addStickerToSet",
                files=files,
                data=data,
                timeout=15
            )
            result = response.json()

            if result.get('ok'):
                logger.info("✅ Стикер добавлен в существующий пак!")
                return True, "✅ Стикер добавлен в пак!"

            # Если пака нет - создаем его
            error_msg = result.get('description', '')
            if "STICKERSET_INVALID" in error_msg:
                return self._create_sticker_set_with_first_sticker(image_bytes, emojis)
            else:
                return False, f"❌ Ошибка Telegram: {error_msg}"

        except Exception as e:
            return False, f"❌ Ошибка: {str(e)}"

    def _create_sticker_set_with_first_sticker(self, image_bytes: bytes, emojis: str) -> Tuple[bool, str]:
        """Создает стикерпак с первым стикером"""
        try:
            files = {'png_sticker': ('sticker.png', image_bytes, 'image/png')}
            data = {
                'user_id': self.owner_user_id,
                'name': self.sticker_set_name,
                'title': 'My Sticker Pack',
                'emojis': emojis
            }

            response = requests.post(
                f"{self.base_url}/createNewStickerSet",
                files=files,
                data=data,
                timeout=15
            )
            result = response.json()

            if result.get('ok'):
                logger.info("✅ Стикерпак создан и стикер добавлен!")
                return True, "✅ Стикерпак создан и стикер добавлен!"
            else:
                error_msg = result.get('description', 'Unknown error')
                return False, f"❌ Ошибка создания пака: {error_msg}"

        except Exception as e:
            return False, f"❌ Ошибка создания пака: {str(e)}"

def get_sticker_bot() -> StickerBot:
    """Фабрика для создания экземпляра StickerBot"""
    BOT_TOKEN = '7348822640:AAE1mnAUdFVVb62DPC5hY_ZedTJ4MT0mPoo'
    OWNER_USER_ID = 5219975213
    STICKER_SET_NAME = 'GOIDAZVONCHEK_336_by_Goidazvonchikbot'

    return StickerBot(BOT_TOKEN, OWNER_USER_ID, STICKER_SET_NAME)