import os
import django
import random
from io import BytesIO

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from store.models import Category, Product, Client, Therapy
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile

# Tenta importar PIL para gerar imagens
try:
    from PIL import Image
    def create_dummy_image():
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        image = Image.new('RGB', (600, 600), color=color)
        thumb_io = BytesIO()
        image.save(thumb_io, format='JPEG')
        return ContentFile(thumb_io.getvalue(), name='produto_teste.jpg')
except ImportError:
    def create_dummy_image(): return None

def populate():
    print("--- A INICIAR O SCRIPT DE POPULAÇÃO ---")

    # 1. Criar 2 Produtos por Categoria
    categories = Category.objects.all()
    
    if not categories.exists():
        print("AVISO: Não existem categorias. Crie algumas no Admin primeiro.")
    else:
        print(f"Encontradas {categories.count()} categorias. A criar produtos...")
        
        for cat in categories:
            for i in range(1, 3):
                product_name = f"Produto {cat.name} {i}"
                # Verifica se já existe para não duplicar
                if not Product.objects.filter(name=product_name).exists():
                    img = create_dummy_image()
                    Product.objects.create(
                        category=cat,
                        name=product_name,
                        description=f"Descrição automática para o produto {i} da categoria {cat.name}.",
                        price=random.randint(10, 100), # Preço aleatório entre 10 e 100
                        stock=50,
                        is_active=True,
                        is_featured=False,
                        image=img
                    )
                    print(f"Criado: {product_name}")
                else:
                    print(f"Saltado (já existe): {product_name}")

    # 3. Criar Terapias
    print("\n--- A CRIAR TERAPIAS ---")
    therapies = ["Reiki", "Massagem de Relaxamento", "Animal de Poder", "Limpeza Espiritual", "Limpeza Energética"]
    for t_name in therapies:
        if not Therapy.objects.filter(name=t_name).exists():
            img = create_dummy_image()
            Therapy.objects.create(
                name=t_name,
                description="Sessão terapêutica para equilíbrio do corpo e mente.",
                price=random.randint(30, 80),
                duration_minutes=60,
                image=img
            )
            print(f"Criada Terapia: {t_name}")

    # 2. Criar 10 Clientes
    print("\n--- A CRIAR 10 CLIENTES ---")
    password_padrao = "2026,2026"
    
    for i in range(1, 11):
        username = f"cliente_{i}"
        email = f"cliente{i}@exemplo.com"
        
        if not Client.objects.filter(username=username).exists():
            Client.objects.create_user(username=username, email=email, password=password_padrao, first_name="Cliente", last_name=str(i))
            # print(f"Criado: {username}") # Comentado para não poluir a consola com 110 linhas
        
    print(f"Sucesso! 10 clientes garantidos com a password '{password_padrao}'.")
    print("--- PROCESSO CONCLUÍDO ---")

if __name__ == '__main__':
    populate()