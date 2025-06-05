# Etapa 1: Use uma imagem base oficial do Python
FROM python:3.11-slim

# Etapa 2: Crie e defina o diretório de trabalho dentro do container
WORKDIR /app

# Etapa 3: Copie o arquivo de dependências primeiro para otimizar o cache
COPY requirements.txt ./requirements.txt

# Etapa 4: Instale as dependências
# --no-cache-dir economiza espaço na imagem
RUN pip install --no-cache-dir -r requirements.txt

# Etapa 5: Copie todo o código da sua aplicação para o diretório de trabalho
COPY . .

# Etapa 6: Exponha a porta que o Cloud Run usará para se comunicar com o container
# O Cloud Run espera a porta 8080 por padrão.
EXPOSE 8080

# Etapa 7: Comando para iniciar a aplicação Streamlit quando o container rodar
# Usamos a variável de ambiente $PORT que o Cloud Run fornece.
CMD ["streamlit", "run", "app.py", "--server.port", "8080", "--server.address", "0.0.0.0"]