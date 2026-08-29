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

simbolos = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'ADA/USDT']
timeframe = '1d'
NOME_BUCKET = 'bronze'

def extrair_carga_full():
    data_inicio = '2018-01-01T00:00:00Z'
    
    for symbol in simbolos:
        print(f'\n--- Iniciando a extração de {symbol} na Binance ---')
        since = exchange.parse8601(data_inicio)
        all = []

        try:
            while True:
                dados = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
                if not dados:
                    break
                all.extend(dados)
                ultimo_timestamp = dados[-1][0]
                since = ultimo_timestamp + 1

                print(f'[{symbol}] Registros extraídos: {len(all)}')
                time.sleep(exchange.rateLimit / 1000)

            print(f"Enviando dados de {symbol} para o MinIO...")
            agora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            nome_arquivo = f"binance_{symbol.replace('/','_')}/bronze_FULL_ohlcv_{agora}.json"
            
            dados_json = json.dumps(all)
            buffer = io.BytesIO(dados_json.encode('utf-8'))
            s3_client.upload_fileobj(buffer, NOME_BUCKET, nome_arquivo)
            print(f"Sucesso! {symbol} gravado no bucket {NOME_BUCKET} com o nome {nome_arquivo}")
            
        except Exception as e:
            print(f"Erro ao extrair dados de {symbol}: {e}")




def extrair_carga_incremental():
    for symbol in simbolos:
        print(f'Iniciando a extração incremental de {symbol} na Binance...')
        try:
            dados_brutos = exchange.fetch_ohlcv(symbol, timeframe, limit=5)

            agora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            nome_arquivo = f"binance_{symbol.replace('/','_')}/bronze_INC_ohlcv_{agora}.json"

            dados_json = json.dumps(dados_brutos)
            buffer = io.BytesIO(dados_json.encode('utf-8'))

            s3_client.upload_fileobj(buffer, NOME_BUCKET, nome_arquivo)
            print(f"Sucesso! Arquivo {nome_arquivo} enviado para o bucket {NOME_BUCKET}")
            
        except Exception as e:
            print(f"Erro ao extrair dados incrementais de {symbol}: {e}")

if __name__ == "__main__":
    extrair_carga_incremental()
