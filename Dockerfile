# Usa una imagen liviana de Python
FROM python:3.11-slim

# Define el directorio de trabajo
WORKDIR /app

# Copia dependencias e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código
COPY . .

# Expone el puerto de Flask
EXPOSE 5000

# Variable de entorno para producción
ENV FLASK_ENV=production
ENV FLASK_APP=manage.py
ENV PORT=5000

# Comando de inicio (puedes reemplazar con gunicorn si quieres producción real)
CMD ["python", "manage.py", "run", "--host=0.0.0.0", "--port=5000"]
