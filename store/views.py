from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category, ProductVariant, Order, OrderItem
from .cart import Cart
from .forms import OrderCreateForm
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required


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

@login_required
def profile(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/profile.html', {'orders': orders})

def checkout(request):
    cart = Cart(request)
    if not cart:
        return redirect('store:product_list')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            # Associar encomenda ao cliente logado
            if request.user.is_authenticated:
                order.user = request.user
            order.total_price = cart.get_total_price()
            order.save()
            
            for item in cart:
                # 1. Obter Produto (usando ID direto do carrinho - muito mais seguro)
                product_id = item.get('product_id')
                product = get_object_or_404(Product, id=product_id)
                
                # 2. Obter Variante (opcional, apenas para referência futura)
                variant_id = item.get('variant_id')
                # Nota: O modelo OrderItem atual não tem campo para guardar a variante,
                # por isso não a passamos no create abaixo para evitar erros.

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=item['price'],
                    quantity=item['quantity'],
                    # variant=variant  <-- Comentado pois o campo não existe no modelo OrderItem
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
