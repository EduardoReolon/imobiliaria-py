from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from PIL import Image as PILImage
from .models import Property, Subcategory, Category, Image
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .forms import PropertyForm
from django.http import JsonResponse
import json
from django.contrib import messages
from django.core.paginator import Paginator

def whatsapp_thumbnail(request, property_id):
    prop = get_object_or_404(Property, id=property_id)
    # Como definimos ordering = ['view_order'] no model, o .first() sempre pega a foto principal correta
    primeira_imagem = prop.images.first()

    if not primeira_imagem or not primeira_imagem.image:
        raise Http404("Imóvel sem imagens")

    try:
        # Abre o WebP original
        img = PILImage.open(primeira_imagem.image.path)
        
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        # Retorna o JPG gerado direto na memória para o navegador/WhatsApp
        response = HttpResponse(content_type="image/jpeg")
        img.save(response, "JPEG", quality=85)
        return response
        
    except Exception:
        raise Http404("Erro ao processar a imagem para o WhatsApp")

def home(request):
    base_query = Property.objects.filter(highlight=True)
    if not request.user.is_authenticated:
        base_query = base_query.filter(is_visible=True)
        
    imoveis = base_query.order_by('-id')[:6]
    
    cidades = Property.objects.values_list('town', flat=True).distinct().order_by('town')
    
    # Busca apenas os NOMES únicos das subcategorias para não duplicar no dropdown
    tipos = Subcategory.objects.filter(is_visible=True).values('name', 'category_id').order_by('name')
    
    # Busca as categorias (Venda / Locação)
    categorias = Category.objects.filter(is_visible=True).order_by('name')
    
    ultimo_imovel = Property.objects.order_by('-id').first() if request.user.is_authenticated else None
        
    return render(request, 'index.html', {
        'imoveis': imoveis,
        'cidades': cidades,
        'tipos': tipos,
        'categorias': categorias,
        'ultimo_imovel': ultimo_imovel
    })

def lista_imoveis(request):
    tipo_nome = request.GET.get('tipo')
    cidade = request.GET.get('cidade')
    categoria_id = request.GET.get('categoria', '2')
    ordem = request.GET.get('ordem', 'recentes') # <- Pega a ordem, padrão é recentes

    if request.user.is_authenticated:
        imoveis = Property.objects.all()
    else:
        imoveis = Property.objects.filter(is_visible=True)

    # Aplica os filtros
    if categoria_id:
        imoveis = imoveis.filter(subcategory__category_id=categoria_id)
    if tipo_nome:
        imoveis = imoveis.filter(subcategory__name=tipo_nome)
    if cidade:
        imoveis = imoveis.filter(town=cidade)

    # Aplica a Ordenação
    if ordem == 'menor_preco':
        imoveis = imoveis.order_by('price', '-id')
    elif ordem == 'maior_preco':
        imoveis = imoveis.order_by('-price', '-id')
    else:
        imoveis = imoveis.order_by('-id')
        
    paginator = Paginator(imoveis, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    cidades = Property.objects.values_list('town', flat=True).distinct().order_by('town')
    tipos = Subcategory.objects.filter(is_visible=True).values('name', 'category_id').order_by('name')
    categorias = Category.objects.filter(is_visible=True).order_by('name')

    return render(request, 'lista_imoveis.html', {
        'imoveis': page_obj,
        'cidades': cidades,
        'tipos': tipos,
        'categorias': categorias,
        'ordem_atual': ordem,
    })

def imovel_detail(request, id):
    property_obj = get_object_or_404(Property, id=id)

    # Se não está logado e o imóvel está oculto, redireciona com aviso
    if not request.user.is_authenticated and not property_obj.is_visible:
        messages.warning(request, 'Este imóvel não está mais disponível ou foi alugado/vendido.')
        return redirect('lista_imoveis')

    # Mantive a sua lógica original das URLs de imagem
    image_urls = [img.image.url for img in property_obj.images.all()]
        
    return render(request, 'imovel_detail.html', {
        'property': property_obj,
        'image_urls': image_urls
    })

@login_required
def imovel_form(request, id=None):
    if id:
        property_obj = get_object_or_404(Property, id=id)
    else:
        property_obj = None

    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES, instance=property_obj)
        if form.is_valid():
            salvo = form.save()
            return redirect('imovel_edit', id=salvo.id)
    else:
        form = PropertyForm(instance=property_obj)

    return render(request, 'imovel_form.html', {'form': form, 'property': property_obj})

@login_required
def imovel_fotos(request, id):
    imovel = get_object_or_404(Property, id=id)

    if request.method == 'POST':
        files = request.FILES.getlist('images')
        if not files:
            return JsonResponse({'erro': 'Nenhuma imagem recebida.'}, status=400)

        # Descobre qual é a última ordem para as novas fotos irem para o final
        ultima_foto = imovel.images.order_by('-view_order').first()
        proxima_ordem = (ultima_foto.view_order + 1) if ultima_foto else 1

        for f in files:
            imovel.images.create(image=f, view_order=proxima_ordem)
            proxima_ordem += 1

        return JsonResponse({'mensagem': 'Fotos enviadas com sucesso!'})

    return render(request, 'imovel_fotos.html', {'property': imovel})


@login_required
def excluir_foto(request, img_id):
    if request.method == 'POST' and request.user.is_authenticated:
        foto = get_object_or_404(Image, id=img_id)
        foto.delete()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'erro': 'Erro'}, status=400)

@login_required
def ordenar_fotos(request, id):
    if request.method == 'POST' and request.user.is_authenticated:
        data = json.loads(request.body)
        ordem = data.get('ordem', [])
        
        for index, img_id in enumerate(ordem):
            # Atualiza a view_order no banco (começando do 1)
            Image.objects.filter(id=img_id, property_id=id).update(view_order=index + 1)
            
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'erro': 'Erro'}, status=400)