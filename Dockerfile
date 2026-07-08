# Usa uma imagem oficial do Python baseada em Linux
FROM python:3.11-slim

# Evita que o Python crie arquivos .pyc e força o log no terminal
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instala dependências do sistema necessárias para o Chrome e Xvfb
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    xvfb \
    unzip \
    curl \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# Instala o Google Chrome
RUN wget -q -O - https://dl.ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia os arquivos do seu PC para o contêiner
COPY requirements.txt .
COPY gerar_manga.py .

# Instala as bibliotecas do Python
RUN pip install --no-cache-dir -r requirements.txt

# O comando que o Docker vai rodar quando ligar
CMD ["xvfb-run", "python", "gerar_manga.py"]