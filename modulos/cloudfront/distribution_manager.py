import boto3
import logging
import time

class CloudFrontManager:
    def __init__(self, project_name):
        self.project_name = project_name
        self.cloudfront_client = boto3.client('cloudfront')
        self.logger = logging.getLogger(__name__)

    def create_distribution(self, s3_bucket_domain, api_gateway_domain):
        """
        Cria uma distribuição CloudFront para S3 e API Gateway
        """
        try:
            response = self.cloudfront_client.create_distribution(
                DistributionConfig={
                    'CallerReference': f"{self.project_name}-{int(time.time())}",
                    'Origins': {
                        'Quantity': 2,
                        'Items': [
                            {
                                'Id': 's3-origin',
                                'DomainName': s3_bucket_domain,
                                'S3OriginConfig': {
                                    'OriginAccessIdentity': ''
                                }
                            },
                            {
                                'Id': 'api-origin',
                                'DomainName': api_gateway_domain,
                                'CustomOriginConfig': {
                                    'HTTPPort': 80,
                                    'HTTPSPort': 443,
                                    'OriginProtocolPolicy': 'https-only'
                                }
                            }
                        ]
                    },
                    'DefaultCacheBehavior': {
                        'TargetOriginId': 's3-origin',
                        'ViewerProtocolPolicy': 'redirect-to-https',
                        'AllowedMethods': {
                            'Quantity': 2,
                            'Items': ['GET', 'HEAD'],
                            'CachedMethods': {
                                'Quantity': 2,
                                'Items': ['GET', 'HEAD']
                            }
                        },
                        'ForwardedValues': {
                            'QueryString': False,
                            'Cookies': {'Forward': 'none'}
                        },
                        'MinTTL': 0,
                        'DefaultTTL': 86400,
                        'MaxTTL': 31536000
                    },
                    'CacheBehaviors': {
                        'Quantity': 1,
                        'Items': [
                            {
                                'PathPattern': '/api/*',
                                'TargetOriginId': 'api-origin',
                                'ViewerProtocolPolicy': 'https-only',
                                'AllowedMethods': {
                                    'Quantity': 7,
                                    'Items': ['GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'OPTIONS', 'DELETE'],
                                    'CachedMethods': {
                                        'Quantity': 2,
                                        'Items': ['GET', 'HEAD']
                                    }
                                },
                                'ForwardedValues': {
                                    'QueryString': True,
                                    'Headers': {
                                        'Quantity': 3,
                                        'Items': ['Authorization', 'Accept', 'Content-Type']
                                    },
                                    'Cookies': {'Forward': 'all'}
                                },
                                'MinTTL': 0,
                                'DefaultTTL': 0,
                                'MaxTTL': 0
                            }
                        ]
                    },
                    'Enabled': True,
                    'Comment': f'Distribution for {self.project_name}',
                    'PriceClass': 'PriceClass_100'
                }
            )

            return response['Distribution']['Id']

        except Exception as e:
            self.logger.error(f"Erro ao criar distribuição CloudFront: {str(e)}")
            raise

    def delete_distribution(self, distribution_id):
        """
        Remove uma distribuição CloudFront
        """
        try:
            # Obter configuração atual
            response = self.cloudfront_client.get_distribution_config(
                Id=distribution_id
            )
            
            etag = response['ETag']
            config = response['DistributionConfig']
            
            # Desabilitar distribuição
            if config['Enabled']:
                config['Enabled'] = False
                self.cloudfront_client.update_distribution(
                    Id=distribution_id,
                    IfMatch=etag,
                    DistributionConfig=config
                )
                
                # Aguardar distribuição ser implantada
                while True:
                    dist = self.cloudfront_client.get_distribution(Id=distribution_id)
                    if dist['Distribution']['Status'] == 'Deployed':
                        break
                    time.sleep(30)
            
            # Deletar distribuição
            etag = self.cloudfront_client.get_distribution(Id=distribution_id)['ETag']
            self.cloudfront_client.delete_distribution(
                Id=distribution_id,
                IfMatch=etag
            )
            
            self.logger.info(f"Distribuição CloudFront {distribution_id} removida com sucesso")

        except Exception as e:
            self.logger.error(f"Erro ao remover distribuição CloudFront: {str(e)}")
            raise