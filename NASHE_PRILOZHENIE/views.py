import io
import os
import tempfile
import logging
from typing import Dict, Any, Tuple, Optional

import requests
from PIL import Image
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from NASHE_PRILOZHENIE.bot import get_sticker_bot

# Настройка логирования
logger = logging.getLogger(__name__)

# Константы
ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class ImageProcessor:
    """Класс для обработки изображений"""

    @staticmethod
    def is_valid_image(filename: str) -> bool:
        """Проверяет, является ли файл изображением"""
        file_ext = os.path.splitext(filename)[1].lower()
        return file_ext in ALLOWED_EXTENSIONS

    @staticmethod
    def convert_to_png(file_path: str) -> str:
        """Конвертирует изображение в PNG формат"""
        try:
            png_path = file_path.rsplit(".", 1)[0] + ".png"

            with Image.open(file_path) as image:
                if image.mode != "RGB":
                    image = image.convert("RGB")
                image.save(png_path, format="PNG", optimize=True)

            return png_path
        except Exception as e:
            logger.error(f"Ошибка конвертации в PNG: {e}")
            raise

    @staticmethod
    def crop_image(image_path: str, center_x: int, center_y: int, size: int = 512) -> str:
        """Обрезает изображение вокруг указанных координат"""
        try:
            with Image.open(image_path) as img:
                # Расчет области обрезки
                left = max(0, center_x - size // 2)
                top = max(0, center_y - size // 2)
                right = min(img.width, center_x + size // 2)
                bottom = min(img.height, center_y + size // 2)

                # Обрезаем изображение
                img_cropped = img.crop((left, top, right, bottom))

                # Сохраняем результат
                cropped_path = image_path.replace('.png', '_cropped.png')
                img_cropped.save(cropped_path, format="PNG", optimize=True)

                return cropped_path
        except Exception as e:
            logger.error(f"Ошибка обрезки изображения: {e}")
            raise


class SessionManager:
    """Класс для управления сессией"""

    @staticmethod
    def get_session_file_path(request, key: str) -> Optional[str]:
        """Безопасно получает путь к файлу из сессии"""
        file_path = request.session.get(key)
        if file_path and os.path.exists(file_path):
            return file_path
        return None

    @staticmethod
    def cleanup_session_files(request):
        """Очищает временные файлы сессии"""
        try:
            file_keys = ['file_path', 'png_image_path', 'processed_image_path']
            for key in file_keys:
                file_path = request.session.get(key)
                if file_path and os.path.exists(file_path):
                    os.unlink(file_path)
                if key in request.session:
                    del request.session[key]
        except Exception as e:
            logger.error(f"Ошибка очистки файлов сессии: {e}")


@require_http_methods(["GET"])
def home_page(request):
    """Главная страница API"""
    return JsonResponse({
        "message": "Welcome to the StickerBot API!",
        "endpoints": {
            "upload": "/upload/ (POST) - Загрузка изображения",
            "image_info": "/image-info/ (GET) - Информация об изображении",
            "set_coordinates": "/coordinates/ (POST) - Установка координат",
            "crop_image": "/crop/ (POST) - Обрезка изображения",
            "apply_sticker": "/apply-sticker/ (POST) - Добавление стикера"
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
def upload_image(request):
    """Загрузка изображения"""
    try:
        # Проверка файла
        if 'file' not in request.FILES:
            return JsonResponse({
                "success": False,
                "message": "No file uploaded"
            }, status=400)

        file = request.FILES['file']

        # Проверка размера файла
        if file.size > MAX_FILE_SIZE:
            return JsonResponse({
                "success": False,
                "message": f"File too large. Maximum size: {MAX_FILE_SIZE // 1024 // 1024}MB"
            }, status=400)

        # Проверка типа файла
        if not ImageProcessor.is_valid_image(file.name):
            return JsonResponse({
                "success": False,
                "message": f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            }, status=400)

        # Очищаем предыдущие файлы сессии
        SessionManager.cleanup_session_files(request)

        # Сохраняем файл во временную директорию
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)
            file_path = temp_file.name

        # Сохраняем путь в сессии
        request.session['file_path'] = file_path

        logger.info(f"Файл загружен: {file_path}")

        return JsonResponse({
            "success": True,
            "message": "File uploaded successfully",
            "file_size": file.size,
            "filename": file.name
        })

    except Exception as e:
        logger.error(f"Ошибка загрузки файла: {e}")
        return JsonResponse({
            "success": False,
            "message": f"Upload error: {str(e)}"
        }, status=500)


@require_http_methods(["GET"])
def get_image_info(request):
    """Получение информации об изображении"""
    try:
        file_path = SessionManager.get_session_file_path(request, 'file_path')
        if not file_path:
            return JsonResponse({
                "success": False,
                "message": "No image file found. Please upload an image first."
            }, status=400)

        # Конвертируем в PNG если нужно
        png_path = ImageProcessor.convert_to_png(file_path)
        request.session['png_image_path'] = png_path

        # Получаем информацию об изображении
        with Image.open(png_path) as image:
            image_info = {
                "width": image.width,
                "height": image.height,
                "format": image.format,
                "mode": image.mode,
                "size": os.path.getsize(png_path)
            }

        return JsonResponse({
            "success": True,
            "image_info": image_info
        })

    except Exception as e:
        logger.error(f"Ошибка получения информации об изображении: {e}")
        return JsonResponse({
            "success": False,
            "message": f"Error getting image info: {str(e)}"
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def set_coordinates(request):
    """Установка координат для обрезки"""
    try:
        x_coord = request.POST.get("x")
        y_coord = request.POST.get("y")

        if not x_coord or not y_coord:
            return JsonResponse({
                "success": False,
                "message": "Both X and Y coordinates are required"
            }, status=400)

        try:
            x = int(x_coord)
            y = int(y_coord)
        except ValueError:
            return JsonResponse({
                "success": False,
                "message": "Coordinates must be integers"
            }, status=400)

        # Проверяем что изображение загружено
        png_path = SessionManager.get_session_file_path(request, 'png_image_path')
        if not png_path:
            return JsonResponse({
                "success": False,
                "message": "No image found. Please upload an image first."
            }, status=400)

        # Проверяем что координаты в пределах изображения
        with Image.open(png_path) as img:
            if x < 0 or x > img.width or y < 0 or y > img.height:
                return JsonResponse({
                    "success": False,
                    "message": f"Coordinates out of bounds. Image size: {img.width}x{img.height}"
                }, status=400)

        request.session['coordinates'] = [x, y]

        return JsonResponse({
            "success": True,
            "coordinates": {"x": x, "y": y},
            "message": "Coordinates set successfully"
        })

    except Exception as e:
        logger.error(f"Ошибка установки координат: {e}")
        return JsonResponse({
            "success": False,
            "message": f"Error setting coordinates: {str(e)}"
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def crop_image(request):
    """Обрезка изображения по координатам"""
    try:
        png_path = SessionManager.get_session_file_path(request, 'png_image_path')
        coordinates = request.session.get('coordinates')

        if not png_path or not coordinates:
            return JsonResponse({
                "success": False,
                "message": "No image or coordinates found. Please upload image and set coordinates first."
            }, status=400)

        # Обрезаем изображение
        cropped_path = ImageProcessor.crop_image(png_path, coordinates[0], coordinates[1])
        request.session['processed_image_path'] = cropped_path

        # Возвращаем информацию об обрезанном изображении
        with Image.open(cropped_path) as img:
            crop_info = {
                "width": img.width,
                "height": img.height,
                "size": os.path.getsize(cropped_path)
            }

        return JsonResponse({
            "success": True,
            "message": "Image cropped successfully",
            "crop_info": crop_info
        })

    except Exception as e:
        logger.error(f"Ошибка обрезки изображения: {e}")
        return JsonResponse({
            "success": False,
            "message": f"Error cropping image: {str(e)}"
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def apply_sticker(request):
    """Добавление стикера в пак"""
    try:
        approved = request.POST.get("approved")
        emojis = request.POST.get("emojis", "🖼️")

        if approved != "true":
            return JsonResponse({
                "success": False,
                "message": "Sticker addition rejected by user"
            }, status=400)

        # Получаем обработанное изображение
        processed_path = SessionManager.get_session_file_path(request, 'processed_image_path')
        if not processed_path:
            return JsonResponse({
                "success": False,
                "message": "No processed image found. Please complete image processing first."
            }, status=400)

        # Читаем изображение и добавляем стикер
        with open(processed_path, 'rb') as f:
            image_bytes = f.read()

        # Используем StickerBot для добавления стикера
        sticker_bot = get_sticker_bot()
        success, message = sticker_bot.add_sticker(image_bytes, emojis)

        # Очищаем сессию после успешного добавления
        if success:
            SessionManager.cleanup_session_files(request)

        return JsonResponse({
            "success": success,
            "message": message
        })

    except Exception as e:
        logger.error(f"Ошибка добавления стикера: {e}")
        return JsonResponse({
            "success": False,
            "message": f"Error applying sticker: {str(e)}"
        }, status=500)


@require_http_methods(["GET"])
def cleanup(request):
    """Очистка временных файлов"""
    try:
        SessionManager.cleanup_session_files(request)
        return JsonResponse({
            "success": True,
            "message": "Session cleaned up successfully"
        })
    except Exception as e:
        logger.error(f"Ошибка очистки: {e}")
        return JsonResponse({
            "success": False,
            "message": f"Cleanup error: {str(e)}"
        }, status=500)