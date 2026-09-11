import argparse
import csv
import hashlib
import json
import platform
import re

from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parent

FAIXA_LATITUDE = (-14, -12)
FAIXA_LONGITUDE = (-39, -37)

OBRIGATORIAS = {
    "CO_CNES",
    "CO_UNIDADE",
    "NO_FANTASIA",
    "NU_LATITUDE",
    "NU_LONGITUDE",
    "CO_CEP",
    "CO_MUNICIPIO_GESTOR",
    "TP_UNIDADE",
    "CO_TIPO_UNIDADE",
}

CAMPOS = [
    "linha_origem",
    "cnes",
    "co_unidade_original",
    "nome",
    "logradouro",
    "numero",
    "bairro",
    "cep",
    "municipio_gestor",
    "tp_unidade",
    "co_tipo_unidade",
    "co_tipo_estabelecimento",
    "latitude_original",
    "longitude_original",
    "latitude",
    "longitude",
    "candidata_upa_nome",
    "status_cadastro",
    "status_coordenadas",
    "alertas",
]


def normalizar_coordenada(valor, minimo, maximo):
    """Retorna o valor numérico candidato e o status da transformação."""

    texto = str(valor).strip()

    if texto.lower() in {"", "nan", "none", "null"}:
        return None, "AUSENTE"

    # Preserva números que já possuem formato decimal válido.
    if re.fullmatch(r"[+-]?\d+(?:[.,]\d+)?", texto):
        numero = Decimal(texto.replace(",", "."))

        if minimo <= numero <= maximo:
            return float(numero), "FORMATO_VALIDO"

        return None, "FORA_DA_FAIXA"

    # Reconhece vários grupos separados por pontos.
    if not re.fullmatch(r"[+-]?\d{1,3}(?:\.\d{3}){2,}", texto):
        return None, "FORMATO_NAO_RECONHECIDO"

    sinal = -1 if texto.startswith("-") else 1
    digitos = texto.lstrip("+-").replace(".", "")

    candidatos = set()

    # Testa possíveis posições da casa decimal.
    for posicao in range(1, len(digitos)):
        numero = sinal * Decimal(
            digitos[:posicao] + "." + digitos[posicao:]
        )

        if minimo <= numero <= maximo:
            candidatos.add(numero)

    if len(candidatos) == 1:
        return float(candidatos.pop()), "RECONSTRUIDA_REVISAR"

    if len(candidatos) > 1:
        return None, "AMBIGUA"

    return None, "FORA_DA_FAIXA"


def escrever_csv(caminho, registros):
    """Salva registros estruturados, inclusive quando a lista está vazia."""

    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        writer = csv.DictWriter(
            arquivo,
            fieldnames=CAMPOS,
            delimiter=";",
        )
        writer.writeheader()
        writer.writerows(registros)


