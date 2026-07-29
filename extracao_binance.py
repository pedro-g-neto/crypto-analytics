import pandas as pd
import ccxt
from datetime import datetime
import json
import os
import io
import boto3
from dotenv import load_dotenv
import time

load_dotenv()
# Configuração do cliente S3 para o MinIO
s3_client = boto3.client(
    's3',
    endpoint_url=os.getenv('MINIO_ENDPOINT'),
    aws_access_key_id=os.getenv('MINIO_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('MINIO_SECRET_KEY')
)
# Configuração da origem dos dados (Binance)
exchange = ccxt.binance({
    'ratelimit': 1200,
    'enableRateLimit': True
})

symbol = 'BTC/USDT'
timeframe = '1d'
NOME_BUCKET = 'bronze'

def extrair_carga_full():
    print(f'Iniciando a extração de {symbol} na Binance...')
    data_inicio = '2020-01-01T00:00:00Z'
    since = exchange.parse8601(data_inicio)
    all = []

    try:
        while True:
            dados = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)

            if not dados:
                break

            all.extend(dados)
            ultimo_timestamp = dados[-1][0]
            since = ultimo_timestamp + 1  # Incrementa o timestamp para a próxima chamada

            print(f'Extração de lote concluída. Total de registros extraídos até agora: {len(all)}')

            time.sleep(exchange.rateLimit / 1000)  # Respeita o limite de taxa da API
        print("\nExtração concluída com sucesso. Enviando dados para o MinIO...")

        agora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        nome_arquivo = f"binance_{symbol.replace('/','_')}/bronze_FULL_ohlcv_{agora}.json"
# Converte os dados para JSON e envia para o MinIO
        dados_json = json.dumps(all)
        buffer = io.BytesIO(dados_json.encode('utf-8'))

        s3_client.upload_fileobj(buffer, NOME_BUCKET, nome_arquivo)

        print(f"Sucesso! Histórico gravado no bucket {NOME_BUCKET} com o nome {nome_arquivo}")
    except Exception as e:
        print(f"Erro ao extrair dados: {e}")




def extrair_carga_incremental():
    print(f'Iniciando a extração de {symbol} na Binance...')
    try:
        dados_brutos = exchange.fetch_ohlcv(symbol, timeframe, limit=5)
        print("\nExtração concluída com sucesso. Enviando dados para o MinIO...")

        agora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        nome_arquivo = f"binance_{symbol.replace('/','_')}_{agora}.json"

        dados_json = json.dumps(dados_brutos)
        buffer = io.BytesIO(dados_json.encode('utf-8'))

        s3_client.upload_fileobj(buffer, NOME_BUCKET, nome_arquivo)
        print(f"Arquivo {nome_arquivo} enviado para o bucket {NOME_BUCKET}")
    except Exception as e:
        print(f"Erro ao extrair dados: {e}")

if __name__ == "__main__":
    extrair_carga_full()
