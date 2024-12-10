import boto3
import logging

class VPCManager:
    def __init__(self, project_name):
        self.project_name = project_name
        self.ec2_client = boto3.client('ec2')
        self.logger = logging.getLogger(__name__)

    def get_existing_vpc(self):
        """
        Verifica se já existe uma VPC com o nome do projeto
        """
        try:
            response = self.ec2_client.describe_vpcs(
                Filters=[
                    {
                        'Name': 'tag:Name',
                        'Values': [f"{self.project_name}-vpc"]
                    }
                ]
            )
            
            if response['Vpcs']:
                vpc = response['Vpcs'][0]
                
                # Buscar sub-redes associadas
                subnets = self.ec2_client.describe_subnets(
                    Filters=[
                        {
                            'Name': 'vpc-id',
                            'Values': [vpc['VpcId']]
                        }
                    ]
                )
                
                public_subnet = None
                private_subnet = None
                
                for subnet in subnets['Subnets']:
                    for tag in subnet.get('Tags', []):
                        if tag['Key'] == 'Name':
                            if 'public' in tag['Value'].lower():
                                public_subnet = subnet
                            elif 'private' in tag['Value'].lower():
                                private_subnet = subnet
                
                return {
                    'vpc_id': vpc['VpcId'],
                    'public_subnet_id': public_subnet['SubnetId'] if public_subnet else None,
                    'private_subnet_id': private_subnet['SubnetId'] if private_subnet else None
                }
                
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar VPC existente: {str(e)}")
            raise

    def create_vpc(self):
        """
        Cria ou recupera uma VPC existente
        """
        try:
            # Primeiro verifica se já existe
            existing_vpc = self.get_existing_vpc()
            if existing_vpc:
                self.logger.info(f"VPC existente encontrada: {existing_vpc['vpc_id']}")
                return existing_vpc
            
            # Se não existe, cria uma nova
            vpc = self.ec2_client.create_vpc(
                CidrBlock='10.0.0.0/16',
                TagSpecifications=[{
                    'ResourceType': 'vpc',
                    'Tags': [{'Key': 'Name', 'Value': f"{self.project_name}-vpc"}]
                }]
            )
            vpc_id = vpc['Vpc']['VpcId']

            # Criar Internet Gateway
            igw = self.ec2_client.create_internet_gateway()
            igw_id = igw['InternetGateway']['InternetGatewayId']
            
            # Anexar Internet Gateway à VPC
            self.ec2_client.attach_internet_gateway(
                InternetGatewayId=igw_id,
                VpcId=vpc_id
            )

            # Criar sub-rede pública
            public_subnet = self.ec2_client.create_subnet(
                VpcId=vpc_id,
                CidrBlock='10.0.1.0/24',
                TagSpecifications=[{
                    'ResourceType': 'subnet',
                    'Tags': [{'Key': 'Name', 'Value': f"{self.project_name}-public-subnet"}]
                }]
            )

            # Criar sub-rede privada
            private_subnet = self.ec2_client.create_subnet(
                VpcId=vpc_id,
                CidrBlock='10.0.2.0/24',
                TagSpecifications=[{
                    'ResourceType': 'subnet',
                    'Tags': [{'Key': 'Name', 'Value': f"{self.project_name}-private-subnet"}]
                }]
            )

            return {
                'vpc_id': vpc_id,
                'public_subnet_id': public_subnet['Subnet']['SubnetId'],
                'private_subnet_id': private_subnet['Subnet']['SubnetId']
            }

        except Exception as e:
            self.logger.error(f"Erro ao criar/recuperar VPC: {str(e)}")
            raise

    def delete_vpc(self, vpc_id):
        """
        Remove uma VPC e todos seus recursos associados
        """
        try:
            # Verificar se a VPC pertence a este projeto
            vpcs = self.ec2_client.describe_vpcs(
                VpcIds=[vpc_id],
                Filters=[
                    {
                        'Name': 'tag:Name',
                        'Values': [f"{self.project_name}-vpc"]
                    }
                ]
            )
            
            if not vpcs['Vpcs']:
                self.logger.warning(f"VPC {vpc_id} não pertence a este projeto ou não existe")
                return

            # Desanexar e remover Internet Gateways
            igws = self.ec2_client.describe_internet_gateways(
                Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}]
            )
            for igw in igws['InternetGateways']:
                self.ec2_client.detach_internet_gateway(
                    InternetGatewayId=igw['InternetGatewayId'],
                    VpcId=vpc_id
                )
                self.ec2_client.delete_internet_gateway(
                    InternetGatewayId=igw['InternetGatewayId']
                )

            # Remover sub-redes
            subnets = self.ec2_client.describe_subnets(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
            )
            for subnet in subnets['Subnets']:
                self.ec2_client.delete_subnet(SubnetId=subnet['SubnetId'])

            # Remover VPC
            self.ec2_client.delete_vpc(VpcId=vpc_id)
            self.logger.info(f"VPC {vpc_id} removida com sucesso")

        except Exception as e:
            self.logger.error(f"Erro ao remover VPC: {str(e)}")
            raise