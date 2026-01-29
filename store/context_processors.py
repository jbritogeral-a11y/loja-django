from .models import SiteSettings
from .cart import Cart

def store_context(request):
    return {
        'site_settings': SiteSettings.objects.first(),
        'cart': Cart(request)
    }