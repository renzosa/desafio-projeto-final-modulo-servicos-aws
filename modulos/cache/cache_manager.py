import boto3
import logging
import time

class ElastiCacheManager:
    def __init__(self, project_name):
        self.project_name = project_name
        self.elasticache_client = boto3.client('elasticache')
        self.logger = logging.getLogger(__name__)

    def create_redis_cluster(self, vpc_id, subnet_ids):
        """
        Cria um cluster Redis no ElastiCache
        """
        try:
            # Criar grupo de sub-rede
            subnet_group_name = f"{self.project_name}-redis-subnet-group"
            
            try:
                self.elasticache_client.create_cache_subnet_group(
                    CacheSubnetGroupName=subnet_group_name,
                    CacheSubnetGroupDescription=f"Subnet group for {self.project_name} Redis cluster",
                    SubnetIds=subnet_ids
                )
            except self.elasticache_client.exceptions.CacheSubnetGroupAlreadyExistsFault:
                self.logger.info(f"Subnet group {subnet_group_name} já existe")

            # Criar cluster Redis
            cluster_id = f"{self.project_name}-redis"
            
            try:
                response = self.elasticache_client.create_cache_cluster(
                    CacheClusterId=cluster_id,
                    Engine='redis',
                    CacheNodeType='cache.t3.micro',
                    NumCacheNodes=1,
                    CacheSubnetGroupName=subnet_group_name,
                    VpcSecurityGroupIds=[self.create_security_group(vpc_id)],
                    Tags=[
                        {
                            'Key': 'Project',
                            'Value': self.project_name
                        }
                    ]
                )

                # Aguardar cluster ficar disponível
                while True:
                    cluster_info = self.elasticache_client.describe_cache_clusters(
                        CacheClusterId=cluster_id
                    )['CacheClusters'][0]
                    
                    if cluster_info['CacheClusterStatus'] == 'available':
                        break
                    
                    time.sleep(30)

                return {
                    'cluster_id': cluster_id,
                    'endpoint': cluster_info['CacheNodes'][0]['Endpoint']['Address'],
                    'port': cluster_info['CacheNodes'][0]['Endpoint']['Port']
                }

            except self.elasticache_client.exceptions.CacheClusterAlreadyExistsFault:
                self.logger.info(f"Cluster {cluster_id} já existe")
                cluster_info = self.elasticache_client.describe_cache_clusters(
                    CacheClusterId=cluster_id
                )['CacheClusters'][0]
                
                return {
                    'cluster_id': cluster_id,
                    'endpoint': cluster_info['CacheNodes'][0]['Endpoint']['Address'],
                    'port': cluster_info['CacheNodes'][0]['Endpoint']['Port']
                }

        except Exception as e:
            self.logger.error(f"Erro ao criar cluster Redis: {str(e)}")
            raise

    def create_security_group(self, vpc_id):
        """
        Cria grupo de segurança para o Redis
        """
        ec2_client = boto3.client('ec2')
        
        try:
            response = ec2_client.create_security_group(
                GroupName=f"{self.project_name}-redis-sg",
                Description=f"Security group for {self.project_name} Redis cluster",
                VpcId=vpc_id
            )
            
            security_group_id = response['GroupId']
            
            # Adicionar regra de entrada para Redis
            ec2_client.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 6379,
                        'ToPort': 6379,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    }
                ]
            )
            
            return security_group_id
            
        except ec2_client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'InvalidGroup.Duplicate':
                # Se o grupo já existe, retornar o ID do grupo existente
                response = ec2_client.describe_security_groups(
                    Filters=[
                        {
                            'Name': 'group-name',
                            'Values': [f"{self.project_name}-redis-sg"]
                        }
                    ]
                )
                return response['SecurityGroups'][0]['GroupId']
            else:
                raise

    def delete_redis_cluster(self, cluster_id):
        """
        Remove um cluster Redis e recursos associados
        """
        try:
            # Remover cluster
            self.elasticache_client.delete_cache_cluster(
                CacheClusterId=cluster_id
            )
            
            # Aguardar remoção do cluster
            while True:
                try:
                    self.elasticache_client.describe_cache_clusters(
                        CacheClusterId=cluster_id
                    )
                    time.sleep(30)
                except self.elasticache_client.exceptions.CacheClusterNotFoundFault:
                    break

            # Remover grupo de sub-rede
            try:
                self.elasticache_client.delete_cache_subnet_group(
                    CacheSubnetGroupName=f"{self.project_name}-redis-subnet-group"
                )
            except:
                pass

            self.logger.info(f"Cluster Redis {cluster_id} removido com sucesso")

        except Exception as e:
            self.logger.error(f"Erro ao remover cluster Redis: {str(e)}")
            raise