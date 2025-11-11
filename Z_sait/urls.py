"""
URL configuration for Z_sait project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from NASHE_PRILOZHENIE import views
urlpatterns = [



    # API эндпоинты
    path('api/upload/', views.TakePictureFile, name='upload'),
    path('api/coordinates/', views.GetCoordinates, name='coordinates'),
    path('api/crop/', views.CutPicture, name='crop'),
    path('api/apply-sticker/', views.apply_sticker, name='apply_sticker'),
    path('api/download/', views.ServePicture, name='download'),

    # HTML страницы (для старой логики)
    path('show-image/', views.ShowImageInformation, name='show_image'),
]

