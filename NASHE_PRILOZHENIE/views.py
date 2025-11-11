from selectors import SelectSelector
import asyncio
from django.shortcuts import render
from django.http import HttpResponse
import aspose.words as aw
import os
import tempfile
from PIL import Image
from telegram import Bot
from django.http import JsonResponse
from NASHE_PRILOZHENIE.bot import *
import json

def home_page(request):

    return render(request, 'Main.html')
def TakePictureFile(request):
    if request.method == "POST":
        file = request.FILES.get("file")
        print("SESSION ID:", request.session.session_key)
        print("SESSION DATA:", dict(request.session))
        if file is None:
            return HttpResponse("No file uploaded", status=400)
        #if not CheckPictureFile(file.name):
            return HttpResponse("File is not an image", status=400)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
            temp_file.write(file.read())
            file_path = temp_file.name
        request.session['file_path'] = file_path
        RestorePath(file_path, request)
        print("=== ПОСЛЕ RestorePath ===")
        print("file_path:", file_path)
        print("png_image_path В СЕССИИ:", request.session.get('png_image_path'))
        print("ВСЯ СЕССИЯ:", dict(request.session))
        print("=========================")
        print(file_path)
        return HttpResponse("OK", status=200)
    return HttpResponse("Use POST method", status=405)

def CheckPictureFile(filename):
    image_extensions: set[str] = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp', '.svg'}
    file_ext = os.path.splitext(filename)[1].lower()
    return file_ext in image_extensions


def ShowImageInformation(request):
    file_path = request.session['file_path']
    RestorePath(file_path, request)
    png_image_path = request.session['png_image_path']
    image = Image.open(png_image_path)
    context = {"height": image.height, "width": image.width}
    return render(request, 'VIBORKOORDINAT.html', context)
def GetCoordinates(request):
    if request.method == "POST":
        data = json.loads(request.body)
        X_cordinates = data.get("x")
        Y_cordinates = data.get("y")
        request.session['cordinates'] = [int(X_cordinates), int(Y_cordinates)]
        print(request.session['cordinates'])
    return HttpResponse("OK", status=200)

def RestorePath(file_path,request):
    png_image_path = file_path.rsplit(".", 1)[0] + ".png"
    with Image.open(file_path) as image:
        if image.mode != "RGB":
            image = image.convert("RGB")
        image.save(png_image_path,format="PNG")
    request.session['png_image_path'] = png_image_path
    return None


def ServePicture(request):
    file_path = request.session.get('file_path')
    RestorePath(file_path,request)
    png_image_path = request.session.get('png_image_path')
    with open(png_image_path, 'rb') as png_image:
      return HttpResponse(png_image.read(), content_type="image/png")

def CutPicture(request):
    print("DEBUG session keys:", list(request.session.keys()))
    print("DEBUG file_path:", request.session.get('file_path'))
    print("DEBUG png_image_path:", request.session.get('png_image_path'))
    print("DEBUG coordinates:", request.session.get('cordinates'))
    image_path = request.session.get('png_image_path')
    coordinates = request.session.get('cordinates')
    img = Image.open(image_path)
    img_cut = img.crop((coordinates[0] - 256, coordinates[1] - 256, coordinates[0] + 256, coordinates[1] + 256))
    cut_path = image_path.replace('.png', '_cut.png')
    img_cut.save(cut_path)
    with open(cut_path, 'rb') as f:
        request.session['processed_image_path'] = cut_path
        return HttpResponse(f.read(), content_type="image/png")


def add_sticker_to_pack(request, emojis):
    cut_path = request.session['processed_image_path']
    with open(cut_path, 'rb') as f:
        image_bytes = f.read()
    success, message = get_sticker_bot().add_sticker(image_bytes, emojis)
    return JsonResponse({
        'success': success,
        'message': message
    })

def apply_sticker(request):
    if request.method == "POST":
        # ЧИТАЕМ JSON ИЗ ТЕЛА ЗАПРОСА
        data = json.loads(request.body)
        approved = data.get("approved")
        emojis = data.get('emojis', '🖼️')

        if approved:
            # ВЫЗЫВАЕМ И ВОЗВРАЩАЕМ РЕЗУЛЬТАТ
            result = add_sticker_to_pack(request, emojis)
            return result  # ← вернет JsonResponse с success/message
        return JsonResponse({"success": False, "message": "Not approved"})


