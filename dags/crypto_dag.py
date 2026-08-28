from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Configurações padrão
default_args = {
    'owner': 'pedro',
    'depends_on_past': False,
    'start_date': datetime(2026, 8, 20),
    'retries': 1, 
    'retry_delay': timedelta(minutes=2),
}

with DAG(
    'pipeline_crypto_mvp',
    default_args=default_args,
    description='Orquestração do Pipeline de Criptomoedas',
    schedule_interval='0 3 * * *', # Cron expression -> Roda às 3h da manhã
    catchup=False,
    tags=['crypto', 'mvp'],
) as dag:

    # Entra na pasta do projeto e executa o script Python
    task_extracao = BashOperator(
        task_id='1_extracao_bronze',
        bash_command='cd /opt/project && python extracao_binance.py'
    )

    task_transformacao = BashOperator(
        task_id='2_transformacao_silver',
        bash_command='cd /opt/project && python transformacao_silver.py'
    )

    task_carga = BashOperator(
        task_id='3_carga_postgres',
        bash_command='cd /opt/project && python carga_postgres.py'
    )

    # Entra na pasta do projeto dbt e executa a modelagem
    task_modelagem = BashOperator(
        task_id='4_modelagem_dbt_gold',
        bash_command='cd /opt/project/meu_projeto_dbt && dbt run --profiles-dir . && dbt test --profiles-dir .'
    )

    # Definindo o fluxo de dependência
    task_extracao >> task_transformacao >> task_carga >> task_modelagem