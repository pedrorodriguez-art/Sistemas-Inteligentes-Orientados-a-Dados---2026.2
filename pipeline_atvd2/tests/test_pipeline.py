import csv
import tempfile
import unittest
from pathlib import Path
from pipeline import executar, coordenada, OBRIGATORIAS


class TestPipeline(unittest.TestCase):
    def test_coordenadas(self):
        self.assertEqual(coordenada('-12,97',90),-12.97)
        for valor in ['-12.959.299.708.001.400','nan','inf','91','']:
            self.assertIsNone(coordenada(valor,90))

    def test_preserva_id_e_separa_geo(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); arquivo=p/'entrada.csv'
            r={c:'' for c in OBRIGATORIAS}
            r.update(CO_CNES='0000123',CO_UNIDADE='2,92741E+12',NO_FANTASIA='UPA TESTE',
                     NU_LATITUDE='-12.9.7',NU_LONGITUDE='-38.5.0',CO_CEP='40000000',CO_MUNICIPIO_GESTOR='292740')
            with arquivo.open('w',newline='',encoding='utf-8') as f:
                w=csv.DictWriter(f,fieldnames=sorted(OBRIGATORIAS),delimiter=';');w.writeheader();w.writerow(r)
            resumo=executar(arquivo,p/'saida')
            self.assertEqual(resumo['cadastros_validos'],1)
            self.assertEqual(resumo['candidatas_coordenadas_validas'],0)
            with (p/'saida/cadastros_tratados.csv').open() as f:
                self.assertEqual(next(csv.DictReader(f,delimiter=';'))['cnes'],'0000123')

    def test_duplicados_nao_escolhe_primeiro(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); arquivo=p/'entrada.csv'
            r={c:'' for c in OBRIGATORIAS};r.update(CO_CNES='0000123',NO_FANTASIA='A')
            with arquivo.open('w',newline='',encoding='utf-8') as f:
                w=csv.DictWriter(f,fieldnames=sorted(OBRIGATORIAS),delimiter=';');w.writeheader();w.writerow(r);w.writerow(r)
            s=executar(arquivo,p/'saida')
            self.assertEqual(s['cadastros_validos'],0)
            self.assertEqual(s['alertas']['CNES_DUPLICADO'],2)

    def test_esquema(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'a.csv').write_text('id\n1\n')
            with self.assertRaises(ValueError):executar(p/'a.csv',p/'saida')


if __name__=='__main__': unittest.main()
