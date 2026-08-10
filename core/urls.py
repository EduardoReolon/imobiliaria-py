"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from core import views
from django.contrib.auth import views as auth_views
from django.views.decorators.cache import cache_page

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    path('', cache_page(900)(views.home), name='home'),
    path('imoveis/<int:property_id>/whatsapp-thumb.jpg', views.whatsapp_thumbnail, name='whatsapp_thumb'),
    path('imoveis/', views.lista_imoveis, name='lista_imoveis'),
    path('imovel/<int:id>/', views.imovel_detail, name='imovel_detail'),
    path('imovel/novo/', views.imovel_form, name='imovel_create'),
    path('imovel/<int:id>/editar/', views.imovel_form, name='imovel_edit'),
    path('imovel/<int:id>/fotos/', views.imovel_fotos, name='imovel_fotos'),
    path('foto/<int:img_id>/excluir/', views.excluir_foto, name='excluir_foto'),
    path('imovel/<int:id>/ordenar-fotos/', views.ordenar_fotos, name='ordenar_fotos'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
