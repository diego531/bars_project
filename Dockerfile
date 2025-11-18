# Usa una imagen base de Python
FROM python:3.9-slim-buster

# --- instalar git dentro del contenedor ---
RUN apt-get update && apt-get install -y git && apt-get clean

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos de requisitos e instala las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de la aplicación
COPY . .

# Expone el puerto en el que Flask se ejecutará
EXPOSE 5000

# Define la variable de entorno para Flask
ENV FLASK_APP=app.py

# Comando para ejecutar la aplicación cuando el contenedor se inicie
CMD ["flask", "run", "--host", "0.0.0.0"]
