"""
Coleta séries públicas do Banco Central (API SGS) e gera dados/panorama.csv

Séries usadas (todas mensais):
  - selic          (4189)  Selic acumulada no mês, anualizada (% a.a.)
  - ipca_12m       (13522) IPCA acumulado em 12 meses (%)
  - saldo_credito  (20539) Saldo da carteira de crédito total (R$ milhões)
  - inadimplencia  (21082) Inadimplência da carteira de crédito total (%)

Se alguma série der erro, confira o código em:
https://www3.bcb.gov.br/sgspub
"""
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests

SERIES = {
    "selic": 4189,
    "ipca_12m": 13522,
    "saldo_credito": 20539,
    "inadimplencia": 21082,
}

URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
DATA_INICIAL = "01/01/2016"
DATA_FINAL = date.today().strftime("%d/%m/%Y")
SAIDA = Path(__file__).parent / "dados" / "panorama.csv"


def buscar_serie(nome: str, codigo: int) -> pd.Series:
    """Baixa uma série do SGS e devolve como pandas.Series indexada pela data."""
    params = {"formato": "json", "dataInicial": DATA_INICIAL, "dataFinal": DATA_FINAL}

    for tentativa in range(1, 4):
        try:
            resposta = requests.get(URL.format(codigo=codigo), params=params, timeout=30)
            resposta.raise_for_status()
            dados = resposta.json()
            break
        except (requests.RequestException, ValueError) as erro:
            print(f"  [{nome}] tentativa {tentativa} falhou: {erro}")
            time.sleep(2 * tentativa)
    else:
        raise RuntimeError(f"Não consegui baixar a série {nome} ({codigo}).")

    if not dados:
        raise RuntimeError(f"A série {nome} ({codigo}) veio vazia.")

    df = pd.DataFrame(dados)
    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    print(f"  [{nome}] {len(df)} registros ({df['data'].min():%m/%Y} a {df['data'].max():%m/%Y})")
    return df.set_index("data")["valor"].rename(nome)


def main() -> None:
    print("Baixando séries do Banco Central...")
    series = [buscar_serie(nome, codigo) for nome, codigo in SERIES.items()]

    # Junta tudo numa tabela só: uma linha por mês, uma coluna por indicador
    panorama = pd.concat(series, axis=1).sort_index()
    panorama = panorama.dropna(how="all").round(2)
    panorama.index.name = "data"

    SAIDA.parent.mkdir(exist_ok=True)
    panorama.to_csv(SAIDA, date_format="%Y-%m-%d")
    print(f"\nPronto! {len(panorama)} meses salvos em {SAIDA}")
    print(panorama.tail())


if __name__ == "__main__":
    main()
