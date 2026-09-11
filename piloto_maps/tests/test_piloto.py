import io
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from aplicativo.base import preparar, coordenada
from aplicativo.rotas import montar, interpretar, consultar


class TestPiloto(unittest.TestCase):
    def test_coordenadas(self):
        self.assertEqual(coordenada('-12,9', 90), -12.9)
        for valor in ['nan', 'inf', '91', '']:
            with self.assertRaises(ValueError):
                coordenada(valor, 90)

    def test_base(self):
        with tempfile.TemporaryDirectory() as pasta:
            entrada = Path(pasta) / 'entrada.csv'
            entrada.write_text('CO_UNIDADE;NO_FANTASIA;NU_LATITUDE;NU_LONGITUDE\n001;Teste;-12,9;-38,5\n001;Duplicado;-12;-38\n002;Inválido;nan;-38\n', encoding='utf-8')
            resultado = preparar(entrada, Path(pasta)/'saida')
            self.assertEqual((resultado['recebidos'], resultado['produzidos'], len(resultado['rejeitados'])), (3, 1, 2))
            self.assertIn('001', (Path(pasta)/'saida/unidades_coordenadas.csv').read_text())

    def test_colunas_ausentes(self):
        with tempfile.TemporaryDirectory() as pasta:
            entrada = Path(pasta)/'entrada.csv'
            entrada.write_text('id\n1\n')
            with self.assertRaises(ValueError):
                preparar(entrada, Path(pasta)/'saida')

    def test_horario(self):
        agora = datetime(2026, 9, 11, tzinfo=timezone.utc)
        resultado = montar((-12, -38), (-13, -38), '2026-09-12T08:00:00-03:00', agora)
        self.assertEqual(resultado['departureTime'], '2026-09-12T11:00:00Z')
        for data in ['2026-09-12T08:00:00', '2020-01-01T00:00:00Z']:
            with self.assertRaises(ValueError):
                montar((-12, -38), (-13, -38), data, agora)

    def test_sem_rota(self):
        self.assertIsNone(interpretar({})['duracao_s'])
        self.assertEqual(interpretar({'routes': []})['status'], 'SEM_ROTA_RETORNADA')

    def test_resposta(self):
        resposta = {'routes': [{'duration': '120.5s', 'distanceMeters': 500}]}
        self.assertEqual(interpretar(resposta)['duracao_s'], 120.5)
        for invalida in [[], {'error': {}}, {'routes': None}, {'routes': [{}]}]:
            with self.assertRaises(ValueError):
                interpretar(invalida)

    def test_transporte_simulado(self):
        def transporte(req, timeout):
            self.assertEqual(timeout, 30)
            self.assertEqual(req.method, 'POST')
            return io.BytesIO(json.dumps({'routes': [{'duration':'60s','distanceMeters':100}]}).encode())
        self.assertEqual(consultar({}, 'chave-ficticia', transporte)['status'], 'OK')

    def test_falhas(self):
        for erro, mensagem in [(HTTPError('https://example.org', 403, 'Forbidden', {}, None), 'ERRO_HTTP_403'), (URLError('offline'), 'ERRO_REDE')]:
            def transporte(req, timeout):
                raise erro
            with self.assertRaisesRegex(RuntimeError, mensagem):
                consultar({}, 'ficticia', transporte)
        with self.assertRaises(ValueError):
            consultar({}, '')


if __name__ == '__main__':
    unittest.main()
