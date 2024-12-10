import json
import boto3
import redis
import os

def handler(event, context):
    # Configurações
    redis_host = os.environ['REDIS_HOST']
    redis_port = 6379
    bucket_name = os.environ['DATA_BUCKET_NAME']
    
    try:
        # Obter nome do arquivo dos parâmetros da rota
        file_name = event['pathParameters']['filename']
        
        # Deletar do S3
        s3_client = boto3.client('s3')
        s3_client.delete_object(
            Bucket=bucket_name,
            Key=file_name
        )
        
        # Remover metadados do Redis
        redis_client = redis.Redis(host=redis_host, port=redis_port)
        redis_client.delete(f"file:{file_name}")
        
        # Invalidar cache da listagem
        redis_client.delete('file_metadata')
        
        # Enviar notificação SNS
        sns_client = boto3.client('sns')
        sns_client.publish(
            TopicArn=os.environ['SNS_TOPIC_ARN'],
            Message=f"Arquivo {file_name} foi deletado do bucket {bucket_name}",
            Subject='Arquivo Deletado'
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True
            },
            'body': json.dumps({
                'message': f'Arquivo {file_name} deletado com sucesso'
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