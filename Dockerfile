# Usa una imagen liviana de Python
FROM python:3.11-slim

# Evita que Python genere archivos .pyc
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Define el directorio de trabajo
WORKDIR /app

# Instala dependencias del sistema necesarias para pip
RUN apt-get update && apt-get install -y build-essential gcc

# Copia dependencias e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código
COPY . .

# Expone el puerto de Flask
EXPOSE 5000

# Variables de entorno
ENV FLASK_ENV=production
ENV FLASK_APP=manage.py
ENV PORT=5000

# Comando de inicio (puedes cambiar a gunicorn si deseas)
CMD ["python", "manage.py", "run", "--host=0.0.0.0", "--port=5000"]
