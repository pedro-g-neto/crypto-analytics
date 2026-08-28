WITH historico_precos AS (
    SELECT * 
    FROM {{ source('camada_silver', 'staging_cripto_ativos') }}
)

SELECT
    simbolo,
    DATE(data_pregao) AS data_referencia,
    preco_abertura,
    preco_fechamento,
    
    -- Variação Percentual Diária
    ROUND(CAST(((preco_fechamento - preco_abertura) / preco_abertura) * 100 AS NUMERIC), 2) AS variacao_percentual,
    
    -- Amplitude de Preço
    ROUND(CAST((preco_maximo - preco_minimo) AS NUMERIC), 2) AS amplitude_dolares,
    
    volume
FROM historico_precos
ORDER BY simbolo ASC, data_referencia DESC