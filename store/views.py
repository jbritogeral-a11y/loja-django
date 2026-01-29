from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category, ProductVariant, Order, OrderItem
from .cart import Cart
from .forms import OrderCreateForm
from django.core.mail import send_mail
from django.conf import settings


def product_list(request):
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.all()
    return render(request, 'store/product_list.html', {'products': products, 'categories': categories})

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    categories = Category.objects.all()
    return render(request, 'store/product_detail.html', {'product': product, 'categories': categories})

def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    variant = None
    
    if request.method == 'POST':
        variant_id = request.POST.get('variant')
        if variant_id:
            variant = get_object_or_404(ProductVariant, id=variant_id)
        
        cart.add(product=product, variant=variant)
        
    return redirect('store:cart_detail')

def cart_remove(request, cart_key):
    cart = Cart(request)
    cart.remove(cart_key)
    return redirect('store:cart_detail')

def cart_detail(request):
    return render(request, 'store/cart_detail.html')

def checkout(request):
    cart = Cart(request)
    if not cart:
        return redirect('store:product_list')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.total_price = cart.get_total_price()
            order.save()
            
            for item in cart:
                # Correção para KeyError: 'product'
                # Se o item não tiver o objeto produto, vamos buscá-lo à BD usando a key (ID)
                product = item.get('product')
                if not product:
                    # Tenta extrair o ID do produto da 'key' (ex: "1", "1-2" ou "1_no_variant")
                    raw_key = str(item.get('key', ''))
                    product_id = raw_key.replace('_', '-').split('-')[0]
                    
                    if product_id and product_id.isdigit():
                        product = Product.objects.get(id=product_id)
                
                # Tratamento da variante (se for apenas um ID, buscar o objeto)
                variant = item.get('variant')
                if variant and not isinstance(variant, ProductVariant):
                    if str(variant).isdigit():
                        try:
                            variant = ProductVariant.objects.get(id=variant)
                        except ProductVariant.DoesNotExist:
                            variant = None
                    else:
                        variant = None

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=item['price'],
                    quantity=item['quantity'],
                    variant=variant
                )
            
            cart.clear()
            
            # Enviar emails de confirmação
            subject = f'Confirmação da Encomenda #{order.id}'
            message = f'Olá {order.full_name},\n\nObrigado pela sua encomenda! O total foi de {order.total_price}€.\n\nEnviaremos novidades sobre o envio em breve.'
            
            try:
                # Email para o cliente
                send_mail(subject, message, settings.EMAIL_HOST_USER, [order.email])
                
                # Email para o admin
                send_mail(
                    f'Nova Encomenda #{order.id}',
                    f'Recebeu uma nova encomenda de {order.full_name} no valor de {order.total_price}€.',
                    settings.EMAIL_HOST_USER,
                    ['seu_email_de_admin@exemplo.com'], # Substitua pelo seu email
                    fail_silently=True
                )
            except Exception as e:
                # Não impede o fluxo, mas regista o erro na consola do servidor
                print(f"ERRO AO ENVIAR EMAIL: {e}")

            return render(request, 'store/order_success.html', {'order': order})
    else:
        form = OrderCreateForm()

    return render(request, 'store/checkout.html', {'form': form})
