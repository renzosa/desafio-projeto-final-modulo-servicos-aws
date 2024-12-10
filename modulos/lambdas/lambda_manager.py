import boto3
import logging
import json
import os
import zipfile
import tempfile

class LambdaManager:
    def __init__(self, project_name):
        self.project_name = project_name
        self.lambda_client = boto3.client('lambda')
        self.iam_client = boto3.client('iam')
        self.logger = logging.getLogger(__name__)

    def create_lambda_role(self):
        """
        Cria uma role IAM para as funções Lambda
        """
        try:
            # Criar role
            role_name = f"{self.project_name}-lambda-role"
            
            assume_role_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "lambda.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
            
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(assume_role_policy)
            )
            
            role_arn = response['Role']['Arn']
            
            # Anexar políticas necessárias
            policies = [
                'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
                'arn:aws:iam::aws:policy/AmazonS3FullAccess',
                'arn:aws:iam::aws:policy/AmazonSNSFullAccess',
                'arn:aws:iam::aws:policy/AmazonSQSFullAccess'
            ]
            
            for policy in policies:
                self.iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy
                )
            
            return role_arn

        except Exception as e:
            self.logger.error(f"Erro ao criar role Lambda: {str(e)}")
            raise

    def create_function(self, function_name, handler_path, role_arn, environment=None):
        """
        Cria uma função Lambda
        """
        try:
            # Criar arquivo ZIP com o código
            with tempfile.NamedTemporaryFile(suffix='.zip') as tmp_file:
                with zipfile.ZipFile(tmp_file.name, 'w') as zip_file:
                    zip_file.write(handler_path, 'index.py')
                    
                    # Incluir requirements se existir
                    req_path = os.path.join(os.path.dirname(handler_path), 'requirements.txt')
                    if os.path.exists(req_path):
                        zip_file.write(req_path, 'requirements.txt')
                
                with open(tmp_file.name, 'rb') as zip_content:
                    response = self.lambda_client.create_function(
                        FunctionName=f"{self.project_name}-{function_name}",
                        Runtime='python3.9',
                        Role=role_arn,
                        Handler='index.handler',
                        Code={'ZipFile': zip_content.read()},
                        Timeout=30,
                        MemorySize=128,
                        Environment={'Variables': environment or {}},
                        Tags={'Project': self.project_name}
                    )
                    
                    return response['FunctionArn']

        except Exception as e:
            self.logger.error(f"Erro ao criar função Lambda: {str(e)}")
            raise

    def update_function_code(self, function_name, handler_path):
        """
        Atualiza o código de uma função Lambda existente
        """
        try:
            with tempfile.NamedTemporaryFile(suffix='.zip') as tmp_file:
                with zipfile.ZipFile(tmp_file.name, 'w') as zip_file:
                    zip_file.write(handler_path, 'index.py')
                
                with open(tmp_file.name, 'rb') as zip_content:
                    self.lambda_client.update_function_code(
                        FunctionName=f"{self.project_name}-{function_name}",
                        ZipFile=zip_content.read()
                    )

        except Exception as e:
            self.logger.error(f"Erro ao atualizar função Lambda: {str(e)}")
            raise

    def delete_function(self, function_name):
        """
        Remove uma função Lambda
        """
        try:
            self.lambda_client.delete_function(
                FunctionName=f"{self.project_name}-{function_name}"
            )
            self.logger.info(f"Função Lambda {function_name} removida com sucesso")

        except Exception as e:
            self.logger.error(f"Erro ao remover função Lambda: {str(e)}")
            raise

    def delete_role(self, role_name):
        """
        Remove uma role IAM e suas políticas
        """
        try:
            # Desanexar políticas
            attached_policies = self.iam_client.list_attached_role_policies(
                RoleName=role_name
            )
            
            for policy in attached_policies['AttachedPolicies']:
                self.iam_client.detach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy['PolicyArn']
                )
            
            # Remover role
            self.iam_client.delete_role(
                RoleName=role_name
            )
            
            self.logger.info(f"Role IAM {role_name} removida com sucesso")

        except Exception as e:
            self.logger.error(f"Erro ao remover role IAM: {str(e)}")
            raise