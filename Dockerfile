# Base image
FROM registry.access.redhat.com/ubi9/s2i-base:latest

# Diretório da aplicação
WORKDIR /app

# Copia arquivos para dentro da imagem
COPY . .

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Garante permissão total na pasta de dados (como você pediu)
RUN mkdir -p /app/dados/jobs && chmod -R 777 /app/dados

# Expõe a porta
EXPOSE 5000

# Comando para rodar o servidor com Hypercorn
CMD ["hypercorn", "app:app", "--bind", "0.0.0.0:5000"]
