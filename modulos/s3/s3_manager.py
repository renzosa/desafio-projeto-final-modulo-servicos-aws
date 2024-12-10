import boto3
import json
import logging
from botocore.exceptions import ClientError

class S3Manager:
    def __init__(self, project_name):
        self.project_name = project_name
        self.s3_client = boto3.client('s3')
        self.logger = logging.getLogger(__name__)
        self.region = self.s3_client.meta.region_name

    def get_existing_bucket(self, bucket_type):
        """
        Verifica se já existe um bucket com o nome do projeto
        """
        try:
            bucket_name = f"{self.project_name}-{bucket_type}"
            try:
                self.s3_client.head_bucket(Bucket=bucket_name)
                self.logger.info(f"Bucket {bucket_name} encontrado")
                return bucket_name
            except ClientError as e:
                error_code = int(e.response['Error']['Code'])
                if error_code == 404:  # Bucket não existe
                    return None
                raise
        except Exception as e:
            self.logger.error(f"Erro ao verificar bucket existente: {str(e)}")
            raise

    def create_bucket(self, bucket_type):
        """
        Cria ou recupera um bucket S3
        """
        try:
            # Verificar se já existe
            existing_bucket = self.get_existing_bucket(bucket_type)
            if existing_bucket:
                return existing_bucket

            bucket_name = f"{self.project_name}-{bucket_type}"
            
            # Criar bucket com configuração específica para região
            if self.region == 'us-east-1':
                self.s3_client.create_bucket(
                    Bucket=bucket_name
                )
            else:
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={
                        'LocationConstraint': self.region
                    }
                )

            # Configurações específicas para cada tipo
            if bucket_type == 'frontend':
                # Desabilitar bloqueio de acesso público
                self.s3_client.put_public_access_block(
                    Bucket=bucket_name,
                    PublicAccessBlockConfiguration={
                        'BlockPublicAcls': False,
                        'IgnorePublicAcls': False,
                        'BlockPublicPolicy': False,
                        'RestrictPublicBuckets': False
                    }
                )

                # Aguardar propagação das configurações
                import time
                time.sleep(5)

                # Configurar website
                self.s3_client.put_bucket_website(
                    Bucket=bucket_name,
                    WebsiteConfiguration={
                        'IndexDocument': {'Suffix': 'index.html'},
                        'ErrorDocument': {'Key': 'index.html'}
                    }
                )

                # Configurar política de acesso público
                bucket_policy = {
                    'Version': '2012-10-17',
                    'Statement': [{
                        'Sid': 'PublicReadGetObject',
                        'Effect': 'Allow',
                        'Principal': '*',
                        'Action': 's3:GetObject',
                        'Resource': f'arn:aws:s3:::{bucket_name}/*'
                    }]
                }
                
                self.s3_client.put_bucket_policy(
                    Bucket=bucket_name,
                    Policy=json.dumps(bucket_policy)
                )

            elif bucket_type == 'data':
                # Habilitar versionamento
                self.s3_client.put_bucket_versioning(
                    Bucket=bucket_name,
                    VersioningConfiguration={
                        'Status': 'Enabled'
                    }
                )

            self.logger.info(f"Bucket {bucket_name} criado com sucesso")
            return bucket_name

        except Exception as e:
            self.logger.error(f"Erro ao criar/recuperar bucket: {str(e)}")
            raise

    def delete_bucket(self, bucket_name):
        """
        Remove um bucket e todo seu conteúdo
        """
        try:
            if not bucket_name.startswith(f"{self.project_name}-"):
                self.logger.warning(f"Bucket {bucket_name} não pertence a este projeto")
                return

            # Remover objetos
            try:
                objects = self.s3_client.list_objects_v2(Bucket=bucket_name)
                if 'Contents' in objects:
                    for obj in objects['Contents']:
                        self.s3_client.delete_object(
                            Bucket=bucket_name,
                            Key=obj['Key']
                        )
            except ClientError as e:
                if e.response['Error']['Code'] != 'NoSuchBucket':
                    raise

            # Remover bucket
            self.s3_client.delete_bucket(Bucket=bucket_name)
            self.logger.info(f"Bucket {bucket_name} removido com sucesso")

        except Exception as e:
            self.logger.error(f"Erro ao remover bucket: {str(e)}")
            raise