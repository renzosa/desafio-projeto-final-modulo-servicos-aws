import os
import sys
import json
import logging
from importlib import import_module

# Adicionar diretório raiz ao path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InfrastructureBuilder:
    def __init__(self, project_name):
        self.project_name = project_name
        self.state = {}
        self.load_state()

    def load_state(self):
        """Carrega estado existente se houver"""
        try:
            with open('infra.state', 'r') as f:
                self.state = json.load(f)
        except FileNotFoundError:
            self.state = {}

    def save_state(self):
        """Salva estado atual"""
        with open('infra.state', 'w') as f:
            json.dump(self.state, f, indent=2)

    def build_infrastructure(self):
        try:
            # 1. Criar VPC e sub-redes (necessário para ElastiCache)
            vpc_manager = import_module('modulos.vpc.vpc_manager').VPCManager(self.project_name)
            vpc_info = vpc_manager.create_vpc()
            self.state['vpc'] = vpc_info

            # 2. Criar buckets S3
            s3_manager = import_module('modulos.s3.s3_manager').S3Manager(self.project_name)
            self.state['frontend_bucket'] = s3_manager.create_bucket('frontend')
            self.state['data_bucket'] = s3_manager.create_bucket('data')

            # 3. Criar cluster ElastiCache
            cache_manager = import_module('modulos.cache.cache_manager').ElastiCacheManager(self.project_name)
            cache_info = cache_manager.create_redis_cluster(
                vpc_info['vpc_id'], 
                [vpc_info['private_subnet_id']]
            )
            self.state['elasticache'] = cache_info

            # 4. Criar tópico SNS e assinaturas
            sns_manager = import_module('modulos.sns.notification_manager').SNSManager(self.project_name)
            topic_arn = sns_manager.create_topic()
            self.state['sns_topic_arn'] = topic_arn

            # 5. Criar fila SQS e vincular ao SNS
            sqs_manager = import_module('modulos.sqs.queue_manager').SQSManager(self.project_name)
            queue_info = sqs_manager.create_queue(topic_arn)
            self.state['sqs'] = queue_info

            # 6. Criar User Pool Cognito
            cognito_manager = import_module('modulos.cognito.auth_manager').CognitoManager(self.project_name)
            cognito_info = cognito_manager.create_user_pool(
                admin_email='admin@meusite.com',
                admin_password='teste123'
            )
            self.state['cognito'] = cognito_info

            # 7. Criar funções Lambda
            lambda_manager = import_module('modulos.lambdas.lambda_manager').LambdaManager(self.project_name)
            lambda_role = lambda_manager.create_lambda_role()
            self.state['lambda_role_arn'] = lambda_role

            # 8. Criar API Gateway
            gateway_manager = import_module('modulos.gateway.api_gateway').APIGatewayManager(self.project_name)
            api_id = gateway_manager.create_api(cognito_info['user_pool_arn'])
            self.state['api_gateway'] = {
                'id': api_id,
                'url': gateway_manager.get_api_url(api_id)
            }

            # 9. Criar distribuição CloudFront
            cloudfront_manager = import_module('modulos.cloudfront.distribution_manager').CloudFrontManager(self.project_name)
            distribution_id = cloudfront_manager.create_distribution(
                f"{self.state['frontend_bucket']}.s3.amazonaws.com",
                f"{api_id}.execute-api.{os.environ['AWS_REGION']}.amazonaws.com"
            )
            self.state['cloudfront_distribution_id'] = distribution_id

            # Salvar estado
            self.save_state()
            logger.info("Infraestrutura criada com sucesso!")

        except Exception as e:
            logger.error(f"Erro ao criar infraestrutura: {str(e)}")
            raise

if __name__ == '__main__':
    builder = InfrastructureBuilder('file-management')
    builder.build_infrastructure()