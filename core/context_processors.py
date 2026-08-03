import datetime

def info_global(request):
    ano_fundacao = 1988
    ano_atual = datetime.date.today().year
    return {
        'anos_mercado': ano_atual - ano_fundacao,
        'mostrar_banner_oferta': True,
        'whatsapp_numero': '5541000000000',
    }