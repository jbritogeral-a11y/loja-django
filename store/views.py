from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category, ProductVariant, Order, OrderItem
from .cart import Cart
from .forms import OrderCreateForm, UserUpdateForm, UserRegisterForm
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.db.models import Q


def product_list(request, category_slug=None):
    category = None
    products = Product.objects.filter(is_active=True)
    
    # Filtro por Categoria
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    # Pesquisa (Search)
    query = request.GET.get('q')
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))

    # Produtos em Destaque (apenas na Homepage sem filtros)
    featured_products = []
    if not category_slug and not query:
        featured_products = Product.objects.filter(is_active=True, is_featured=True)[:4]

    return render(request, 'store/product_list.html', {
        'products': products, 
        'category': category,
        'featured_products': featured_products,
        'query': query
    })

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return render(request, 'store/product_detail.html', {'product': product})

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
    # Se for Administrador (Staff), ignora a sessão e redireciona para login de cliente
    if request.user.is_staff:
        return redirect('store:login')

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        if user_form.is_valid():
            user_form.save()
            return redirect('store:profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
    
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/profile.html', {'orders': orders, 'user_form': user_form})

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # Faz login automático após registo
            return redirect('store:product_list')
    else:
        form = UserRegisterForm()
    return render(request, 'store/register.html', {'form': form})

def checkout(request):
    cart = Cart(request)
    if not cart:
        return redirect('store:product_list')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            # Associar encomenda ao cliente logado
            # Apenas associa se NÃO for administrador (staff)
            if request.user.is_authenticated and not request.user.is_staff:
                order.user = request.user
            order.total_price = cart.get_total_price()
            order.save()
            
            for item in cart:
                # 1. Obter Produto (usando ID direto do carrinho - muito mais seguro)
                product_id = item.get('product_id')
                product = get_object_or_404(Product, id=product_id)
                
                # --- GESTÃO DE STOCK ---
                if product.stock >= item['quantity']:
                    product.stock -= item['quantity']
                    product.save()
                
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
        initial_data = {}
        # Apenas preenche dados se NÃO for administrador
        if request.user.is_authenticated and not request.user.is_staff:
            initial_data['full_name'] = f"{request.user.first_name} {request.user.last_name}".strip()
            initial_data['email'] = request.user.email
            
            # Tenta preencher morada com base na última encomenda
            last_order = Order.objects.filter(user=request.user).order_by('-created_at').first()
            if last_order:
                initial_data['address'] = last_order.address
                initial_data['city'] = last_order.city
        
        form = OrderCreateForm(initial=initial_data)

    return render(request, 'store/checkout.html', {'form': form})
