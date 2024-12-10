import boto3
import logging
from botocore.exceptions import ClientError

class CognitoManager:
    def __init__(self, project_name):
        self.project_name = project_name
        self.cognito_client = boto3.client('cognito-idp')
        self.logger = logging.getLogger(__name__)

    def create_user_pool(self, admin_email='admin@meusite.com', admin_password='teste123'):
        """
        Cria um User Pool no Cognito e adiciona um usuário admin
        """
        try:
            # Criar User Pool
            response = self.cognito_client.create_user_pool(
                PoolName=f"{self.project_name}-user-pool",
                Policies={
                    'PasswordPolicy': {
                        'MinimumLength': 8,
                        'RequireUppercase': True,
                        'RequireLowercase': True,
                        'RequireNumbers': True,
                        'RequireSymbols': True
                    }
                },
                AutoVerifiedAttributes=['email'],
                UsernameAttributes=['email'],
                AdminCreateUserConfig={
                    'AllowAdminCreateUserOnly': False
                },
                Schema=[
                    {
                        'Name': 'email',
                        'AttributeDataType': 'String',
                        'Required': True,
                        'Mutable': True
                    }
                ]
            )
            
            user_pool_id = response['UserPool']['Id']
            
            # Criar App Client
            client_response = self.cognito_client.create_user_pool_client(
                UserPoolId=user_pool_id,
                ClientName=f"{self.project_name}-client",
                GenerateSecret=False,
                ExplicitAuthFlows=[
                    'ALLOW_USER_SRP_AUTH',
                    'ALLOW_REFRESH_TOKEN_AUTH'
                ],
                SupportedIdentityProviders=['COGNITO']
            )

            # Criar usuário admin
            try:
                self.cognito_client.admin_create_user(
                    UserPoolId=user_pool_id,
                    Username=admin_email,
                    UserAttributes=[
                        {
                            'Name': 'email',
                            'Value': admin_email
                        },
                        {
                            'Name': 'email_verified',
                            'Value': 'true'
                        }
                    ],
                    TemporaryPassword=admin_password,
                    MessageAction='SUPPRESS'
                )

                # Definir senha permanente para o usuário admin
                self.cognito_client.admin_set_user_password(
                    UserPoolId=user_pool_id,
                    Username=admin_email,
                    Password=admin_password,
                    Permanent=True
                )

                self.logger.info(f"Usuário admin criado com sucesso: {admin_email}")

            except ClientError as e:
                self.logger.error(f"Erro ao criar usuário admin: {str(e)}")
                # Continuar mesmo se falhar a criação do usuário admin
            
            return {
                'user_pool_id': user_pool_id,
                'client_id': client_response['UserPoolClient']['ClientId'],
                'admin_user': {
                    'email': admin_email,
                    'password': admin_password
                }
            }

        except Exception as e:
            self.logger.error(f"Erro ao criar User Pool: {str(e)}")
            raise

    def delete_user_pool(self, user_pool_id):
        """
        Remove um User Pool e seus recursos
        """
        try:
            # Listar e remover App Clients
            clients = self.cognito_client.list_user_pool_clients(
                UserPoolId=user_pool_id
            )
            
            for client in clients['UserPoolClients']:
                self.cognito_client.delete_user_pool_client(
                    UserPoolId=user_pool_id,
                    ClientId=client['ClientId']
                )
            
            # Remover User Pool
            self.cognito_client.delete_user_pool(
                UserPoolId=user_pool_id
            )
            
            self.logger.info(f"User Pool {user_pool_id} removido com sucesso")

        except Exception as e:
            self.logger.error(f"Erro ao remover User Pool: {str(e)}")
            raise