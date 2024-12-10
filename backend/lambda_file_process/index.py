import json
import boto3
import redis
import os

def count_lines(content):
    return len(content.split('\n'))

def handler(event, context):
    # Configurações
    redis_host = os.environ['REDIS_HOST']
    redis_port = 6379
    
    try:
        # Obter informações do evento S3
        bucket_name = event['Records'][0]['s3']['bucket']['name']
        file_name = event['Records'][0]['s3']['object']['key']
        
        # Ler arquivo do S3
        s3_client = boto3.client('s3')
        response = s3_client.get_object(
            Bucket=bucket_name,
            Key=file_name
        )
        content = response['Body'].read().decode('utf-8')
        
        # Contar linhas
        num_lines = count_lines(content)
        
        # Salvar metadados no Redis
        redis_client = redis.Redis(host=redis_host, port=redis_port)
        file_metadata = {
            'lines': num_lines,
            'processed_at': response['LastModified'].strftime('%Y-%m-%d %H:%M:%S')
        }
        
        redis_client.hmset(f"file:{file_name}", file_metadata)
        
        # Invalidar cache da listagem
        redis_client.delete('file_metadata')
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'file': file_name,
                'lines': num_lines
            })
        }
        
    except Exception as e:
        print(f"Erro ao processar arquivo: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }