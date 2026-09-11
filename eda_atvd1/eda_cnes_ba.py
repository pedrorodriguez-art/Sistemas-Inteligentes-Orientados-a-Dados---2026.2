from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

df = pd.read_csv(r'C:\Users\pacot\OneDrive\Área de Trabalho\projeto\upa_bahia_202607.csv',sep=';')

df.columns = df.columns.str.strip()

print("\n" + "=" * 70)
print("EDA SIMPLES — UNIDADES DE PRONTO ATENDIMENTO / SALVADOR-BA")
print("=" * 70)

print(f"\nQuantidade de registros: {len(df):,}")
print(f"Quantidade de colunas: {len(df.columns):,}")

print("\nColunas disponíveis:")
print(df.columns.tolist())


#################3

campos_principais = [
    "NO_FANTASIA",
    "NO_RAZAO_SOCIAL",
    "NO_BAIRRO",
    "NO_LOGRADOURO",
    "NU_ENDERECO",
    "CO_CEP",
    "NU_LATITUDE",
    "NU_LONGITUDE",
    "CO_CNES",
    "CO_UNIDADE"
]

# Mantém somente os campos que existem no CSV
campos_principais = [
    coluna for coluna in campos_principais
    if coluna in df.columns
]

resumo_ausentes = pd.DataFrame({
    "Campo": campos_principais,
    "Dados faltantes": [
        df[coluna].isna().sum()
        for coluna in campos_principais
    ]
})

resumo_ausentes["Preenchidos"] = (
    len(df) - resumo_ausentes["Dados faltantes"]
)

resumo_ausentes["Faltantes (%)"] = (
    resumo_ausentes["Dados faltantes"] / len(df) * 100
).round(2)

resumo_ausentes = resumo_ausentes.sort_values(
    by="Faltantes (%)",
    ascending=False
)

print("\n" + "-" * 70)
print("CAMPOS FALTANTES")
print("-" * 70)
print(resumo_ausentes.to_string(index=False))

# Retorno direto dos três campos mais importantes
for coluna in ["NO_FANTASIA", "NU_LATITUDE", "NU_LONGITUDE"]:
    if coluna in df.columns:
        faltantes = df[coluna].isna().sum()
        preenchidos = df[coluna].notna().sum()

        print(f"\n{coluna}:")
        print(f"  Preenchidos: {preenchidos:,}")
        print(f"  Faltantes: {faltantes:,}")
        print(f"  Percentual faltante: {(faltantes / len(df) * 100):.2f}%")

# Gráfico de dados faltantes
plt.figure(figsize=(10, 5))

sns.barplot(
    data=resumo_ausentes,
    x="Faltantes (%)",
    y="Campo",
    hue="Campo",
    legend=False,
    palette="Reds_r"
)

plt.title("Percentual de dados faltantes por campo")
plt.xlabel("Dados faltantes (%)")
plt.ylabel("Campos")
plt.xlim(0, 100)
plt.tight_layout()
plt.show()


