# Usa una imagen base de Python
FROM python:3.9

# Instala paquetes necesarios para ODBC y agrega los repos de Microsoft
RUN apt-get update && apt-get install -y curl gnupg2 unixodbc unixodbc-dev && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql17

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos del proyecto al contenedor
COPY . .

# Instala las dependencias necesarias 
RUN pip install --no-cache-dir flask fpdf pyodbc

# Expone el puerto en el que Flask correrá
EXPOSE 5000

# Comando para ejecutar la API
CMD ["python", "app.py"]

