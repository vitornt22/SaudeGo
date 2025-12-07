# Use Python 3.10 como base
FROM python:3.10-slim

# Diretório de trabalho
WORKDIR /app

# Copia os requisitos
COPY requirements.txt .

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante da aplicação
COPY . .

# Expõe a porta da FastAPI
EXPOSE 8002

# Comando para iniciar a API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]
