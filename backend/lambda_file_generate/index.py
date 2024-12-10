import json
import boto3
import redis
import os
import random
import uuid
from datetime import datetime

def generate_random_content(num_lines):
    content = []
    for i in range(num_lines):
        line = f"Linha {i+1}: " + ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=20))
        content.append(line)
    return '\n'.join(content)

def handler(event, context):
    # Configurações
    redis_host = os.environ['REDIS_HOST']
    redis_port = 6379
    bucket_name = os.environ['DATA_BUCKET_NAME']
    
    try:
        # Gerar arquivo com conteúdo aleatório
        num_lines = random.randint(10, 99)
        content = generate_random_content(num_lines)
        
        # Nome único para o arquivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"file_{timestamp}_{str(uuid.uuid4())[:8]}.txt"
        
        # Upload para S3
        s3_client = boto3.client('s3')
        s3_client.put_object(
            Bucket=bucket_name,
            Key=file_name,
            Body=content.encode('utf-8')
        )
        
        # Salvar metadados no Redis
        redis_client = redis.Redis(host=redis_host, port=redis_port)
        file_metadata = {
            'lines': num_lines,
            'created_at': timestamp
        }
        
        redis_client.hmset(f"file:{file_name}", file_metadata)
        
        # Invalidar cache da listagem
        redis_client.delete('file_metadata')
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True
            },
            'body': json.dumps({
                'name': file_name,
                'lines': num_lines
            })
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