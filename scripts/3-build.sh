#!/bin/bash

# Configurar variáveis
DEPLOY_DIR="../todeploy"
FRONTEND_DIR="../frontend"
BACKEND_DIR="../backend"
STATE_FILE="infra.state"

# Verificar se jq está instalado
if ! command -v jq &> /dev/null; then
    echo "Instalando jq..."
    sudo apt-get update && sudo apt-get install -y jq
fi

# Função para empacotar uma lambda
package_lambda() {
    LAMBDA_NAME=$1
    LAMBDA_DIR="$BACKEND_DIR/$LAMBDA_NAME"
    OUTPUT_FILE="$DEPLOY_DIR/${LAMBDA_NAME}.zip"
    
    echo "Empacotando $LAMBDA_NAME..."
    
    # Criar diretório temporário
    TMP_DIR=$(mktemp -d)
    
    # Copiar arquivos
    cp -r $LAMBDA_DIR/* $TMP_DIR/
    
    # Instalar dependências
    if [ -f "$TMP_DIR/requirements.txt" ]; then
        pip install -r "$TMP_DIR/requirements.txt" -t "$TMP_DIR/"
    fi
    
    # Criar ZIP
    cd $TMP_DIR
    zip -r $OUTPUT_FILE ./*
    cd - > /dev/null
    
    # Limpar
    rm -rf $TMP_DIR
    
    echo "$LAMBDA_NAME empacotado com sucesso!"
}

# Função para gerar arquivo .env do frontend
generate_frontend_env() {
    if [ ! -f "$STATE_FILE" ]; then
        echo "Arquivo de estado não encontrado!"
        exit 1
    }

    echo "Gerando arquivo .env para o frontend..."
    
    # Extrair valores do arquivo de estado
    CLOUDFRONT_URL="https://$(jq -r .cloudfront_distribution_id $STATE_FILE).cloudfront.net"
    API_URL="$(jq -r .api_gateway.url $STATE_FILE)"
    USER_POOL_ID="$(jq -r .cognito.user_pool_id $STATE_FILE)"
    CLIENT_ID="$(jq -r .cognito.client_id $STATE_FILE)"
    DATA_BUCKET="$(jq -r .data_bucket $STATE_FILE)"
    REGION="$(jq -r .aws_region $STATE_FILE)"
    
    # Criar arquivo .env
    cat > $FRONTEND_DIR/.env << EOF
REACT_APP_API_URL=$API_URL
REACT_APP_USER_POOL_ID=$USER_POOL_ID
REACT_APP_CLIENT_ID=$CLIENT_ID
REACT_APP_CLOUDFRONT_URL=$CLOUDFRONT_URL
REACT_APP_DATA_BUCKET=$DATA_BUCKET
REACT_APP_AWS_REGION=$REGION
EOF

    echo "Arquivo .env gerado com sucesso!"
}

# Limpar diretório de deploy
echo "Limpando diretório de deploy..."
rm -rf $DEPLOY_DIR
mkdir -p $DEPLOY_DIR

# Build do Frontend
echo "Iniciando build do frontend..."
cd $FRONTEND_DIR

# Gerar arquivo .env
generate_frontend_env

# Verificar se o .env foi gerado corretamente
if [ ! -f ".env" ]; then
    echo "Erro ao gerar arquivo .env!"
    exit 1
fi

echo "Instalando dependências do frontend..."
npm install

echo "Buildando frontend..."
npm run build

# Verificar se o build foi bem sucedido
if [ ! -d "build" ]; then
    echo "Erro no build do frontend!"
    exit 1
fi

echo "Empacotando frontend..."
cd build
zip -r $DEPLOY_DIR/frontend.zip ./*
cd ../..

echo "Frontend processado com sucesso!"

# Build das Lambdas
echo "Iniciando build das lambdas..."

# Array com os nomes das lambdas
LAMBDAS=("lambda_file_list" "lambda_file_generate" "lambda_file_delete" "lambda_file_process")

# Processar cada lambda
for lambda in "${LAMBDAS[@]}"; do
    package_lambda "$lambda"
done

# Verificar se todos os arquivos necessários foram gerados
echo "Verificando arquivos gerados..."
FILES_TO_CHECK=("frontend.zip" "${LAMBDAS[@]/%/.zip}")
for file in "${FILES_TO_CHECK[@]}"; do
    if [ ! -f "$DEPLOY_DIR/$file" ]; then
        echo "Erro: Arquivo $file não foi gerado!"
        exit 1
    fi
done

echo "Build concluído com sucesso!"
echo "Arquivos gerados em $DEPLOY_DIR:"
ls -lh $DEPLOY_DIR