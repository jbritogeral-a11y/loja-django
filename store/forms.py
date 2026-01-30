from django import forms
from django.contrib.auth.models import User
from .models import Order, Client, CeremonyRegistration, Anamnesis, PaymentMethod, Appointment
from django.utils import timezone
from datetime import timedelta

class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['full_name', 'email', 'address', 'city', 'payment_method', 'shipping_method']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Palavra-passe")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirmar Palavra-passe")
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True, label="Primeiro Nome")
    last_name = forms.CharField(required=True, label="Último Nome")

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password") != cleaned_data.get("confirm_password"):
            self.add_error('confirm_password', "As palavras-passe não coincidem.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            # Garante que é Cliente
            Client.objects.filter(pk=user.pk).update(is_staff=False, is_superuser=False)
        return user

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class CeremonyRegistrationForm(forms.ModelForm):
    # Filtra apenas métodos de pagamento ativos
    payment_method = forms.ModelChoiceField(
        queryset=PaymentMethod.objects.filter(is_active=True),
        label="Método de Pagamento",
        empty_label="Selecione um método"
    )

    class Meta:
        model = CeremonyRegistration
        fields = ['full_name', 'email', 'payment_method']

class AnamnesisForm(forms.ModelForm):
    class Meta:
        model = Anamnesis
        exclude = ['registration', 'created_at']
        widgets = {
            'health_issues': forms.Textarea(attrs={'rows': 3}),
            'medications': forms.Textarea(attrs={'rows': 2}),
            'goals': forms.Textarea(attrs={'rows': 3}),
        }

class ContactForm(forms.Form):
    name = forms.CharField(label="Nome", max_length=100)
    email = forms.EmailField(label="Email")
    subject = forms.CharField(label="Assunto", max_length=200)
    message = forms.CharField(label="Mensagem", widget=forms.Textarea(attrs={'rows': 5}))

class AppointmentForm(forms.ModelForm):
    start_time = forms.DateTimeField(
        label="Data e Hora Preferida",
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        help_text="Selecione a data e hora para a sessão."
    )

    class Meta:
        model = Appointment
        fields = ['start_time']

    def clean_start_time(self):
        start_time = self.cleaned_data['start_time']
        if start_time < timezone.now():
            raise forms.ValidationError("Não é possível agendar para o passado.")
        return start_time

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        
        # A validação de sobreposição complexa é feita na view ou aqui se tivermos acesso à duração
        # Vamos deixar a lógica pesada para a view onde temos acesso à instância da Terapia
        
        return cleaned_data