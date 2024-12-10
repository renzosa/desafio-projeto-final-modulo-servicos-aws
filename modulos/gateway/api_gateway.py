import boto3
import logging
import json

class APIGatewayManager:
    def __init__(self, project_name):
        self.project_name = project_name
        self.api_client = boto3.client('apigateway')
        self.logger = logging.getLogger(__name__)

    def create_api(self, cognito_user_pool_arn):
        """
        Cria uma API REST com autenticação Cognito
        """
        try:
            # Criar API
            api = self.api_client.create_rest_api(
                name=f"{self.project_name}-api",
                description=f"API for {self.project_name}",
                endpointConfiguration={'types': ['REGIONAL']},
                minimumCompressionSize=1024
            )
            
            api_id = api['id']
            
            # Obter ID do resource raiz
            resources = self.api_client.get_resources(restApiId=api_id)
            root_id = [resource for resource in resources['items'] if resource['path'] == '/'][0]['id']
            
            # Criar authorizer do Cognito
            authorizer = self.api_client.create_authorizer(
                restApiId=api_id,
                name='CognitoAuthorizer',
                type='COGNITO_USER_POOLS',
                providerARNs=[cognito_user_pool_arn],
                identitySource='method.request.header.Authorization'
            )
            
            # Criar recursos e métodos
            self._create_files_endpoints(api_id, root_id, authorizer['id'])
            
            # Criar deployment
            self.api_client.create_deployment(
                restApiId=api_id,
                stageName='prod'
            )
            
            return api_id

        except Exception as e:
            self.logger.error(f"Erro ao criar API Gateway: {str(e)}")
            raise

    def _create_files_endpoints(self, api_id, parent_id, authorizer_id):
        """
        Cria endpoints relacionados a arquivos
        """
        # Criar resource /files
        files_resource = self.api_client.create_resource(
            restApiId=api_id,
            parentId=parent_id,
            pathPart='files'
        )
        
        # GET /files - Listar arquivos
        self.api_client.put_method(
            restApiId=api_id,
            resourceId=files_resource['id'],
            httpMethod='GET',
            authorizationType='COGNITO_USER_POOLS',
            authorizerId=authorizer_id
        )
        
        self.api_client.put_integration(
            restApiId=api_id,
            resourceId=files_resource['id'],
            httpMethod='GET',
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=f"arn:aws:apigateway:{self.api_client.meta.region_name}:lambda:path/2015-03-31/functions/arn:aws:lambda:{self.api_client.meta.region_name}:{self._get_account_id()}:function:{self.project_name}-file-list/invocations"
        )
        
        # POST /files/generate - Gerar novo arquivo
        generate_resource = self.api_client.create_resource(
            restApiId=api_id,
            parentId=files_resource['id'],
            pathPart='generate'
        )
        
        self.api_client.put_method(
            restApiId=api_id,
            resourceId=generate_resource['id'],
            httpMethod='POST',
            authorizationType='COGNITO_USER_POOLS',
            authorizerId=authorizer_id
        )
        
        self.api_client.put_integration(
            restApiId=api_id,
            resourceId=generate_resource['id'],
            httpMethod='POST',
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=f"arn:aws:apigateway:{self.api_client.meta.region_name}:lambda:path/2015-03-31/functions/arn:aws:lambda:{self.api_client.meta.region_name}:{self._get_account_id()}:function:{self.project_name}-file-generate/invocations"
        )
        
        # DELETE /files/{filename} - Excluir arquivo
        file_resource = self.api_client.create_resource(
            restApiId=api_id,
            parentId=files_resource['id'],
            pathPart='{filename}'
        )
        
        self.api_client.put_method(
            restApiId=api_id,
            resourceId=file_resource['id'],
            httpMethod='DELETE',
            authorizationType='COGNITO_USER_POOLS',
            authorizerId=authorizer_id,
            requestParameters={
                'method.request.path.filename': True
            }
        )
        
        self.api_client.put_integration(
            restApiId=api_id,
            resourceId=file_resource['id'],
            httpMethod='DELETE',
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=f"arn:aws:apigateway:{self.api_client.meta.region_name}:lambda:path/2015-03-31/functions/arn:aws:lambda:{self.api_client.meta.region_name}:{self._get_account_id()}:function:{self.project_name}-file-delete/invocations"
        )

    def _get_account_id(self):
        """
        Obtém ID da conta AWS atual
        """
        return boto3.client('sts').get_caller_identity()['Account']

    def delete_api(self, api_id):
        """
        Remove uma API e todos seus recursos
        """
        try:
            self.api_client.delete_rest_api(
                restApiId=api_id
            )
            self.logger.info(f"API Gateway {api_id} removida com sucesso")

        except Exception as e:
            self.logger.error(f"Erro ao remover API Gateway: {str(e)}")
            raise

    def get_api_url(self, api_id):
        """
        Retorna URL base da API
        """
        return f"https://{api_id}.execute-api.{self.api_client.meta.region_name}.amazonaws.com/prod"