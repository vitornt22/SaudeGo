FROM python:3.10-slim

# Evita buffering no console
ENV PYTHONUNBUFFERED 1

# Diretório da aplicação
WORKDIR /app

# Instalar dependências do sistema (ex: psycopg2, Pillow etc.)
RUN apt-get update && apt-get install -y \
	build-essential \
	libpq-dev \
	&& rm -rf /var/lib/apt/lists/*

# Copia requirements primeiro (melhor cache)
COPY requirements.txt /app/

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o projeto
COPY . /app/

# Expõe a porta do Django
EXPOSE 8004

# Comando para iniciar o servidor
CMD ["python", "manage.py", "runserver", "0.0.0.0:8004"]
