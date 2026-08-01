from django.db import models

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
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    # Usando ImageField como combinado. O upload_to define a pasta dentro do MEDIA_ROOT
    image = models.ImageField(upload_to='properties/images/', max_length=255, null=True, blank=True)
    view_order = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = 'Image'
        verbose_name_plural = 'Images'
        ordering = ['view_order']

    def __str__(self):
        return f"Image for Property {self.property_id}"