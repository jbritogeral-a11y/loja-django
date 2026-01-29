#!/bin/bash

# 1. Puxar código novo
echo "--> A puxar alteracoes do GitHub..."
git pull

# 2. Instalar bibliotecas novas (caso existam)
echo "--> A verificar dependencias..."
pip install -r requirements.txt

# 3. Atualizar Base de Dados e Estáticos
echo "--> A atualizar Base de Dados e Ficheiros Estaticos..."
python manage.py migrate
python manage.py collectstatic --no-input

# 4. Tentar recarregar o site (Truque para evitar ir ao botão Reload)
# Isto toca no ficheiro WSGI para forçar o reload
echo "--> A recarregar o site..."
touch /var/www/*_wsgi.py

echo "--> SUCESSO! O site esta atualizado."