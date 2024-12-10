import boto3
import logging
import json

class SQSManager:
    def __init__(self, project_name):
        self.project_name = project_name
        self.sqs_client = boto3.client('sqs')
        self.logger = logging.getLogger(__name__)

    def create_queue(self, sns_topic_arn=None):
        """
        Cria uma fila SQS e opcionalmente a inscreve em um tópico SNS
        """
        try:
            # Criar fila
            queue_name = f"{self.project_name}-notifications-queue"
            
            response = self.sqs_client.create_queue(
                QueueName=queue_name,
                Attributes={
                    'VisibilityTimeout': '30',
                    'MessageRetentionPeriod': '86400',  # 1 dia
                    'ReceiveMessageWaitTimeSeconds': '20'  # Long polling
                }
            )
            
            queue_url = response['QueueUrl']
            
            # Obter ARN da fila
            queue_attrs = self.sqs_client.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=['QueueArn']
            )
            queue_arn = queue_attrs['Attributes']['QueueArn']
            
            # Se um tópico SNS foi fornecido, configurar a assinatura
            if sns_topic_arn:
                # Configurar política de acesso para permitir SNS
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Sid": "AllowSNSPublish",
                            "Effect": "Allow",
                            "Principal": {
                                "Service": "sns.amazonaws.com"
                            },
                            "Action": "sqs:SendMessage",
                            "Resource": queue_arn,
                            "Condition": {
                                "ArnEquals": {
                                    "aws:SourceArn": sns_topic_arn
                                }
                            }
                        }
                    ]
                }
                
                self.sqs_client.set_queue_attributes(
                    QueueUrl=queue_url,
                    Attributes={
                        'Policy': json.dumps(policy)
                    }
                )
                
                # Inscrever a fila no tópico SNS
                sns_client = boto3.client('sns')
                sns_client.subscribe(
                    TopicArn=sns_topic_arn,
                    Protocol='sqs',
                    Endpoint=queue_arn
                )
            
            return {
                'queue_url': queue_url,
                'queue_arn': queue_arn
            }

        except Exception as e:
            self.logger.error(f"Erro ao criar fila SQS: {str(e)}")
            raise

    def delete_queue(self, queue_url):
        """
        Remove uma fila SQS
        """
        try:
            self.sqs_client.delete_queue(
                QueueUrl=queue_url
            )
            self.logger.info(f"Fila SQS {queue_url} removida com sucesso")

        except Exception as e:
            self.logger.error(f"Erro ao remover fila SQS: {str(e)}")
            raise

    def send_message(self, queue_url, message):
        """
        Envia uma mensagem para a fila
        """
        try:
            response = self.sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(message)
            )
            return response['MessageId']

        except Exception as e:
            self.logger.error(f"Erro ao enviar mensagem para fila: {str(e)}")
            raise

    def receive_messages(self, queue_url, max_messages=10):
        """
        Recebe mensagens da fila
        """
        try:
            response = self.sqs_client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=20  # Long polling
            )
            
            messages = response.get('Messages', [])
            
            # Delete mensagens recebidas
            for message in messages:
                self.sqs_client.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=message['ReceiptHandle']
                )
            
            return [json.loads(message['Body']) for message in messages]

        except Exception as e:
            self.logger.error(f"Erro ao receber mensagens da fila: {str(e)}")
            raise

    def purge_queue(self, queue_url):
        """
        Remove todas as mensagens da fila
        """
        try:
            self.sqs_client.purge_queue(
                QueueUrl=queue_url
            )
            self.logger.info(f"Fila SQS {queue_url} limpa com sucesso")

        except Exception as e:
            self.logger.error(f"Erro ao limpar fila SQS: {str(e)}")
            raise