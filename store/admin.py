from django.contrib import admin
from .models import Category, Product, ProductImage, ProductVariant, Order, OrderItem, SiteSettings, PaymentMethod, ShippingMethod

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

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'email', 'city', 'paid', 'status', 'created_at']
    list_filter = ['paid', 'status', 'created_at']
    inlines = [OrderItemInline]

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    # Impede adicionar mais de uma configuração
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

admin.site.register(PaymentMethod)
admin.site.register(ShippingMethod)
