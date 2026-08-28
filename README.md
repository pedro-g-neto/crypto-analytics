# Cripto Analytics: Data Lakehouse Multi-Ativos

![Python](https://img.shields.io/badge/Python-3.12-yellow)

## Sobre o Projeto
Este projeto implementa uma arquitetura **Data Lakehouse (Medallion)** completa e conteinerizada para extração, transformação, modelagem e visualização de indicadores financeiros do mercado de criptomoedas (BTC, ETH, SOL e ADA). 

O pipeline é totalmente automatizado e construído com foco em escalabilidade, governança de dados e qualidade das métricas finais disponibilizadas para tomada de decisão.

---

## Arquitetura de Dados

![Diagrama Arquitetural](/assets/diagrama_arquitetural.svg)

1. **Origem:** Extração via API da Binance utilizando `ccxt`.
2. **Camada Bronze:** Armazenamento bruto no formato `.json` dentro do Data Lake (MinIO).
3. **Camada Silver:** Transformação tabular, tratamento de fusos horários e conversão para o formato colunar `.parquet` via `Pandas`.
4. **Camada Gold:** Carga no **PostgreSQL** e modelagem via **dbt** (Data Build Tool), aplicando testes de integridade e cálculos de indicadores (Variação Percentual, Amplitude).
5. **Consumo:** Dashboards interativos via **Metabase** conectados exclusivamente à fonte de verdade (Camada Gold).

---

## Stack

* **Linguagem:** Python
* **Orquestração:** Apache Airflow
* **Data Lake:** MinIO (S3 Compatible)
* **Data Warehouse:** PostgreSQL
* **Modelagem & Qualidade:** dbt (Data Build Tool)
* **Business Intelligence:** Metabase
* **Infraestrutura:** Docker & Docker Compose

---

## Dashboard Executivo

![Dashboard](/assets/painel1.png)
![Dashboard](/assets/painel2.png)

O painel final permite ao usuário navegar entre os ativos disponíveis (Bitcoin, Ethereum, Solana e Cardano) para analisar tendências históricas de preço e variação percentual desde o ano de 2018.

---

## Como Executar o Projeto

### Pré-requisitos
* Git
* Docker Desktop e Docker Compose instalados.

### Passo a Passo

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/pedro-g-neto/crypto-analytics.git](https://github.com/pedro-g-neto/crypto-analytics.git)
   cd crypto-analytics```
2. **Configure as variáveis de ambiente:**
Crie um arquivo .env na raiz do projeto com as chaves necessárias (S3, Postgres, Airflow).
3. Inicie a infraestrutura:
    ```bash
    docker compose up -d
    ```
4. **Acesse as ferramentas:**

    Airflow (Orquestração): http://localhost:8080

    MinIO (Data Lake): http://localhost:9001

    Metabase (BI): http://localhost:3000

## Destaques Técnicos
- **Refatoração Multi-Ativo:** Pipeline agnóstico construído para processar e consolidar múltiplos ativos num único fluxo sem duplicação de código.

- **Idempotência:** Scripts desenvolvidos para garantir que reexecuções não gerem dados duplicados no banco.

- **Data Quality:** Testes do dbt barrando anomalias lógicas na chave primária composta (Símbolo + Data).
