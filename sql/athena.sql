-- =====================================================================
-- Panorama de juros e crédito no Brasil - consultas no Amazon Athena
-- Antes: suba dados/panorama.csv para s3://SEU-BUCKET/panorama/
--        (a pasta deve conter SÓ esse arquivo)
-- Troque SEU-BUCKET pelo nome do seu bucket.
-- =====================================================================

-- 1) Banco e tabela -----------------------------------------------------
CREATE DATABASE IF NOT EXISTS economia;

CREATE EXTERNAL TABLE IF NOT EXISTS economia.panorama (
    data           DATE,
    selic          DOUBLE,
    ipca_12m       DOUBLE,
    saldo_credito  DOUBLE,
    inadimplencia  DOUBLE
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
LOCATION 's3://SEU-BUCKET/panorama/'
TBLPROPERTIES ('skip.header.line.count' = '1');

-- Teste rápido
SELECT * FROM economia.panorama ORDER BY data DESC LIMIT 12;


-- 2) Média anual de juros, inflação e inadimplência ---------------------
SELECT
    year(data)                    AS ano,
    round(avg(selic), 2)          AS selic_media,
    round(avg(ipca_12m), 2)       AS ipca_12m_medio,
    round(avg(inadimplencia), 2)  AS inadimplencia_media
FROM economia.panorama
GROUP BY year(data)
ORDER BY ano;


-- 3) Juro real: Selic descontada da inflação (aproximação) --------------
--    Mostra em quais períodos o dinheiro "rendeu de verdade"
SELECT
    data,
    selic,
    ipca_12m,
    round(selic - ipca_12m, 2) AS juro_real_aprox
FROM economia.panorama
WHERE selic IS NOT NULL AND ipca_12m IS NOT NULL
ORDER BY juro_real_aprox DESC
LIMIT 10;


-- 4) Crescimento do crédito em 12 meses (função de janela LAG) ----------
SELECT
    data,
    saldo_credito,
    round(
        (saldo_credito / LAG(saldo_credito, 12) OVER (ORDER BY data) - 1) * 100
    , 2) AS credito_var_12m
FROM economia.panorama
ORDER BY data DESC
LIMIT 24;


-- 5) Classificação dos meses por patamar de juros (CASE) ----------------
WITH faixas AS (
    SELECT
        data,
        inadimplencia,
        CASE
            WHEN selic < 7  THEN '1. Juros baixos (< 7%)'
            WHEN selic < 11 THEN '2. Juros médios (7% a 11%)'
            ELSE                 '3. Juros altos (>= 11%)'
        END AS patamar_juros
    FROM economia.panorama
    WHERE selic IS NOT NULL
)
SELECT
    patamar_juros,
    count(*)                      AS meses,
    round(avg(inadimplencia), 2)  AS inadimplencia_media
FROM faixas
GROUP BY patamar_juros
ORDER BY patamar_juros;


-- 6) Correlação entre Selic e inadimplência -----------------------------
SELECT round(corr(selic, inadimplencia), 2) AS correlacao_selic_inadimplencia
FROM economia.panorama;
