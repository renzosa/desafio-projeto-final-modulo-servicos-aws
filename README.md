# Projeto para Configuração de Aplicação de Serviços AWS Simulado


## Descrição do cenário
A Ada Contabilidade enfrenta um desafio operacional diário: os contadores precisam enviar arquivos manualmente para armazenamento e, em seguida, registrar no banco de dados a quantidade de linhas contidas nesses arquivos. Esse processo manual é ineficiente e propenso a erros.

---

Crie uma solução que automatize a arquitetura em todo o seu fluxo, se baseando em práticas DevOps para simplificar o fluxo de trabalho e garantir a confiabilidade do processo.

### Requisitos:

- Código com a aplicação que envia os arquivos para o s3 (Linguagem de sua preferência)
- Código da arquitetura usando boto3 ou terraform para subir os recursos;
- Os códigos precisam estar no GitHub, usando as boas práticas já estudadas;
- A aplicação precisa gerar um arquivo de texto com um número aleatório de linhas;
- Esse arquivo precisa ser enviado para um s3 de forma automatizada;
- Usar S3, SNS, SQS, Lambda e Elasticache obrigatoriamente;
- No banco de dados é obrigatório que seja gravado o nome do arquivo e o número de linhas contido;
- Gravar um vídeo de até 5 minutos explicando a arquitetura e justificando suas escolhas.

### Opcional:

Como você implementaria o monitoramento desse fluxo? Quais são os pontos criticos? Registre sua resposta na documentação do seu repositório no GitHub em uma seção de “Estratégia de monitoramento”.