def executar(entrada, saida, encoding="utf-8-sig"):
    entrada = Path(entrada)
    saida = Path(saida)

    if entrada.resolve().is_relative_to(saida.resolve()):
        raise ValueError(
            "A entrada deve ficar fora da pasta de saída."
        )

    # Leitura textual: preserva zeros iniciais e valores originais.
    with entrada.open(encoding=encoding, newline="") as arquivo:
        reader = csv.DictReader(arquivo, delimiter=";")

        headers = reader.fieldnames or []
        limpos = [campo.strip() for campo in headers]

        if len(limpos) != len(set(limpos)):
            raise ValueError("Existem cabeçalhos duplicados.")

        faltantes = OBRIGATORIAS - set(limpos)

        if faltantes:
            raise ValueError(
                f"Colunas obrigatórias ausentes: {sorted(faltantes)}"
            )

        reader.fieldnames = limpos
        brutos = list(reader)

    if not brutos:
        raise ValueError("Arquivo sem registros.")

    if any(
        None in registro
        or any(valor is None for valor in registro.values())
        for registro in brutos
    ):
        raise ValueError(
            "Há linhas com quantidade de campos diferente do cabeçalho."
        )

    frequencias = Counter(
        registro["CO_CNES"].strip()
        for registro in brutos
    )

    registros = []
    motivos = Counter()

    ajustes = Counter({
        "cabecalhos_aparados": sum(
            original != limpo
            for original, limpo in zip(headers, limpos)
        ),
        "celulas_com_espacos_aparados": 0,
        "coordenadas_reconstruidas": 0,
        "pares_reconstruidos_para_revisao": 0,
        "coordenadas_virgula_para_ponto": 0,
    })

    for linha, bruto in enumerate(brutos, start=2):
        r = {
            campo: valor.strip()
            for campo, valor in bruto.items()
        }

        ajustes["celulas_com_espacos_aparados"] += sum(
            bruto[campo] != valor
            for campo, valor in r.items()
        )

        cnes = r["CO_CNES"]
        alertas = []

        # Validações cadastrais.
        id_valido = bool(re.fullmatch(r"\d{7}", cnes))

        if not id_valido:
            alertas.append("CNES_INVALIDO")

        if frequencias[cnes] > 1:
            alertas.append("CNES_DUPLICADO")

        if not r["NO_FANTASIA"]:
            alertas.append("NOME_AUSENTE")

        cadastro_ok = (
            id_valido
            and frequencias[cnes] == 1
            and bool(r["NO_FANTASIA"])
        )

        if not re.fullmatch(r"\d+", r["CO_UNIDADE"]):
            alertas.append("CO_UNIDADE_NAO_INTEIRO_TEXTUAL")

        if not re.fullmatch(r"\d{8}", r["CO_CEP"]):
            alertas.append("CEP_INVALIDO")

        if not re.fullmatch(r"\d{6}", r["CO_MUNICIPIO_GESTOR"]):
            alertas.append("MUNICIPIO_GESTOR_INVALIDO")

        if not r["CO_TIPO_UNIDADE"]:
            alertas.append("CO_TIPO_UNIDADE_AUSENTE")

        # Normalização das coordenadas.
        lat, status_lat = normalizar_coordenada(
            r["NU_LATITUDE"],
            *FAIXA_LATITUDE,
        )

        lon, status_lon = normalizar_coordenada(
            r["NU_LONGITUDE"],
            *FAIXA_LONGITUDE,
        )

        geo_ok = lat is not None and lon is not None

        reconstruida = (
            status_lat == "RECONSTRUIDA_REVISAR"
            or status_lon == "RECONSTRUIDA_REVISAR"
        )

        if not geo_ok:
            status_geo = "PENDENTES"
            alertas.append("COORDENADAS_INVALIDAS")

        elif reconstruida:
            status_geo = "RECONSTRUIDAS_REVISAR"

        else:
            status_geo = "VALIDAS_NUMERICAMENTE"

        # Registra o resultado de cada coluna.
        for campo, status in [
            ("LATITUDE", status_lat),
            ("LONGITUDE", status_lon),
        ]:
            if status != "FORMATO_VALIDO":
                alertas.append(f"{campo}_{status}")

            if status == "RECONSTRUIDA_REVISAR":
                ajustes["coordenadas_reconstruidas"] += 1

        if geo_ok and reconstruida:
            ajustes["pares_reconstruidos_para_revisao"] += 1

        ajustes["coordenadas_virgula_para_ponto"] += sum([
            status_lat == "FORMATO_VALIDO"
            and "," in r["NU_LATITUDE"],

            status_lon == "FORMATO_VALIDO"
            and "," in r["NU_LONGITUDE"],
        ])

        # Triagem pelo nome, sem confirmação oficial de classificação.
        candidata = bool(
            re.search(
                r"\bUPA\b|UNIDADE DE PRONTO ATENDIMENTO",
                r["NO_FANTASIA"].upper(),
            )
        )

        motivos.update(alertas)

        registros.append({
            "linha_origem": linha,
            "cnes": cnes,
            "co_unidade_original": bruto["CO_UNIDADE"],
            "nome": r["NO_FANTASIA"],
            "logradouro": r.get("NO_LOGRADOURO", ""),
            "numero": r.get("NU_ENDERECO", ""),
            "bairro": r.get("NO_BAIRRO", ""),
            "cep": r["CO_CEP"],
            "municipio_gestor": r["CO_MUNICIPIO_GESTOR"],
            "tp_unidade": r["TP_UNIDADE"],
            "co_tipo_unidade": r["CO_TIPO_UNIDADE"],
            "co_tipo_estabelecimento": r.get(
                "CO_TIPO_ESTABELECIMENTO", ""
            ),
            "latitude_original": bruto["NU_LATITUDE"],
            "longitude_original": bruto["NU_LONGITUDE"],
            "latitude": lat,
            "longitude": lon,
            "candidata_upa_nome": int(candidata),
            "status_cadastro": (
                "VALIDO" if cadastro_ok else "PENDENTE"
            ),
            "status_coordenadas": status_geo,
            "alertas": "|".join(alertas),
        })

    # As saídas são subconjuntos sobrepostos.
    cadastral = [
        r for r in registros
        if r["status_cadastro"] == "VALIDO"
    ]

    pendencias = [
        r for r in registros
        if r["alertas"]
    ]

    candidatas = [
        r for r in cadastral
        if r["candidata_upa_nome"]
    ]

    geograficas = [
        r for r in candidatas
        if r["status_coordenadas"] == "VALIDAS_NUMERICAMENTE"
    ]

    reconstruidas = [
        r for r in candidatas
        if r["status_coordenadas"] == "RECONSTRUIDAS_REVISAR"
    ]

    saida.mkdir(parents=True, exist_ok=True)

    conjuntos = {
        "cadastros_tratados.csv": cadastral,
        "pendencias.csv": pendencias,
        "candidatas_upa_revisao.csv": candidatas,
        "candidatas_coordenadas_validas.csv": geograficas,
        "candidatas_coordenadas_reconstruidas.csv": reconstruidas,
    }

    for nome, dados in conjuntos.items():
        escrever_csv(saida / nome, dados)

    resumo = {
        "execucao_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "entrada": entrada.name,
        "entrada_sha256": hashlib.sha256(
            entrada.read_bytes()
        ).hexdigest(),
        "pipeline_sha256": hashlib.sha256(
            Path(__file__).read_bytes()
        ).hexdigest(),
        "encoding": encoding,
        "separador": ";",
        "competencia_informada": (
            "2026-07 (nome do arquivo; não verificada na fonte)"
        ),
        "faixa_latitude_triagem": FAIXA_LATITUDE,
        "faixa_longitude_triagem": FAIXA_LONGITUDE,
        "bytes_entrada": entrada.stat().st_size,
        "colunas_entrada": len(limpos),
        "recebidos": len(registros),
        "cadastros_validos": len(cadastral),
        "cadastros_pendentes": len(registros) - len(cadastral),
        "registros_com_alertas": len(pendencias),
        "candidatas_upa_por_nome": len(candidatas),
        "candidatas_coordenadas_validas": len(geograficas),
        "candidatas_coordenadas_reconstruidas": len(reconstruidas),
        "alertas": dict(motivos),
        "transformacoes": dict(ajustes),
        "municipios_gestores": dict(Counter(
            r["CO_MUNICIPIO_GESTOR"].strip()
            for r in brutos
        )),
        "tipos_unidade": dict(Counter(
            r["TP_UNIDADE"].strip()
            for r in brutos
        )),
        "saidas": {
            nome: {
                "registros": len(dados),
                "sha256": hashlib.sha256(
                    (saida / nome).read_bytes()
                ).hexdigest(),
            }
            for nome, dados in conjuntos.items()
        },
    }

    (saida / "execucao.json").write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    log = [
        f"Execução UTC: {resumo['execucao_utc']}",
        f"Entrada: {entrada.name}",
        f"Registros recebidos: {len(registros)}",
        f"Cadastros válidos pelos critérios CNES/nome: {len(cadastral)}",
        f"Candidatas a UPA pelo nome: {len(candidatas)}",
        (
            "Pares reconstruídos em toda a entrada: "
            f"{ajustes['pares_reconstruidos_para_revisao']}"
        ),
        (
            "Candidatas a UPA com coordenadas reconstruídas: "
            f"{len(reconstruidas)}"
        ),
        (
            "Candidatas a UPA com coordenadas válidas sem reconstrução: "
            f"{len(geograficas)}"
        ),
        (
            "Coordenadas reconstruídas são candidatas para revisão; "
            "os valores originais foram preservados."
        ),
        *[
            f"ALERTA {motivo}: {quantidade} registros"
            for motivo, quantidade in motivos.items()
        ],
        "CONCLUÍDO COM ALERTAS" if pendencias else "CONCLUÍDO",
        (
            "As faixas são aproximadas. A saída não certifica endereço, "
        ),
    ]

    (saida / "execucao.log").write_text(
        "\n".join(log) + "\n",
        encoding="utf-8",
    )

    print("\n".join(log))

    return resumo


