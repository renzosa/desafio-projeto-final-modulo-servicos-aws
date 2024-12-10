import os
import json
import boto3
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Deployer:
    def __init__(self):
        self.state = self.load_state()
        self.s3_client = boto3.client('s3')
        self.lambda_client = boto3.client('lambda')

    def load_state(self):
        """Carrega o arquivo de estado"""
        with open('infra.state', 'r') as f:
            return json.load(f)

    def deploy_frontend(self):
        """Deploy do frontend para S3"""
        try:
            frontend_bucket = self.state['frontend_bucket']
            frontend_zip = '../todeploy/frontend.zip'
            
            # Extrair e fazer upload dos arquivos
            os.system(f'unzip -o {frontend_zip} -d /tmp/frontend')
            
            for root, dirs, files in os.walk('/tmp/frontend'):
                for file in files:
                    local_path = os.path.join(root, file)
                    relative_path = os.path.relpath(local_path, '/tmp/frontend')
                    
                    # Determinar content type
                    content_type = 'text/html' if file.endswith('.html') else \
                                 'application/javascript' if file.endswith('.js') else \
                                 'text/css' if file.endswith('.css') else \
                                 'application/octet-stream'
                    
                    self.s3_client.upload_file(
                        local_path, 
                        frontend_bucket,
                        relative_path,
                        ExtraArgs={'ContentType': content_type}
                    )
            
            logger.info(f"Frontend deployed to {frontend_bucket}")
            
        except Exception as e:
            logger.error(f"Erro no deploy do frontend: {str(e)}")
            raise

    def deploy_lambda(self, lambda_name):
        """Deploy de uma função Lambda"""
        try:
            with open(f'../todeploy/{lambda_name}.zip', 'rb') as f:
                zip_content = f.read()
            
            function_name = f"{self.state['project_name']}-{lambda_name}"
            
            try:
                # Atualizar código se a função já existe
                self.lambda_client.update_function_code(
                    FunctionName=function_name,
                    ZipFile=zip_content
                )
            except self.lambda_client.exceptions.ResourceNotFoundException:
                # Criar função se não existe
                self.lambda_client.create_function(
                    FunctionName=function_name,
                    Runtime='python3.9',
                    Role=self.state['lambda_role_arn'],
                    Handler='index.handler',
                    Code={'ZipFile': zip_content},
                    Environment={
                        'Variables': {
                            'REDIS_HOST': self.state['elasticache']['endpoint'],
                            'DATA_BUCKET_NAME': self.state['data_bucket'],
                            'SNS_TOPIC_ARN': self.state['sns_topic_arn']
                        }
                    }
                )
            
            logger.info(f"Lambda {lambda_name} deployed successfully")
            
        except Exception as e:
            logger.error(f"Erro no deploy da lambda {lambda_name}: {str(e)}")
            raise

    def deploy_all(self):
        """Executa todo o processo de deploy"""
        try:
            # Deploy do frontend
            self.deploy_frontend()
            
            # Deploy das lambdas
            lambda_functions = [
                'lambda_file_list',
                'lambda_file_generate',
                'lambda_file_delete',
                'lambda_file_process'
            ]
            
            for lambda_name in lambda_functions:
                self.deploy_lambda(lambda_name)
            
            logger.info("Deploy completed successfully!")
            
        except Exception as e:
            logger.error(f"Deploy failed: {str(e)}")
            raise

if __name__ == '__main__':
    deployer = Deployer()
    deployer.deploy_all()