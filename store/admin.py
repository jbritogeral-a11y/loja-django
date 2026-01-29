from django.contrib import admin
from django import forms
from django.db import models
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.auth.models import Group
from .models import Category, Product, ProductImage, ProductVariant, Order, OrderItem, SiteSettings, PaymentMethod, ShippingMethod, Client, Administrator, Profile
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

admin.site.unregister(Group) # Remove "Grupos" para limpar o CMS
admin.site.unregister(User) # Remove o menu "Users" original para evitar confusão

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

class ProfileInline(admin.TabularInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Dados Pessoais'
    min_num = 1
    # Reduz o tamanho da caixa de texto da morada para ficar mais elegante
    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'rows': 2, 'style': 'width: 350px;'})},
    }

# Configuração para ver Encomendas dentro do Cliente (User)
class OrderInlineUser(admin.TabularInline):
    model = Order
    fields = ['display_id', 'created_at', 'status', 'total_price', 'paid']
    readonly_fields = ['display_id', 'created_at']
    extra = 0
    can_delete = False
    show_change_link = False
    verbose_name_plural = "Histórico de Encomendas"
    
    def has_add_permission(self, request, obj=None):
        return False

    def display_id(self, obj):
        url = reverse("admin:store_order_change", args=[obj.id])
        return format_html(
            '<div style="display: flex; align-items: center;">'
            '<span style="font-size: 1.5rem; font-weight: bold; margin-right: 15px;">#{}</span>'
            '<a href="{}" style="background-color: #2563eb; color: white; padding: 6px 12px; border-radius: 4px; font-weight: bold; text-decoration: none; font-size: 12px; text-transform: uppercase;">VER DETALHES</a>'
            '</div>',
            obj.id, url
        )
    display_id.short_description = "Encomenda"

# --- GESTÃO DE CLIENTES (APENAS CLIENTES) ---
@admin.register(Client)
class ClientAdmin(BaseUserAdmin):
    inlines = [ProfileInline, OrderInlineUser]
    list_display = ('username', 'email', 'first_name', 'last_name', 'date_joined')
    list_filter = ('date_joined',)
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

    # 1. Mostra apenas utilizadores que NÃO SÃO administradores
    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_staff=False)

    # 2. Garante que um novo utilizador criado aqui é SEMPRE um cliente
    def save_model(self, request, obj, form, change):
        obj.is_staff = False
        obj.is_superuser = False
        super().save_model(request, obj, form, change)

    # Torna Nome e Email obrigatórios no Admin
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['first_name'].required = True
        form.base_fields['last_name'].required = True
        form.base_fields['email'].required = True
        return form

    # 3. Esconde todos os campos de permissões do formulário
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informação Pessoal', {'fields': ('first_name', 'last_name', 'email')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {'fields': ('first_name', 'last_name')}),
    )
    filter_horizontal = ()

# --- GESTÃO DE ADMINISTRADORES (APENAS STAFF) ---
@admin.register(Administrator)
class AdministratorAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'is_superuser', 'last_login')
    list_filter = ('is_superuser',)
    search_fields = ('username', 'email')
    ordering = ('username',)
    
    # Mostra apenas utilizadores que SÃO administradores
    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_staff=True)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'link_to_client', 'get_items_summary', 'total_price', 'paid', 'status', 'created_at']
    list_display_links = ['id', 'full_name'] 
    list_filter = ['paid', 'status', 'created_at']
    search_fields = ['id', 'full_name', 'email', 'user__username'] # Pesquisa por ID, Nome, Email
    inlines = [OrderItemInline]
    
    # Organização visual da Ficha de Encomenda
    fieldsets = (
        ('Estado da Encomenda', {
            'fields': (('status', 'paid'), 'created_at')
        }),
        ('Detalhes Financeiros', {
            'fields': (('total_price', 'payment_method'), 'shipping_method')
        }),
        ('Dados do Cliente (Cópia no momento da compra)', {
            'classes': ('collapse',),
            'fields': ('full_name', 'email', ('address', 'city'), 'user')
        }),
    )
    
    # Campos que não devem ser editados para manter integridade histórica
    readonly_fields = ['user', 'full_name', 'email', 'address', 'city', 'payment_method', 'shipping_method', 'total_price', 'created_at']

    def link_to_client(self, obj):
        if obj.user:
            # Link inteligente: vai para a ficha de Cliente ou de Administrador
            if obj.user.is_staff:
                url_name = "admin:store_administrator_change"
                label = "Ver Admin"
            else:
                url_name = "admin:store_client_change"
                label = "Ver Cliente"
            link = reverse(url_name, args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', link, label)
        return "Visitante"
    link_to_client.short_description = "Ficha"

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