def teste_normalizacao():
    """Teste simples da transformação; não valida o endereço real."""

    lat, status_lat = normalizar_coordenada(
        "-12.959.299.708.001.400",
        *FAIXA_LATITUDE,
    )

    lon, status_lon = normalizar_coordenada(
        "-3.848.756.432.533.260",
        *FAIXA_LONGITUDE,
    )

    assert lat is not None and lon is not None
    assert abs(lat - (-12.9592997080014)) < 1e-12
    assert abs(lon - (-38.4875643253326)) < 1e-12
    assert status_lat == status_lon == "RECONSTRUIDA_REVISAR"

    assert normalizar_coordenada(
        "-12.97", *FAIXA_LATITUDE
    ) == (-12.97, "FORMATO_VALIDO")

    assert normalizar_coordenada(
        "", *FAIXA_LATITUDE
    ) == (None, "AUSENTE")

    print("Teste de normalização passou.")
    print(f"Latitude candidata: {lat}")
    print(f"Longitude candidata: {lon}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--entrada",
        type=Path,
        default=ROOT / "dados/brutos/upa_bahia_202607.csv",
    )

    parser.add_argument(
        "--saida",
        type=Path,
        default=ROOT / "dados/processados",
        help="Arquivos homônimos nesta pasta serão substituídos.",
    )

    parser.add_argument(
        "--encoding",
        default="utf-8-sig",
    )

    parser.add_argument(
        "--teste",
        action="store_true",
        help="Executa somente o teste simples, sem ler o CSV.",
    )

    args = parser.parse_args()

    try:
        if args.teste:
            teste_normalizacao()
        else:
            executar(
                args.entrada,
                args.saida,
                args.encoding,
            )

    except (OSError, ValueError, csv.Error) as erro:
        parser.exit(1, f"FALHA: {erro}\n")