from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('categoria/<slug:category_slug>/', views.product_list, name='category_detail'),
    path('produto/<slug:slug>/', views.product_detail, name='product_detail'),
    path('carrinho/', views.cart_detail, name='cart_detail'),
    path('carrinho/adicionar/<int:product_id>/', views.cart_add, name='cart_add'),
    path('carrinho/remover/<str:cart_key>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('minha-conta/', views.profile, name='profile'),
    path('registar/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='store/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('cerimonias/', views.ceremony_list, name='ceremony_list'),
    path('cerimonias/<int:ceremony_id>/', views.ceremony_detail, name='ceremony_detail'),
    path('cerimonias/anamnese/<int:registration_id>/', views.anamnesis_view, name='anamnesis'),
    path('contactos/', views.contact_view, name='contact'),
]