"""
Lê dados/panorama.csv, gera os gráficos em graficos/ e imprime um resumo
com os números que viram as conclusões do README.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

PASTA = Path(__file__).parent
ENTRADA = PASTA / "dados" / "panorama.csv"
GRAFICOS = PASTA / "graficos"

AZUL = "#1f4e79"
LARANJA = "#ec7000"


def carregar() -> pd.DataFrame:
    df = pd.read_csv(ENTRADA, parse_dates=["data"]).set_index("data")
    # Crescimento do crédito em relação ao mesmo mês do ano anterior (%)
    df["credito_var_12m"] = df["saldo_credito"].pct_change(12, fill_method=None) * 100
    return df


def grafico_duas_linhas(df, col_esq, rot_esq, col_dir, rot_dir, titulo, arquivo):
    fig, ax1 = plt.subplots(figsize=(11, 5))
    ax1.plot(df.index, df[col_esq], color=AZUL, linewidth=2, label=rot_esq)
    ax1.set_ylabel(rot_esq, color=AZUL)
    ax1.tick_params(axis="y", labelcolor=AZUL)

    ax2 = ax1.twinx()
    ax2.plot(df.index, df[col_dir], color=LARANJA, linewidth=2, label=rot_dir)
    ax2.set_ylabel(rot_dir, color=LARANJA)
    ax2.tick_params(axis="y", labelcolor=LARANJA)

    for eixo in (ax1, ax2):
        eixo.ticklabel_format(axis="y", useOffset=False, style="plain")

    ax1.set_title(titulo, fontsize=13, fontweight="bold", loc="left")
    ax1.grid(alpha=0.3)
    for lado in ("top",):
        ax1.spines[lado].set_visible(False)
        ax2.spines[lado].set_visible(False)

    fig.tight_layout()
    fig.savefig(GRAFICOS / arquivo, dpi=150)
    plt.close(fig)
    print(f"  gráfico salvo: graficos/{arquivo}")


def correlacao_com_atraso(df, col_a, col_b, meses):
    """Correlação entre col_a de hoje e col_b daqui a `meses` meses."""
    return df[col_a].corr(df[col_b].shift(-meses))


def main() -> None:
    GRAFICOS.mkdir(exist_ok=True)
    df = carregar()

    print("Gerando gráficos...")
    grafico_duas_linhas(df, "selic", "Selic (% a.a.)", "ipca_12m", "IPCA 12 meses (%)",
                        "Juros x Inflação", "1_selic_ipca.png")
    grafico_duas_linhas(df, "selic", "Selic (% a.a.)", "credito_var_12m",
                        "Crescimento do crédito em 12 meses (%)",
                        "Juros x Crescimento do crédito", "2_selic_credito.png")
    grafico_duas_linhas(df, "selic", "Selic (% a.a.)", "inadimplencia", "Inadimplência (%)",
                        "Juros x Inadimplência", "3_selic_inadimplencia.png")

    print("\n===== RESUMO PARA O README =====")
    ultimo = df.dropna(subset=["selic"]).iloc[-1]
    print(f"Último mês com Selic: {ultimo.name:%m/%Y} -> {ultimo['selic']:.2f}% a.a.")
    print(f"Selic mínima: {df['selic'].min():.2f}% em {df['selic'].idxmin():%m/%Y}")
    print(f"Selic máxima: {df['selic'].max():.2f}% em {df['selic'].idxmax():%m/%Y}")
    print(f"Inadimplência mínima: {df['inadimplencia'].min():.2f}% em {df['inadimplencia'].idxmin():%m/%Y}")
    print(f"Inadimplência máxima: {df['inadimplencia'].max():.2f}% em {df['inadimplencia'].idxmax():%m/%Y}")

    print("\nCorrelação da Selic com indicadores futuros (de -1 a 1):")
    for meses in (0, 6, 12):
        c_cred = correlacao_com_atraso(df, "selic", "credito_var_12m", meses)
        c_inad = correlacao_com_atraso(df, "selic", "inadimplencia", meses)
        print(f"  {meses:>2} meses depois -> crédito: {c_cred:+.2f} | inadimplência: {c_inad:+.2f}")

    print("\nDica de leitura: correlação negativa com o crédito = juros altos freiam o crédito;"
          "\nse a correlação fica mais forte com 6 ou 12 meses, o efeito chega com atraso.")


if __name__ == "__main__":
    main()
