"""Uma consulta TRANSIT por execução. Padrão: somente simular a requisição."""
import argparse
import json
import os
import re
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from .base import coordenada

ENDPOINT = 'https://routes.googleapis.com/directions/v2:computeRoutes'
FIELD_MASK = 'routes.duration,routes.distanceMeters,routes.legs.steps.travelMode,routes.legs.steps.transitDetails'


def ponto(lat, lon):
    return {'location': {'latLng': {'latitude': coordenada(lat, 90), 'longitude': coordenada(lon, 180)}}}


def montar(origem, destino, partida, agora=None):
    horario = datetime.fromisoformat(partida.replace('Z', '+00:00'))
    if horario.tzinfo is None:
        raise ValueError('Informe fuso explícito, por exemplo -03:00')
    horario = horario.astimezone(timezone.utc)
    agora = agora or datetime.now(timezone.utc)
    if not agora - timedelta(days=7) <= horario <= agora + timedelta(days=100):
        raise ValueError('Partida fora da janela TRANSIT: -7 a +100 dias')
    return dict(origin=ponto(*origem), destination=ponto(*destino), travelMode='TRANSIT',
                departureTime=horario.isoformat().replace('+00:00', 'Z'),
                computeAlternativeRoutes=False, languageCode='pt-BR', units='METRIC')


def interpretar(resposta):
    if not isinstance(resposta, dict) or 'error' in resposta:
        raise ValueError('Estrutura de resposta inválida')
    rotas = resposta.get('routes', [])
    if not isinstance(rotas, list):
        raise ValueError('routes não é lista')
    if not rotas:
        return dict(status='SEM_ROTA_RETORNADA', duracao_s=None, distancia_m=None)
    rota = rotas[0]
    if not isinstance(rota, dict):
        raise ValueError('Rota inválida')
    duracao = rota.get('duration')
    distancia = rota.get('distanceMeters')
    if not isinstance(duracao, str) or not re.fullmatch(r'\d+(?:\.\d{1,9})?s', duracao):
        raise ValueError('Duração ausente ou inválida')
    if isinstance(distancia, bool) or not isinstance(distancia, int) or distancia < 0:
        raise ValueError('Distância ausente ou inválida')
    return dict(status='OK', duracao_s=float(duracao[:-1]), distancia_m=distancia,
                etapas=rota.get('legs', []))


def consultar(payload, chave, transport=urlopen):
    if not chave or not chave.strip():
        raise ValueError('Defina GOOGLE_MAPS_API_KEY no ambiente')
    requisicao = Request(ENDPOINT, data=json.dumps(payload).encode(), method='POST', headers={
        'Content-Type': 'application/json', 'X-Goog-Api-Key': chave,
        'X-Goog-FieldMask': FIELD_MASK})
    try:
        with transport(requisicao, timeout=30) as resposta:
            resultado = json.load(resposta)
    except HTTPError as erro:
        # Não imprimir corpo remoto nem cabeçalhos para evitar expor credenciais.
        raise RuntimeError(f'ERRO_HTTP_{erro.code}; sem repetição automática') from None
    except (URLError, TimeoutError, OSError):
        raise RuntimeError('ERRO_REDE; sem repetição automática') from None
    except (ValueError, UnicodeError):
        raise RuntimeError('RESPOSTA_JSON_INVALIDA') from None
    try:
        return interpretar(resultado)
    except ValueError:
        raise RuntimeError('RESPOSTA_INVALIDA') from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origem', nargs=2, required=True, type=float, metavar=('LAT', 'LON'))
    parser.add_argument('--destino', nargs=2, required=True, type=float, metavar=('LAT', 'LON'))
    parser.add_argument('--partida', required=True, help='ISO 8601 com fuso explícito')
    parser.add_argument('--executar', action='store_true', help='Autoriza uma chamada potencialmente paga')
    args = parser.parse_args()
    try:
        payload = montar(args.origem, args.destino, args.partida)
        if not args.executar:
            print('SIMULAÇÃO: nenhuma consulta realizada. Requisição planejada:')
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        resultado = consultar(payload, os.environ.get('GOOGLE_MAPS_API_KEY', ''))
        print('Google Maps — resultado transitório; não exportado nem desenhado em mapa.')
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
    except (ValueError, RuntimeError) as erro:
        parser.exit(1, f'Falha: {erro}\n')


if __name__ == '__main__':
    main()
