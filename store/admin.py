from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.auth.models import Group
from .models import Category, Product, ProductImage, ProductVariant, Order, OrderItem, SiteSettings, PaymentMethod, ShippingMethod, Client
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

admin.site.unregister(Group) # Remove "Grupos" para limpar o CMS

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
    list_display = ['username', 'email', 'get_last_city', 'date_joined']
    list_filter = ['is_active', 'date_joined']
    
    def get_last_city(self, obj):
        # Tenta obter a cidade da última encomenda do cliente
        last_order = Order.objects.filter(user=obj).order_by('-created_at').first()
        return last_order.city if last_order else "-"
    get_last_city.short_description = "Cidade (Última)"

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'link_to_client', 'get_items_summary', 'total_price', 'paid', 'status', 'created_at']
    list_display_links = ['id', 'full_name'] 
    list_filter = ['paid', 'status', 'created_at']
    inlines = [OrderItemInline]
    
    # Torna os campos informativos apenas de leitura
    readonly_fields = ['user', 'full_name', 'email', 'address', 'city', 'total_price', 'created_at']
    
    # Apenas permitimos editar o Status e o Pagamento para processamento
    # Se quiser bloquear TUDO, adicione 'status' e 'paid' à lista readonly_fields acima.

    def link_to_client(self, obj):
        if obj.user:
            # Cria um link HTML para a página de edição do Cliente
            link = reverse("admin:store_client_change", args=[obj.user.id])
            return format_html('<a href="{}" style="font-weight:bold;">Ver Ficha</a>', link)
        return "Visitante"
    link_to_client.short_description = "Cliente"

    def get_items_summary(self, obj):
        items = obj.items.all()
        return ", ".join([f"{item.quantity}x {item.product.name}" for item in items])
    get_items_summary.short_description = "Artigos na Encomenda"

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    # Impede adicionar mais de uma configuração
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

admin.site.register(PaymentMethod)
admin.site.register(ShippingMethod)
