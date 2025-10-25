from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from NASHE_PRILOZHENIE import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_page, name='home'),
    path('api/upload/', views.upload_image, name='upload_image'),
    path('api/image-info/', views.get_image_info, name='image_info'),
    path('api/coordinates/', views.set_coordinates, name='set_coordinates'),
    path('api/crop/', views.crop_image, name='crop_image'),
    path('api/apply-sticker/', views.apply_sticker, name='apply_sticker'),
    path('api/cleanup/', views.cleanup, name='cleanup'),
]

# Для обслуживания медиа-файлов в разработке
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
