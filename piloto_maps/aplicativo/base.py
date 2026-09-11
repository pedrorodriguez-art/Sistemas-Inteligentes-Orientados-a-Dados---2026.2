"""Prepara coordenadas de uma base já selecionada; não certifica UPAs/SUS."""
import argparse
import csv
import json
import math
from pathlib import Path


def coordenada(valor, limite):
    numero = float(str(valor).strip().replace(',', '.'))
    if not math.isfinite(numero) or not -limite <= numero <= limite:
        raise ValueError('Coordenada inválida')
    return numero


def preparar(entrada, saida, encoding='utf-8-sig'):
    obrigatorias = {'CO_UNIDADE', 'NO_FANTASIA', 'NU_LATITUDE', 'NU_LONGITUDE'}
    validos, rejeitados, vistos = [], [], set()
    with Path(entrada).open(encoding=encoding, newline='') as arquivo:
        leitor = csv.DictReader(arquivo, delimiter=';')
        campos = [c.strip() for c in leitor.fieldnames or []]
        if len(campos) != len(set(campos)):
            raise ValueError('Cabeçalhos duplicados')
        if obrigatorias - set(campos):
            raise ValueError(f'Colunas ausentes: {sorted(obrigatorias - set(campos))}')
        leitor.fieldnames = campos
        for linha, registro in enumerate(leitor, 2):
            identificador = (registro.get('CO_UNIDADE') or '').strip()
            try:
                if None in registro or any(v is None for v in registro.values()):
                    raise ValueError('Número de campos incompatível com cabeçalho')
                if not identificador:
                    raise ValueError('CO_UNIDADE vazio')
                if identificador in vistos:
                    raise ValueError('CO_UNIDADE duplicado: revisar conflito')
                # Não é CO_CNES: não aplicar regra de sete dígitos a CO_UNIDADE.
                vistos.add(identificador)
                nome = registro['NO_FANTASIA'].strip()
                if not nome:
                    raise ValueError('NO_FANTASIA vazio')
                lat = coordenada(registro['NU_LATITUDE'], 90)
                lon = coordenada(registro['NU_LONGITUDE'], 180)
                if lat == 0 and lon == 0:
                    raise ValueError('Par 0,0 suspeito')
                validos.append(dict(id=identificador, nome=nome, latitude=lat, longitude=lon))
            except (ValueError, TypeError) as erro:
                rejeitados.append(dict(linha=linha, id=identificador, motivo=str(erro)))
    destino = Path(saida)
    destino.mkdir(parents=True, exist_ok=True)
    with (destino / 'unidades_coordenadas.csv').open('w', encoding='utf-8', newline='') as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=['id', 'nome', 'latitude', 'longitude'])
        escritor.writeheader()
        escritor.writerows(validos)
    relatorio = dict(recebidos=len(validos)+len(rejeitados), produzidos=len(validos),
                     rejeitados=rejeitados, aviso='Sem filtro municipal, confirmação SUS ou validação territorial.')
    (destino / 'validacao.json').write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding='utf-8')
    return relatorio


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--entrada', required=True)
    parser.add_argument('--saida', required=True, help='Pasta de saída; arquivos homônimos serão substituídos')
    parser.add_argument('--encoding', default='utf-8-sig')
    args = parser.parse_args()
    try:
        print(json.dumps(preparar(args.entrada, args.saida, args.encoding), ensure_ascii=False, indent=2))
    except (ValueError, OSError) as erro:
        parser.exit(1, f'Falha: {erro}\n')


if __name__ == '__main__':
    main()
