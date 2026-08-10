from django.db import models
import uuid
import os
from io import BytesIO
from PIL import Image as PILImage
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import builtins

def get_image_filename(instance, filename):
    # Gera o nome no formato: {id_propriedade}_{hash_aleatorio}.webp
    short_hash = uuid.uuid4().hex[:8]
    return f"properties/images/{instance.property_id}_{short_hash}.webp"

class Category(models.Model):
    name = models.CharField(max_length=255)
    is_visible = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Subcategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=255)
    is_visible = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Subcategory'
        verbose_name_plural = 'Subcategories'

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class Property(models.Model):
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE, related_name='properties')
    is_visible = models.BooleanField(default=False)
    
    # Endereço
    address = models.CharField(max_length=80, null=True, blank=True)
    number = models.CharField(max_length=8, null=True, blank=True)
    complement = models.CharField(max_length=60, null=True, blank=True)
    neighborhood = models.CharField(max_length=60, null=True, blank=True)
    town = models.CharField(max_length=60, null=True, blank=True)
    state = models.CharField(max_length=2, null=True, blank=True)
    
    # Detalhes
    brief_description = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    bedrooms = models.IntegerField(default=0)
    bathrooms = models.IntegerField(default=0)
    garage = models.IntegerField(default=0)
    area_facility = models.IntegerField(default=0) # Área construída/útil
    area_land = models.IntegerField(default=0)     # Área do terreno
    highlight = models.BooleanField(default=False)
    
    # Dados de registro/lote
    square = models.CharField(max_length=15, null=True, blank=True) # Quadra
    lot = models.CharField(max_length=15, null=True, blank=True)    # Lote
    registration = models.CharField(max_length=40, null=True, blank=True) # Matrícula
    
    # Proprietário
    owner_name = models.CharField(max_length=80, null=True, blank=True)
    owner_id = models.CharField(max_length=20, null=True, blank=True) # RG
    owner_cpf = models.CharField(max_length=14, null=True, blank=True)
    owner_fone1 = models.CharField(max_length=20, null=True, blank=True)
    owner_fone2 = models.CharField(max_length=20, null=True, blank=True)
    owner_fone3 = models.CharField(max_length=20, null=True, blank=True)
    owner_fone4 = models.CharField(max_length=20, null=True, blank=True)
    
    # Outros
    parley = models.TextField(null=True, blank=True) # Negociação/Anotações
    youtube = models.CharField(max_length=20, null=True, blank=True) # ID do vídeo
    sold = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Property'
        verbose_name_plural = 'Properties'

    def __str__(self):
        return f"{self.id} - {self.address or 'Sem endereço'}"


class Image(models.Model):
    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=get_image_filename, max_length=255, null=True, blank=True)
    view_order = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = 'Image'
        verbose_name_plural = 'Images'
        ordering = ['view_order']

    def save(self, *args, **kwargs):
        # Se existe imagem e ela ainda não é um WebP, fazemos a conversão
        if self.image and not self.image.name.lower().endswith('.webp'):
            img = PILImage.open(self.image)
            
            # Converte para RGB caso seja PNG com fundo transparente ou RGBA
            if img.mode != 'RGB':
                img = img.convert('RGB')
                
            output = BytesIO()
            img.save(output, format='WEBP', quality=85)
            output.seek(0)
            
            # Substitui a imagem enviada pela versão WebP processada
            # O nome temporário não importa, a função get_image_filename dará o nome final
            self.image = ContentFile(output.read(), name='temp.webp')

        super().save(*args, **kwargs)
    
    @builtins.property
    def thumb_url(self):
        """
        Retorna a URL da imagem otimizada (-thumb.webp).
        Se ela não existir fisicamente no disco, cria na hora.
        """
        if not self.image:
            return ""

        original_path = self.image.name  # Ex: imoveis/foto1.jpg
        
        # 1. Ignoramos a extensão original e forçamos a string ".webp" no final
        base_name, _ = os.path.splitext(original_path)
        thumb_path = f"{base_name}-thumb.webp"  # Ex: imoveis/foto1-thumb.webp

        if not default_storage.exists(thumb_path):
            try:
                with default_storage.open(original_path, 'rb') as f:
                    img = PILImage.open(f)
                    
                    if img.width > 600:
                        output_size = (600, int((600 / img.width) * img.height))
                        img = img.resize(output_size, PILImage.Resampling.LANCZOS)
                    
                    output = BytesIO()
                    img.save(output, format='WEBP', quality=75) 
                    output.seek(0)
                    
                    default_storage.save(thumb_path, ContentFile(output.read()))
            except Exception as e:
                # 2. Print para descobrirmos o motivo de falhar silenciosamente no servidor
                print(f"ERRO AO GERAR THUMB: {e}")
                return self.image.url

        return default_storage.url(thumb_path)

    def __str__(self):
        return f"Image for Property {self.property_id}"