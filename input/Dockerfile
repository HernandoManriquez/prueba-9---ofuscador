# Usa una imagen oficial de Python como base
FROM python:3.9-slim

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia los archivos necesarios al contenedor
COPY requirements.txt .
COPY app.py .
COPY templates ./templates
COPY static ./static

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Informa a Docker que la aplicación escucha en el puerto 5000
EXPOSE 5000

# Define la variable de entorno para Flask
ENV FLASK_APP=app.py

# Ejecuta la aplicación cuando se inicie el contenedor
CMD ["flask", "run", "--host=0.0.0.0"]