# Sistemas Inteligentes Orientados a Dados — 2026.2

Repositório das atividades desenvolvidas na disciplina da UFBA.

## Projeto

Análise da acessibilidade geográfica potencial às Unidades de Pronto Atendimento (UPAs) de Salvador, utilizando dados cadastrais, populacionais e estimativas de deslocamento.

## Organização

- **[eda_atvd1/](eda_atvd1/)** — exploração e caracterização inicial dos dados do CNES.
- **[pipeline_atvd2/](pipeline_atvd2/)** — pipeline de tratamento, validação e reconstrução de coordenadas candidatas.
- **[piloto_maps/](piloto_maps/)** — implementação piloto para consultas à API do Google Maps.

## Executar o pipeline

Requisito: Python 3.10 ou superior, sem dependências externas.

Na raiz do repositório:

```bash
python pipeline_atvd2/pipeline.py --teste
python pipeline_atvd2/pipeline.py
```

Os resultados são gravados em `pipeline_atvd2/dados/processados/`.

## Situação atual

O pipeline processa 98 cadastros e identifica 12 candidatas a UPA pelo nome. As coordenadas reconstruídas estão sinalizadas para revisão e precisam ser conferidas com os endereços das unidades antes das consultas de deslocamento.

A integração com dados populacionais do IBGE e a validação das consultas ao Google Maps são etapas futuras.

## Documentação

Consulte o [relatório da Atividade 02](pipeline_atvd2/docs/atividade02.md) para conhecer as transformações, validações, resultados e limitações.