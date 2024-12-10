#!/bin/bash

echo "Iniciando setup do ambiente..."

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "Python 3 não encontrado. Instalando..."
    sudo apt-get update && sudo apt-get install -y python3 python3-pip
fi

# Verificar Node.js
if ! command -v node &> /dev/null; then
    echo "Node.js não encontrado. Instalando..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

# Verificar AWS CLI
if ! command -v aws &> /dev/null; then
    echo "AWS CLI não encontrado. Instalando..."
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
    rm -rf aws awscliv2.zip
fi

# Instalar dependências Python
echo "Instalando dependências Python..."
pip3 install -r ../backend/requirements.txt
pip3 install boto3 python-dotenv

# Configurar AWS CLI
echo "Configurando AWS CLI..."
echo "Por favor, insira suas credenciais AWS:"
aws configure

# Criar pasta todeploy
mkdir -p ../todeploy

echo "Setup concluído com sucesso!"