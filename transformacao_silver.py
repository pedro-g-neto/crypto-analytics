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

simbolos = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'ADA/USDT']
BUCKET_ORIGEM = 'bronze'
BUCKET_DESTINO = 'silver'
PREFIXO_SILVER_CONSOLIDADO = 'cripto_consolidadas/'

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
    print("Iniciando a transformação da camada Bronze para Silver...")
    dataframes = []
    
    for symbol in simbolos:
        prefixo_bronze_dinamico = f"binance_{symbol.replace('/','_')}/"
        chave_bronze = arquivo_recente(BUCKET_ORIGEM, prefixo_bronze_dinamico)
        
        if not chave_bronze:
            print(f"Nenhum arquivo encontrado para {symbol}. Pulando...")
            continue
            
        print(f'Lendo arquivo mais recente de {symbol}...')
        objeto_s3 = s3_client.get_object(Bucket=BUCKET_ORIGEM, Key=chave_bronze)
        dados_brutos = json.loads(objeto_s3['Body'].read().decode('utf-8'))

        df = pd.DataFrame(dados_brutos, columns=['timestamp_ms', 'preco_abertura', 'preco_maximo', 'preco_minimo', 'preco_fechamento', 'volume'])
        
        df['simbolo'] = symbol
        
        df['data_pregao'] = pd.to_datetime(df['timestamp_ms'], unit='ms')
        df['data_pregao'] = df['data_pregao'].dt.tz_localize('UTC').dt.tz_convert('America/Recife').dt.tz_localize(None)
        df['data_processamento_silver'] = pd.Timestamp.now()

        colunas_ordenadas = ['simbolo', 'data_pregao', 'preco_abertura', 'preco_maximo', 'preco_minimo', 'preco_fechamento', 'volume', 'data_processamento_silver']
        df = df[colunas_ordenadas]
        
        dataframes.append(df)

    if not dataframes:
        print("Nenhum dado processado.")
        return

    df_silver_consolidado = pd.concat(dataframes, ignore_index=True)
    print("Amostra do DataFrame Consolidado:")
    print(df_silver_consolidado.head())

    buffer_parquet = io.BytesIO()
    df_silver_consolidado.to_parquet(buffer_parquet, engine='pyarrow', index=False)
    buffer_parquet.seek(0)

    agora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_arquivo = f"{PREFIXO_SILVER_CONSOLIDADO}silver_ohlcv_todas_{agora}.parquet"

    s3_client.upload_fileobj(buffer_parquet, BUCKET_DESTINO, nome_arquivo)
    print(f"Sucesso! DataFrame consolidado gravado como: {nome_arquivo}")

if __name__ == "__main__":
    bronze_tosilver()