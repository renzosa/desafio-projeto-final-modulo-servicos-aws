import boto3
import logging

class SNSManager:
    def __init__(self, project_name):
        self.project_name = project_name
        self.sns_client = boto3.client('sns')
        self.logger = logging.getLogger(__name__)
        # Definindo assinantes padrão
        self.default_email = 'renzo.sa@gmail.com'
        self.default_phone = '+5596981140747'

    def create_topic(self):
        """
        Cria um tópico SNS para notificações e adiciona assinaturas padrão
        """
        try:
            # Criar tópico
            topic = self.sns_client.create_topic(
                Name=f"{self.project_name}-notifications"
            )
            
            topic_arn = topic['TopicArn']
            
            # Adicionar política padrão
            self.sns_client.set_topic_attributes(
                TopicArn=topic_arn,
                AttributeName='Policy',
                AttributeValue='''{
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {
                                "Service": "lambda.amazonaws.com"
                            },
                            "Action": "sns:Publish",
                            "Resource": "''' + topic_arn + '''"
                        }
                    ]
                }'''
            )

            # Adicionar assinatura de email
            self.add_email_subscription(topic_arn, self.default_email)

            # Adicionar assinatura de SMS
            self.add_sms_subscription(topic_arn, self.default_phone)
            
            return topic_arn

        except Exception as e:
            self.logger.error(f"Erro ao criar tópico SNS: {str(e)}")
            raise

    def add_email_subscription(self, topic_arn, email):
        """
        Adiciona uma assinatura de email ao tópico
        """
        try:
            response = self.sns_client.subscribe(
                TopicArn=topic_arn,
                Protocol='email',
                Endpoint=email
            )
            self.logger.info(f"Assinatura de email {email} adicionada com sucesso")
            return response['SubscriptionArn']

        except Exception as e:
            self.logger.error(f"Erro ao adicionar assinatura de email: {str(e)}")
            raise

    def add_sms_subscription(self, topic_arn, phone_number):
        """
        Adiciona uma assinatura de SMS ao tópico
        """
        try:
            response = self.sns_client.subscribe(
                TopicArn=topic_arn,
                Protocol='sms',
                Endpoint=phone_number
            )
            self.logger.info(f"Assinatura de SMS {phone_number} adicionada com sucesso")
            return response['SubscriptionArn']

        except Exception as e:
            self.logger.error(f"Erro ao adicionar assinatura de SMS: {str(e)}")
            raise

    def delete_topic(self, topic_arn):
        """
        Remove um tópico SNS e suas assinaturas
        """
        try:
            # Listar e remover assinaturas
            subscriptions = self.sns_client.list_subscriptions_by_topic(
                TopicArn=topic_arn
            )
            
            for sub in subscriptions['Subscriptions']:
                if 'SubscriptionArn' in sub and sub['SubscriptionArn'] != 'PendingConfirmation':
                    self.sns_client.unsubscribe(
                        SubscriptionArn=sub['SubscriptionArn']
                    )
            
            # Remover tópico
            self.sns_client.delete_topic(
                TopicArn=topic_arn
            )
            
            self.logger.info(f"Tópico SNS {topic_arn} removido com sucesso")

        except Exception as e:
            self.logger.error(f"Erro ao remover tópico SNS: {str(e)}")
            raise

    def publish_message(self, topic_arn, message, subject=None):
        """
        Publica uma mensagem no tópico
        """
        try:
            params = {
                'TopicArn': topic_arn,
                'Message': message
            }
            
            if subject:
                params['Subject'] = subject

            response = self.sns_client.publish(**params)
            return response['MessageId']

        except Exception as e:
            self.logger.error(f"Erro ao publicar mensagem: {str(e)}")
            raise