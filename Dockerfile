FROM python:3.11-slim

# Configurações Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Instalar dependências de sistema (Resolve o erro do Pillow e Postgres)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências do projeto
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código
COPY . /app/

# Comando de arranque: Prepara estáticos, base de dados e inicia o servidor
CMD sh -c "python manage.py collectstatic --no-input && python manage.py migrate && gunicorn --bind 0.0.0.0:8080 config.wsgi:application"