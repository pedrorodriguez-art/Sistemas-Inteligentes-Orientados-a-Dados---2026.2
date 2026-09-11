import pandas as pd
import matplotlib.pyplot as plt

# Carregando os dados
arquivo = r'C:\Users\pacot\OneDrive\Área de Trabalho\projeto\upa_bahia_202607.csv'

df = pd.read_csv(arquivo, sep=';')
df.columns = df.columns.str.strip()


print("=" * 60)
print("ANÁLISE INICIAL DOS DADOS")
print("=" * 60)


# Tamanho da base
print("\nTamanho da base:")
print(f"Registros: {df.shape[0]}")
print(f"Colunas: {df.shape[1]}")


# Tipos das colunas
print("\nTipos de dados:")
print(df.dtypes)


# Dados faltantes
print("\nDados faltantes:")

faltantes = df.isna().sum()
faltantes = faltantes[faltantes > 0]

if len(faltantes) == 0:
    print("Nenhum dado faltante encontrado.")
else:
    print(faltantes)


# Registros duplicados
print("\nRegistros duplicados:")

duplicados = df.duplicated().sum()

print(f"Quantidade: {duplicados}")
print(f"Percentual: {(duplicados / len(df) * 100):.2f}%")


# Estatísticas das colunas numéricas
print("\nResumo das variáveis numéricas:")

numericas = df.select_dtypes(include="number")

if len(numericas.columns) > 0:
    print(numericas.describe().T)
else:
    print("A base não possui variáveis numéricas.")


# Algumas informações sobre as colunas de texto
print("\nQuantidade de valores diferentes nas colunas:")

for coluna in df.select_dtypes(include="object").columns:
    quantidade = df[coluna].nunique()

    # Mostra apenas colunas com poucas categorias
    if quantidade <= 15:
        print(f"\n{coluna}: {quantidade} valores diferentes")
        print(df[coluna].value_counts().head(10))


# Verificação de datas
print("\nPeríodo dos dados:")

for coluna in df.columns:

    if "DT_" in coluna.upper() or "DATA" in coluna.upper():

        datas = pd.to_datetime(
            df[coluna],
            errors="coerce",
            dayfirst=True
        )

        if datas.notna().any():
            print(f"{coluna}:")
            print(f"  De {datas.min()} até {datas.max()}")


print("\n" + "=" * 60)
print("Fim da análise")
print("=" * 60)
