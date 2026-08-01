import datetime

def info_global(request):
    ano_fundacao = 1988
    ano_atual = datetime.date.today().year
    return {
        'anos_mercado': ano_atual - ano_fundacao
    }