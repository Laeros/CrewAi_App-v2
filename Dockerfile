# Usa imagen base optimizada de Python
FROM python:3.11-slim

# Establecer directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la app
COPY . .

# Expone el puerto que Gunicorn usará
EXPOSE 5000

# Comando para producción con Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]
