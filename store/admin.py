from django.contrib import admin
from django import forms
from django.db import models
from decimal import Decimal
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.auth.models import Group
from .models import Category, Product, ProductImage, ProductVariant, Order, OrderItem, SiteSettings, PaymentMethod, ShippingMethod, Client, Administrator, Profile, Ceremony, CeremonyRegistration, Anamnesis, Therapy, Appointment
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

class AnamnesisInline(admin.StackedInline):
    model = Anamnesis
    can_delete = False

class CeremonyRegistrationInline(admin.TabularInline):
    model = CeremonyRegistration
    extra = 0
    readonly_fields = ['full_name', 'email', 'payment_method', 'created_at']
    can_delete = False

@admin.register(Ceremony)
class CeremonyAdmin(admin.ModelAdmin):
    list_display = ['name', 'event_date', 'max_participants', 'get_registrations_count']
    inlines = [CeremonyRegistrationInline]

    def get_registrations_count(self, obj):
        return obj.registrations.count()
    get_registrations_count.short_description = "Inscritos"

@admin.register(CeremonyRegistration)
class CeremonyRegistrationAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'ceremony', 'created_at']
    inlines = [AnamnesisInline]

@admin.register(Therapy)
class TherapyAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'duration_minutes', 'is_active']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['therapy', 'user', 'start_time', 'end_time', 'confirmed']
    list_filter = ['start_time', 'confirmed', 'therapy']
    ordering = ['-start_time']

# --- AGENDA / CALENDÁRIO ---
from django.urls import path
from django.http import JsonResponse

def admin_calendar_view(request):
    context = admin.site.each_context(request)
    context['title'] = 'Agenda de Marcações'
    return TemplateResponse(request, 'admin/calendar.html', context)

def admin_calendar_events(request):
    events = []
    
    # 1. Adicionar Terapias
    appointments = Appointment.objects.all()
    for app in appointments:
        events.append({
            'title': f"{app.therapy.name} ({app.user.first_name})",
            'start': app.start_time.isoformat(),
            'end': app.end_time.isoformat(),
            'color': '#10b981' if app.confirmed else '#f59e0b', # Verde se confirmado, Amarelo se pendente
            'url': reverse('admin:store_appointment_change', args=[app.id])
        })

    # 2. Adicionar Cerimónias
    ceremonies = Ceremony.objects.all()
    for cer in ceremonies:
        events.append({
            'title': f"Cerimónia: {cer.name}",
            'start': cer.event_date.isoformat(),
            'color': '#6366f1', # Roxo
            'url': reverse('admin:store_ceremony_change', args=[cer.id])
        })
    
    return JsonResponse(events, safe=False)


# --- DASHBOARD PERSONALIZADO ---
def admin_dashboard(request, extra_context=None):
    # 1. Top 10 Artigos Mais Vendidos
    top_products = OrderItem.objects.values('product__name').annotate(total_sold=Sum('quantity')).order_by('-total_sold')[:10]

    # 2. Total Vendas (Mês, Semana, Dia) - Apenas encomendas pagas
    now = timezone.now()
    orders = Order.objects.filter(paid=True)
    
    sales_day = orders.filter(created_at__date=now.date()).aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')
    
    start_week = now - timedelta(days=now.weekday())
    sales_week = orders.filter(created_at__gte=start_week).aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')
    
    start_month = now.replace(day=1)
    sales_month = orders.filter(created_at__gte=start_month).aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')

    # 3. Número de Clientes (Excluindo Staff)
    total_clients = Client.objects.filter(is_staff=False).count()

    # 4. Total de Clientes por Cerimónia
    ceremonies = Ceremony.objects.annotate(total_registrations=Count('registrations'))

    # 5. Encomendas Recentes
    recent_orders = Order.objects.order_by('-created_at')[:5]

    # Obtém a lista de apps padrão para manter o menu de gestão acessível
    app_list = admin.site.get_app_list(request)

    context = {
        **admin.site.each_context(request),
        'title': 'Dashboard da Loja',
        'app_list': app_list,
        'top_products': top_products,
        'sales_day': sales_day, 'sales_week': sales_week, 'sales_month': sales_month,
        'total_clients': total_clients, 'ceremonies': ceremonies, 'recent_orders': recent_orders,
    }
    return TemplateResponse(request, 'admin/dashboard.html', context)

# Injetar URLs personalizadas no Admin
original_get_urls = admin.site.get_urls
def get_admin_urls():
    urls = original_get_urls()
    custom_urls = [
        path('agenda/', admin_calendar_view, name='admin_calendar'),
        path('agenda/events/', admin_calendar_events, name='admin_calendar_events'),
    ]
    return custom_urls + urls
admin.site.get_urls = get_admin_urls

# Substitui a página inicial do Admin pelo nosso Dashboard
admin.site.index = admin_dashboard
