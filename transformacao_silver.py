import os
import json
import io
import pandas as pd
import boto3
from dotenv import load_dotenv
from datetime import datetime
import pyarrow

load_dotenv()
# Configuração do cliente S3 para o MinIO
s3_client = boto3.client(
    's3',
    endpoint_url=os.getenv('MINIO_ENDPOINT'),
    aws_access_key_id=os.getenv('MINIO_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('MINIO_SECRET_KEY')
)

BUCKET_ORIGEM = 'bronze'
BUCKET_DESTINO = 'silver'
PREFIXO_BRONZE = 'binance_BTC_USDT/'
PREFIXO_SILVER = 'binance_BTC_USDT/'

def arquivo_recente(bucket, prefixo):
    #Busca o arquivo mais recente no bucket de origem
    resposta = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefixo)
    if 'Contents' not in resposta:
        print(f'Nenhum arquivo encontrado no bucket {bucket} com o prefixo {prefixo}.')
        return None
    # Ordena os arquivos pelo timestamp de modificação e retorna o mais recente
    arquivos_ordenados = sorted(resposta['Contents'], key=lambda obj:obj['LastModified'])
    return arquivos_ordenados[-1]['Key']

def bronze_tosilver():
    print("Iniciando a transformação de dados da camada Bronze para Silver...")
    chave_bronze = arquivo_recente(BUCKET_ORIGEM, PREFIXO_BRONZE)
    if not chave_bronze:
        print("Nenhum arquivo encontrado para transformação.")
        return
    print(f'Lendo dados do arquivo mais recente: {chave_bronze}')

    # Leitura em memória pegando do MinIO
    objeto_s3 = s3_client.get_object(Bucket=BUCKET_ORIGEM, Key=chave_bronze)
    dados_brutos = json.loads(objeto_s3['Body'].read().decode('utf-8'))

    #Limpeza e estruturação tabular
    df = pd.DataFrame(dados_brutos, columns=['timestamp_ms', 'preco_abertura', 'preco_maximo', 'preco_minimo', 'preco_fechamento', 'volume'])

    # Conversão do timestamp para datetime
    df['data_pregao'] = pd.to_datetime(df['timestamp_ms'], unit='ms')

    # Metadados
    df['data_processamento_silver'] = pd.Timestamp.now()

    colunas_ordenadas = ['data_pregao', 'preco_abertura', 'preco_maximo', 'preco_minimo', 'preco_fechamento', 'volume', 'data_processamento_silver']
    df = df[colunas_ordenadas]

    print("Amostra de dados limpos:")
    print(df.head())

    buffer_parquet = io.BytesIO()
    df.to_parquet(buffer_parquet, engine='pyarrow', index=False)
    buffer_parquet.seek(0) # o ponteiro aponta para o início do arquivo em buffer antes do upload

    agora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_arquivo = f"{PREFIXO_SILVER}silver_ohlcv_{agora}.parquet"

    s3_client.upload_fileobj(
        buffer_parquet,
        BUCKET_DESTINO,
        nome_arquivo
    )

    print(f"Transformação concluída com sucesso! Dados gravados no bucket '{BUCKET_DESTINO}': {nome_arquivo}")

if __name__ == "__main__":
    bronze_tosilver()