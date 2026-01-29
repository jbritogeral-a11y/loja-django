from django.contrib import admin
from .models import Category, Product, ProductImage, ProductVariant, Order, OrderItem, SiteSettings, PaymentMethod, ShippingMethod, Client
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'stock', 'is_active', 'is_featured', 'category']
    list_filter = ['is_active', 'is_featured', 'category']
    list_editable = ['price', 'stock', 'is_active', 'is_featured']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductVariantInline]

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0
    can_delete = False
    readonly_fields = ['product', 'price', 'quantity']

    # Impede adicionar novos itens à encomenda
    def has_add_permission(self, request, obj=None):
        return False

# Configuração para ver Encomendas dentro do Cliente (User)
class OrderInlineUser(admin.TabularInline):
    model = Order
    fields = ['id', 'created_at', 'status', 'total_price', 'paid']
    readonly_fields = ['created_at']
    extra = 0
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

# Gestão de Clientes (Aparece no menu da Loja)
@admin.register(Client)
class ClientAdmin(BaseUserAdmin):
    inlines = [OrderInlineUser]
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'email', 'city', 'paid', 'status', 'created_at']
    list_display_links = ['id', 'full_name'] # Permite clicar no ID ou no Nome para ver detalhes
    list_filter = ['paid', 'status', 'created_at']
    inlines = [OrderItemInline]
    
    # Torna os campos informativos apenas de leitura
    readonly_fields = ['user', 'full_name', 'email', 'address', 'city', 'total_price', 'created_at']
    
    # Apenas permitimos editar o Status e o Pagamento para processamento
    # Se quiser bloquear TUDO, adicione 'status' e 'paid' à lista readonly_fields acima.

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    # Impede adicionar mais de uma configuração
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

admin.site.register(PaymentMethod)
admin.site.register(ShippingMethod)
