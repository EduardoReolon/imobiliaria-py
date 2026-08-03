from django.core.management.base import BaseCommand
from core.models import Property

class Command(BaseCommand):
    help = 'Padroniza e limpa os nomes das cidades no banco de dados'

    def handle(self, *args, **options):
        # Dicionário para forçar correções específicas de acentuação ou lixo
        correcoes_manuais = {
            "Araucaria": "Araucária",
            "Mandirituba Pr": "Mandirituba",
            "Pien": "Piên",
            "Tijucas Do Sul": "Tijucas do Sul",
            "Sao Jose Dos Pinhais": "São José dos Pinhais"
        }

        imoveis = Property.objects.all()
        alterados = 0

        self.stdout.write("Iniciando verificação das cidades...")

        for imovel in imoveis:
            if imovel.town:
                # Remove espaços extras e converte para Title Case (ex: " MANDIRITUBA" -> "Mandirituba")
                cidade_limpa = imovel.town.strip().title()
                
                # Aplica as correções específicas do dicionário, se houver match
                cidade_limpa = correcoes_manuais.get(cidade_limpa, cidade_limpa)
                
                # Atualiza no banco apenas se houve alteração real
                if imovel.town != cidade_limpa:
                    self.stdout.write(self.style.WARNING(f"Corrigindo: '{imovel.town}' -> '{cidade_limpa}'"))
                    imovel.town = cidade_limpa
                    # update_fields garante que apenas a coluna town seja afetada no SQL, otimizando o processo
                    imovel.save(update_fields=['town'])
                    alterados += 1

        self.stdout.write(self.style.SUCCESS(f"Limpeza concluída com sucesso! {alterados} imóveis atualizados."))