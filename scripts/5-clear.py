import json
import logging
from importlib import import_module
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InfrastructureCleaner:
    def __init__(self):
        self.state = self.load_state()
        self.project_name = self.state.get('project_name', 'file-management')

    def load_state(self):
        """Carrega o arquivo de estado"""
        try:
            with open('infra.state', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("Arquivo de estado não encontrado")
            return {}

    def clean_infrastructure(self):
        """Remove todos os recursos na ordem reversa de criação"""
        try:
            # 1. Remover CloudFront
            if 'cloudfront_distribution_id' in self.state:
                logger.info("Removendo distribuição CloudFront...")
                cloudfront_manager = import_module('modulos.cloudfront.distribution_manager').CloudFrontManager(self.project_name)
                cloudfront_manager.delete_distribution(self.state['cloudfront_distribution_id'])

            # 2. Remover API Gateway
            if 'api_gateway' in self.state:
                logger.info("Removendo API Gateway...")
                gateway_manager = import_module('modulos.gateway.api_gateway').APIGatewayManager(self.project_name)
                gateway_manager.delete_api(self.state['api_gateway']['id'])

            # 3. Remover Lambdas e Role
            if 'lambda_role_arn' in self.state:
                logger.info("Removendo funções Lambda...")
                lambda_manager = import_module('modulos.lambdas.lambda_manager').LambdaManager(self.project_name)
                lambda_functions = [
                    'lambda_file_list',
                    'lambda_file_generate',
                    'lambda_file_delete',
                    'lambda_file_process'
                ]
                
                for func in lambda_functions:
                    lambda_manager.delete_function(func)
                
                # Remover role após remover todas as funções
                lambda_manager.delete_role(f"{self.project_name}-lambda-role")

            # 4. Remover Cognito User Pool
            if 'cognito' in self.state:
                logger.info("Removendo Cognito User Pool...")
                cognito_manager = import_module('modulos.cognito.auth_manager').CognitoManager(self.project_name)
                cognito_manager.delete_user_pool(self.state['cognito']['user_pool_id'])

            # 5. Remover SQS Queue
            if 'sqs' in self.state:
                logger.info("Removendo fila SQS...")
                sqs_manager = import_module('modulos.sqs.queue_manager').SQSManager(self.project_name)
                sqs_manager.delete_queue(self.state['sqs']['queue_url'])

            # 6. Remover SNS Topic
            if 'sns_topic_arn' in self.state:
                logger.info("Removendo tópico SNS...")
                sns_manager = import_module('modulos.sns.notification_manager').SNSManager(self.project_name)
                sns_manager.delete_topic(self.state['sns_topic_arn'])

            # 7. Remover ElastiCache
            if 'elasticache' in self.state:
                logger.info("Removendo cluster ElastiCache...")
                cache_manager = import_module('modulos.elasticache.cache_manager').ElastiCacheManager(self.project_name)
                cache_manager.delete_redis_cluster(self.state['elasticache']['cluster_id'])

            # 8. Remover buckets S3
            s3_manager = import_module('modulos.s3.s3_manager').S3Manager(self.project_name)
            if 'frontend_bucket' in self.state:
                logger.info("Removendo bucket frontend...")
                s3_manager.delete_bucket(self.state['frontend_bucket'])
            if 'data_bucket' in self.state:
                logger.info("Removendo bucket de dados...")
                s3_manager.delete_bucket(self.state['data_bucket'])

            # 9. Remover VPC (por último, pois outros serviços dependem dela)
            if 'vpc' in self.state:
                logger.info("Removendo VPC...")
                vpc_manager = import_module('modulos.vpc.vpc_manager').VPCManager(self.project_name)
                vpc_manager.delete_vpc(self.state['vpc']['vpc_id'])

            # Remover arquivo de estado
            logger.info("Removendo arquivo de estado...")
            if os.path.exists('infra.state'):
                os.remove('infra.state')

            # Limpar diretório todeploy
            logger.info("Limpando diretório de deploy...")
            deploy_dir = '../todeploy'
            if os.path.exists(deploy_dir):
                for file in os.listdir(deploy_dir):
                    os.remove(os.path.join(deploy_dir, file))

            logger.info("Limpeza completa realizada com sucesso!")

        except Exception as e:
            logger.error(f"Erro durante a limpeza: {str(e)}")
            raise

    def confirm_cleanup(self):
        """Solicita confirmação do usuário antes de prosseguir"""
        print("\nAVISO: Esta operação irá remover todos os recursos criados na AWS!")
        print("Esta ação é irreversível e todos os dados serão perdidos.")
        response = input("\nDigite 'CONFIRMAR' para prosseguir: ")
        return response.upper() == 'CONFIRMAR'

if __name__ == '__main__':
    cleaner = InfrastructureCleaner()
    if cleaner.confirm_cleanup():
        cleaner.clean_infrastructure()
    else:
        logger.info("Operação cancelada pelo usuário.")