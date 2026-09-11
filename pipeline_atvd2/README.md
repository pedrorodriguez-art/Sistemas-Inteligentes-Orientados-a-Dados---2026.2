# Atividade 02 — Pipeline inicial de dados

Projeto: acessibilidade geográfica às UPAs de Salvador.
Disciplina: Sistemas Inteligentes Orientados a Dados — PGCOMP/UFBA, 2026.2.

O pipeline foi executado sobre o arquivo real `upa_bahia_202607.csv`:
98 cadastros preservados, 12 candidatas a UPA por nome e nenhuma candidata com
coordenadas numéricas válidas. A etapa cadastral está implementada; o cálculo de
rotas permanece bloqueado pela qualidade dos dados. Veja o relatório completo
em [docs/atividade02.md](docs/atividade02.md).

## Executar

Requisito: Python 3.10 ou superior. Testado com Python 3.12.14.
Não requer pip, pandas, credenciais, internet ou Google Maps.
Na pasta que contém este README:

```bash
python pipeline.py
python -m unittest discover -s tests -v
```

O primeiro comando usa caminhos relativos ao próprio script, independentemente
da pasta de onde ele for chamado. Para outra entrada ou pasta de saída:

```bash
python pipeline.py --entrada dados/brutos/upa_bahia_202607.csv --saida dados/nova_execucao --encoding utf-8-sig
```

A saída padrão é `dados/processados/`. Uma nova execução substitui os arquivos
de saída homônimos; use outra pasta para preservar uma execução anterior.
O arquivo bruto permanece intacto. Não abra e salve novamente o CSV no Excel:
importe identificadores como texto se precisar visualizá-lo.

## Conteúdo

| Arquivo | Função |
|---|---|
| `pipeline.py` | Leitura, transformação, validação, saídas e log |
| `tests/test_pipeline.py` | Testes com dados sintéticos, separados da execução real |
| `dados/brutos/upa_bahia_202607.csv` | Cópia byte a byte da entrada recebida |
| `dados/processados/cadastros_tratados.csv` | Cadastros com CNES válido e único e nome preenchido |
| `dados/processados/pendencias.csv` | Registros com qualquer alerta, inclusive os preservados |
| `dados/processados/candidatas_upa_revisao.csv` | Subconjunto cadastral identificado pelo nome, para revisão |
| `dados/processados/candidatas_coordenadas_validas.csv` | Subconjunto candidato com coordenadas válidas numericamente |
| `dados/processados/execucao.json` | Contagens, ambiente, transformações e hashes SHA-256 |
| `dados/processados/execucao.log` | Evidência legível da execução real |
| `docs/atividade02.md` | Respostas aos itens da atividade, arquitetura e decisões |

Os CSVs de saída são UTF-8, delimitados por ponto e vírgula. Valores numéricos
usam ponto decimal; campos vazios de latitude/longitude significam indisponibilidade,
nunca zero. `cnes`, `cep` e códigos administrativos devem ser lidos como texto.
As saídas são subconjuntos sobrepostos: suas contagens não devem ser somadas.

## Esquema das saídas

| Campos | Definição |
|---|---|
| `linha_origem` | Linha lógica no CSV, considerando cabeçalho como linha 1 |
| `cnes` | Identificador textual de sete dígitos, com zeros iniciais preservados |
| `co_unidade_original` | Valor recebido, mantido sem reconstrução |
| `nome`, `logradouro`, `numero`, `bairro`, `cep` | Dados cadastrais selecionados |
| `municipio_gestor` | Código de gestão; não usado como prova de localização física |
| `tp_unidade`, `co_tipo_unidade`, `co_tipo_estabelecimento` | Campos distintos preservados, sem equivalência presumida |
| `latitude_original`, `longitude_original` | Representações recebidas, para auditoria |
| `latitude`, `longitude` | Decimais validados ou vazios se o par não puder ser usado |
| `candidata_upa_nome` | 1 para correspondência por nome; 0 em caso contrário |
| `status_cadastro` | VALIDO: CNES válido/único e nome presente; PENDENTE: falha nesses critérios |
| `status_coordenadas` | VALIDAS_NUMERICAMENTE ou PENDENTES |
| `alertas` | Códigos de problemas separados por `|` |

VALIDO não significa cadastro oficialmente confirmado, nem ausência de alertas.
Nem mesmo coordenadas válidas numericamente certificam pertencimento a Salvador.

## Como entregar no repositório existente

Copie esta pasta como `atividade02/` dentro do mesmo repositório do projeto.
Não substitua o README principal: acrescente nele um link para `atividade02/README.md`.
Inclua o código, a entrada usada, as saídas e a documentação no commit da atividade.
Não foi criado um repositório novo nem realizado push: o repositório remoto não foi fornecido.
Antes de tornar a entrada pública, revise os campos pessoais presentes no arquivo bruto;
as saídas selecionam somente campos necessários ao projeto.

## Reprodutibilidade

O código é offline e determinístico nas saídas CSV para a mesma entrada e parâmetros.
O JSON e o log registram nova hora de execução. O JSON inclui hashes da entrada,
do script e de cada CSV de saída para rastreabilidade. O arquivo é identificado
como competência julho/2026 pelo nome informado, sem nova validação na fonte CNES.
Erros de esquema, leitura ou escrita encerram com código 1. Alertas de qualidade
não impedem a produção do diagnóstico e retornam código 0 com log explícito.

## Limites desta entrega

Não inclui consulta Google, geocodificação, validação SUS, confirmação oficial de UPAs,
recorte por limite municipal, dados populacionais ou cálculo de acessibilidade.
O piloto Google entregue anteriormente é separado e não é dependência desta atividade.
O erro de coordenadas deve ser resolvido na origem antes de alimentar a API.
