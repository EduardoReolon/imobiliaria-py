import os
import pymysql
import requests
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from core.models import Category, Subcategory, Property, Image
from django.db import connection
from django.core.management.color import no_style

class Command(BaseCommand):
    help = 'Importa dados e imagens do banco MySQL antigo (Adonis)'

    def add_arguments(self, parser):
        parser.add_argument('--apenas-banco', action='store_true', help='Importa apenas textos')
        parser.add_argument('--apenas-imagens', action='store_true', help='Importa apenas imagens')

    def get_mysql_connection(self):
        return pymysql.connect(
            host=os.environ.get('DB_OLD_HOST'),
            port=int(os.environ.get('DB_OLD_PORT', 3306)),
            user=os.environ.get('DB_OLD_USER'),
            password=os.environ.get('DB_OLD_PASSWORD'),
            database=os.environ.get('DB_OLD_NAME'),
            cursorclass=pymysql.cursors.DictCursor
        )

    def handle(self, *args, **options):
        apenas_banco = options['apenas_banco']
        apenas_imagens = options['apenas_imagens']
        # Se nenhum argumento for passado, roda tudo
        rodar_tudo = not apenas_banco and not apenas_imagens

        mysql_conn = self.get_mysql_connection()
        
        try:
            with mysql_conn.cursor() as cursor:
                if rodar_tudo or apenas_banco:
                    self.importar_textos(cursor)
                
                if rodar_tudo or apenas_imagens:
                    self.importar_imagens(cursor)
                    
        finally:
            mysql_conn.close()

    def importar_textos(self, cursor):
        self.stdout.write("Importando Categorias...")
        cursor.execute("SELECT * FROM categories")
        for row in cursor.fetchall():
            Category.objects.update_or_create(
                id=row['id'], defaults={'name': row['name'], 'is_visible': row['isVisible']}
            )

        self.stdout.write("Importando Subcategorias...")
        cursor.execute("SELECT * FROM subcategories")
        for row in cursor.fetchall():
            Subcategory.objects.update_or_create(
                id=row['id'], defaults={'name': row['name'], 'category_id': row['category_id'], 'is_visible': row['isVisible']}
            )

        self.stdout.write("Importando Imóveis...")
        cursor.execute("SELECT * FROM properties")
        for row in cursor.fetchall():
            # Removemos os campos que não existem no Django model e ajustamos nomes
            defaults = {k: v for k, v in row.items() if k not in ['id', 'created_at', 'updated_at', 'isVisible']}
            defaults['is_visible'] = row['isVisible']
            
            Property.objects.update_or_create(id=row['id'], defaults=defaults)

        # Atualiza a sequência do Postgres para evitar erro de ID ao cadastrar novos imóveis manualmente depois
        sequence_sql = connection.ops.sequence_reset_sql(no_style(), [Category, Subcategory, Property])
        with connection.cursor() as pg_cursor:
            for sql in sequence_sql:
                pg_cursor.execute(sql)
                
        self.stdout.write(self.style.SUCCESS("Textos importados com sucesso!"))

    def importar_imagens(self, cursor):
        self.stdout.write("Importando Imagens...")
        old_url = os.environ.get('OLD_SITE_URL')
        erros = 0
        sucessos = 0

        cursor.execute("SELECT * FROM images")
        imagens = cursor.fetchall()

        for row in imagens:
            # Verifica se já importamos essa imagem (baseado no id original, caso precisemos parar e continuar)
            if Image.objects.filter(id=row['id']).exists():
                continue

            url_imagem = f"{old_url}/properties/{row['path']}"
            try:
                response = requests.get(url_imagem, timeout=10)
                if response.status_code == 200:
                    img_instance = Image(id=row['id'], property_id=row['property_id'], view_order=row['viewOrder'])
                    # Salvar a imagem dispara o método save() no model, que faz a conversão pra WebP
                    img_instance.image.save(f"{row['path']}.jpg", ContentFile(response.content), save=True)
                    sucessos += 1
                    self.stdout.write(f"Imagem {row['id']} OK.")
                else:
                    erros += 1
                    self.stdout.write(self.style.WARNING(f"Erro 404/Download: {url_imagem}"))
            except Exception as e:
                erros += 1
                self.stdout.write(self.style.ERROR(f"Erro ao processar imagem {row['id']}: {e}"))

        # Atualiza a sequência do Postgres para as imagens
        sequence_sql = connection.ops.sequence_reset_sql(no_style(), [Image])
        with connection.cursor() as pg_cursor:
            for sql in sequence_sql:
                pg_cursor.execute(sql)

        self.stdout.write(self.style.SUCCESS(f"Imagens finalizadas. Sucesso: {sucessos} | Erros: {erros}"))