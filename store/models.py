from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nome da Categoria")
    slug = models.SlugField(unique=True, blank=True)
    
    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE, verbose_name="Categoria")
    name = models.CharField(max_length=255, verbose_name="Nome do Produto")
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, verbose_name="Descrição")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço")
    stock = models.PositiveIntegerField(default=0, verbose_name="Estoque")
    is_active = models.BooleanField(default=True, verbose_name="Ativo?")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Imagem")
    is_featured = models.BooleanField(default=False, verbose_name="Destaque?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ('-created_at',)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/gallery/')
    
    class Meta:
        verbose_name = "Imagem Extra"
        verbose_name_plural = "Imagens Extras"

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    name = models.CharField(max_length=100, verbose_name="Nome (ex: Tamanho XL)")
    price_extra = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Preço Extra")

    def __str__(self):
        return f"{self.name} (+{self.price_extra}€)"

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pendente'),
        ('paid', 'Pago'),
        ('shipped', 'Enviado'),
        ('completed', 'Concluído'),
        ('canceled', 'Cancelado'),
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    address = models.TextField()
    city = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.ForeignKey('PaymentMethod', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Método de Pagamento")
    shipping_method = models.ForeignKey('ShippingMethod', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Método de Envio")

    class Meta:
        ordering = ('-created_at',)
        verbose_name = "Encomenda"
        verbose_name_plural = "Encomendas"

    def __str__(self):
        return f"Encomenda #{self.id}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    
    def get_cost(self):
        return self.price * self.quantity

class SiteSettings(models.Model):
    site_name = models.CharField(max_length=100, default="Minha Loja", verbose_name="Nome da Loja")
    banner_image = models.ImageField(upload_to='banner/', blank=True, null=True, verbose_name="Imagem do Banner")
    banner_title = models.CharField(max_length=100, blank=True, verbose_name="Título do Banner")
    banner_text = models.TextField(blank=True, verbose_name="Texto do Banner")
    primary_color = models.CharField(max_length=7, default="#000000", verbose_name="Cor Principal (Hex)", help_text="Ex: #FF0000")
    contact_email = models.EmailField(blank=True, verbose_name="Email de Contacto")
    
    def save(self, *args, **kwargs):
        # Garante que só existe uma configuração (Singleton)
        if not self.pk and SiteSettings.objects.exists():
            return
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Configuração da Loja"
        verbose_name_plural = "Configurações da Loja"

    def __str__(self):
        return "Configurações Gerais"

class PaymentMethod(models.Model):
    name = models.CharField(max_length=100, verbose_name="Método de Pagamento")
    is_active = models.BooleanField(default=True, verbose_name="Ativo?")

    def __str__(self):
        return self.name

class ShippingMethod(models.Model):
    name = models.CharField(max_length=100, verbose_name="Método de Envio")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Custo")
    is_active = models.BooleanField(default=True, verbose_name="Ativo?")

    def __str__(self):
        return f"{self.name} (+{self.price}€)"

class Client(User):
    class Meta:
        proxy = True
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

class Administrator(User):
    class Meta:
        proxy = True
        verbose_name = "Administrador"
        verbose_name_plural = "Administradores"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, verbose_name="Telefone")
    address = models.TextField(verbose_name="Morada")
    postal_code = models.CharField(max_length=20, verbose_name="Código Postal")

    def __str__(self):
        return f"Perfil de {self.user.username}"
