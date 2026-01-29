from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category, ProductVariant
from .cart import Cart

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
