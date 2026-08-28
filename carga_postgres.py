import os
import io 
import pandas as pd
import boto3
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

s3_client = boto3.client(
    's3',
    endpoint_url=os.getenv('MINIO_ENDPOINT'),
    aws_access_key_id=os.getenv('MINIO_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('MINIO_SECRET_KEY')
)

BUCKET_SILVER = 'silver'
PREFIXO_SILVER = 'cripto_consolidadas/'

def obter_arquivo_mais_recente(bucket, prefixo):
    resposta = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefixo)
    if 'Contents' not in resposta:
        return None
    arquivos_ordenados = sorted(resposta['Contents'], key=lambda obj: obj['LastModified'])
    return arquivos_ordenados[-1]['Key']

def carregar_para_postgres():
    print("Iniciando a carga de dados da camada Silver para o PostgreSQL...")
    chave_silver = obter_arquivo_mais_recente(BUCKET_SILVER, PREFIXO_SILVER)
    if not chave_silver:
        print("Nenhum arquivo encontrado para carga.")
        return
    print(f'Lendo dados do arquivo mais recente: {chave_silver}')
    # Leitura em memória (buffer) pegando do MinIO
    objeto_s3 = s3_client.get_object(Bucket=BUCKET_SILVER, Key=chave_silver)
    buffer_parquet = io.BytesIO(objeto_s3['Body'].read())

    df_silver = pd.read_parquet(buffer_parquet)
    print("Dados carregados na memória. Total de registros:", len(df_silver))

    user = os.getenv('POSTGRES_USER')
    password = os.getenv('POSTGRES_PASSWORD')
    host = os.getenv('POSTGRES_HOST')
    port = os.getenv('POSTGRES_PORT')
    database = os.getenv('POSTGRES_DB')

    url_banco = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    engine = create_engine(url_banco)

    nome_tabela = 'staging_cripto_ativos'
    print(f'Carregando dados para a tabela {nome_tabela}...')
    
    try:
        df_silver.to_sql(nome_tabela, engine, if_exists='replace', index=False)
        print(f"Sucesso! Dados carregados.")
    except Exception as e:
        print(f"Erro ao carregar dados para o PostgreSQL: {e}")

if __name__ == "__main__":
    carregar_para_postgres()