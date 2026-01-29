from decimal import Decimal
from django.conf import settings
from .models import Product, ProductVariant

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart

    def add(self, product, quantity=1, variant=None):
        product_id = str(product.id)
        variant_id = str(variant.id) if variant else 'no_variant'
        cart_key = f"{product_id}_{variant_id}"

        if cart_key not in self.cart:
            price = float(product.price)
            if variant:
                price += float(variant.price_extra)
                
            self.cart[cart_key] = {
                'quantity': 0,
                'price': price,
                'product_id': product_id,
                'variant_id': variant.id if variant else None,
                'name': product.name,
                'variant_name': variant.name if variant else '',
                'image': product.image.url if product.image else ''
            }
        
        self.cart[cart_key]['quantity'] += quantity
        self.save()

    def remove(self, cart_key):
        if cart_key in self.cart:
            del self.cart[cart_key]
            self.save()

    def save(self):
        self.session.modified = True

    def __iter__(self):
        for key, item in self.cart.items():
            item['total_price'] = Decimal(item['price']) * item['quantity']
            item['key'] = key
            yield item

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def clear(self):
        del self.session['cart']
        self.save()