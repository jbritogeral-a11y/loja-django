from .models import SiteSettings, Category
from .cart import Cart

def store_context(request):
    return {
        'site_settings': SiteSettings.objects.first(),
        'cart': Cart(request),
        'categories': Category.objects.all()
    }