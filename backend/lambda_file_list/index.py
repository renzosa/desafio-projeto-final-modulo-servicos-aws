import json
import boto3
import redis
import os

def handler(event, context):
    # Configurações do Redis
    redis_host = os.environ['REDIS_HOST']
    redis_port = 6379
    
    try:
        # Conexão com Redis
        redis_client = redis.Redis(host=redis_host, port=redis_port)
        
        # Tentar recuperar do cache primeiro
        cached_data = redis_client.get('file_metadata')
        if cached_data:
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Credentials': True
                },
                'body': cached_data.decode('utf-8')
            }
        
        # Se não estiver em cache, buscar do S3
        s3_client = boto3.client('s3')
        bucket_name = os.environ['DATA_BUCKET_NAME']
        
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        
        files = []
        for item in response.get('Contents', []):
            # Recuperar metadados do próprio Redis
            metadata = redis_client.hgetall(f"file:{item['Key']}")
            
            if metadata:
                files.append({
                    'name': item['Key'],
                    'lines': int(metadata.get(b'lines', 0)),
                    'size': item['Size']
                })
        
        # Atualizar cache
        redis_client.setex('file_metadata', 300, json.dumps(files))  # Cache por 5 minutos
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True
            },
            'body': json.dumps(files)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True
            },
            'body': json.dumps({'error': str(e)})
        }