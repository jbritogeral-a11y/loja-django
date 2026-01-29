from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('produto/<slug:slug>/', views.product_detail, name='product_detail'),
    path('carrinho/', views.cart_detail, name='cart_detail'),
    path('carrinho/adicionar/<int:product_id>/', views.cart_add, name='cart_add'),
    path('carrinho/remover/<str:cart_key>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('minha-conta/', views.profile, name='profile'),
]