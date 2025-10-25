import os
import requests
from telegram import Bot
from typing import Tuple, Optional
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StickerBot:
    def __init__(self, token: str, owner_user_id: int, sticker_set_name: str):
        self.bot = Bot(token=token)
        self.owner_user_id = owner_user_id
        self.sticker_set_name = sticker_set_name
        self.base_url = f"https://api.telegram.org/bot{token}"

    def _create_sticker_set(self) -> bool:
        """Создаёт стикерпак, если он ещё не существует."""
        try:
            # Проверяем существование стикерпака
            response = requests.get(
                f"{self.base_url}/getStickerSet",
                params={'name': self.sticker_set_name},
                timeout=10
            )
            result = response.json()

            if result.get('ok') and 'stickers' in result.get('result', {}):
                logger.info(f"Стикерпак '{self.sticker_set_name}' уже существует.")
                return True
            else:
                return self._create_new_sticker_set()

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при создании стикерпака: {e}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при создании стикерпака: {e}")
            return False

    def _create_new_sticker_set(self) -> bool:
        """Создаёт новый стикерпак."""
        try:
            logger.warning("⚠️  Для первого запуска создайте стикерпак вручную через @BotFather")
            logger.warning("⚠️  Команды:")
            logger.warning("⚠️  1. /newpack")
            logger.warning(f"⚠️  2. Название пака: {self.sticker_set_name}")
            logger.warning("⚠️  3. Отправьте любую картинку как первый стикер")

            # Проверяем еще раз - может пак уже создан
            response = requests.get(
                f"{self.base_url}/getStickerSet",
                params={'name': self.sticker_set_name},
                timeout=10
            )
            result = response.json()

            if result.get('ok'):
                logger.info(f"✅ Стикерпак теперь существует!")
                return True
            else:
                logger.error("❌ Стикерпак не создан. Создайте его через @BotFather")
                return False

        except Exception as e:
            logger.error(f"Ошибка при создании стикерпака: {e}")
            return False

    def add_sticker(self, image_bytes: bytes, emojis: str = '😊') -> Tuple[bool, str]:
        """Добавляет стикер в стикерпак."""
        try:
            # Убедимся, что стикерпак существует
            if not self._create_sticker_set():
                return False, "❌ Не удалось найти стикерпак. Создайте его через @BotFather"

            files = {
                'png_sticker': ('sticker.png', image_bytes, 'image/png')
            }
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
                logger.info("Стикер успешно добавлен в пак")
                return True, "✅ Стикер добавлен в пак!"
            else:
                error_msg = result.get('description', 'Unknown Telegram error')
                logger.error(f"Ошибка Telegram при добавлении стикера: {error_msg}")

                # Полезные подсказки для частых ошибок
                if "STICKERSET_INVALID" in error_msg:
                    return False, f"❌ Стикерпак не найден. Создайте через @BotFather: /newpack {self.sticker_set_name}"
                elif "STICKER_PNG_DIMENSIONS" in error_msg:
                    return False, "❌ Неверные размеры стикера. Нужно 512x512 пикселей"
                elif "STICKER_PNG_NOPNG" in error_msg:
                    return False, "❌ Файл не в формате PNG"
                else:
                    return False, f"❌ Ошибка Telegram: {error_msg}"

        except requests.exceptions.Timeout:
            error_msg = "Таймаут при добавлении стикера"
            logger.error(error_msg)
            return False, f"❌ {error_msg}"
        except Exception as e:
            error_msg = f"Ошибка при добавлении стикера: {str(e)}"
            logger.error(error_msg)
            return False, f"❌ {error_msg}"

    def get_sticker_set_info(self) -> Optional[dict]:
        """Получает информацию о стикерпаке."""
        try:
            response = requests.get(
                f"{self.base_url}/getStickerSet",
                params={'name': self.sticker_set_name},
                timeout=10
            )
            result = response.json()

            if result.get('ok'):
                return result['result']
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении информации о стикерпаке: {e}")
            return None

    def get_sticker_set_url(self) -> str:
        """Возвращает ссылку на стикерпак."""
        return f"https://t.me/addstickers/{self.sticker_set_name}"


def get_sticker_bot() -> StickerBot:
    """Фабрика для создания экземпляра StickerBot."""
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7348822640:AAE1mnAUdFVVb62DPC5hY_ZedTJ4MT0mPoo')
    OWNER_USER_ID = int(os.getenv('TELEGRAM_OWNER_ID', '5219975213'))
    STICKER_SET_NAME = os.getenv('STICKER_SET_NAME', 'GOIDAZVONCHIK_336')

    logger.info(f"Создаем StickerBot с набором: {STICKER_SET_NAME}")
    return StickerBot(BOT_TOKEN, OWNER_USER_ID, STICKER_SET_NAME)


# Глобальный экземпляр для удобства
sticker_bot = get_sticker_bot()