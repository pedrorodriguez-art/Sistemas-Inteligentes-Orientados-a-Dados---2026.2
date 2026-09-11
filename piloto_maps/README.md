# Piloto Google Maps — acesso às UPAs

Versão inicial separada dos scripts enviados. Python 3.10+, apenas biblioteca padrão.
Nenhuma chave ou consulta real incluída. Não é a entrega completa da Atividade 02.

## Revisão dos originais

- base.py selecionava colunas e criava cópia em memória; não salvava nem validava.
- CO_UNIDADE não deve ser confundido com CO_CNES (sete dígitos).
- rotas.py lia export.geojson: não havia chamada Overpass para substituir.
- Caminhos absolutos impediam execução em outro computador.
- Diretório de saída não era criado e o mesmo mapa era salvo duas vezes.
- Geometria vazia, ausência de CRS e ausência de campos de tooltip não eram tratadas antes do mapa.
- O título dizia Salvador, mas não havia filtro municipal ou recorte territorial.
- A mudança é de catálogo/desenho de linhas para estimativa de viagem origem-destino.

## Arquitetura do piloto

| Componente | Entrada | Saída / função |
|---|---|---|
| aplicativo/base.py | CSV CNES previamente selecionado | CSV de coordenadas e relatório de validação |
| aplicativo/rotas.py | Duas coordenadas e horário explícito | Requisição simulada ou resultado transitório Google |
| tests/test_piloto.py | Dados sintéticos e transporte simulado | Testes sem rede nem custos |

A ligação entre CSV e consulta ainda é manual por argumentos; coleta em lote e matriz não estão implementadas.
Não remover o GeoJSON/rotas antigo: ele documenta a abordagem anterior e pode continuar sendo usado com dados OSM.

## Executar no terminal, dentro desta pasta

```powershell
python -m unittest discover -s tests -v
python -m aplicativo.base --entrada "../upa_bahia_202607.csv" --saida dados/processados
```

Se necessário, acrescente `--encoding latin1`, conforme a codificação real do arquivo.
Entrada: CSV delimitado por ponto e vírgula. Colunas obrigatórias: CO_UNIDADE,
NO_FANTASIA, NU_LATITUDE, NU_LONGITUDE. Identificadores são lidos como texto.
Saídas: unidades_coordenadas.csv e validacao.json. Reexecutar substitui essas saídas.
O primeiro registro de cada identificador reserva o ID; duplicados posteriores são rejeitados
e devem ser revisados, não considerados automaticamente equivalentes.
Validações: esquema, largura das linhas, ID/nome não vazios, duplicidade, coordenadas
numéricas finitas nos limites globais e par 0,0 suspeito. Vírgula decimal é normalizada.
Esses limites NÃO validam pertencimento a Salvador, SUS ou classificação UPA.

### Simulação: não usa chave, não acessa rede

```powershell
python -m aplicativo.rotas --origem -12.97 -38.50 --destino -12.93 -38.47 --partida "2026-09-12T08:00:00-03:00"
```

Coordenadas acima são APENAS exemplos de sintaxe, não UPAs verificadas.
Substitua-as por pontos reais validados e atualize a data. Horários exigem fuso e janela
de -7 a +100 dias em relação à execução. Não mede trajetos históricos de julho/2026
só porque o CNES é dessa competência: versões temporais precisam ser documentadas.

### Consulta real: uma requisição potencialmente paga

Habilite faturamento e Routes API no Google Cloud. Configure chave restrita à API
e restrição de aplicação compatível com execução servidor (IP, quando aplicável).
Defina limites de uso; alerta de orçamento não é bloqueio automático de gasto.
Configure GOOGLE_MAPS_API_KEY localmente (PowerShell: `$env:GOOGLE_MAPS_API_KEY = "SUA_CHAVE"`).
Não cole a chave no chat, código ou Git; este projeto não carrega .env automaticamente.
Repita o comando de simulação acrescentando `--executar` após conferir os pontos.

Endpoint: POST https://routes.googleapis.com/directions/v2:computeRoutes.
Modo TRANSIT, alternativas desativadas, timeout 30s e máscara explícita de campos.
Retorna duração em segundos, distância em metros e etapas quando disponíveis.
Sem rota é status próprio com valores nulos; erros HTTP/rede/JSON são falhas distintas.
Não há repetição automática: impede tentativas adicionais silenciosas no piloto.

## Restrições e limites científicos

Resultados da API ficam somente na memória/terminal; não redirecionar para arquivos
nem integrar ao Folium nesta versão. Google exige atribuição e, se exibidos em mapa,
Google Maps. Antes de coleta/publicação científica, confirmar compatibilidade das
condições de armazenamento, redistribuição e uso analítico com a UFBA/provedor.
O piloto não resolve essa questão nem autoriza uma base permanente de respostas.
Sem rota retornada não significa falta de transporte. Resultado estimado não é viagem
observada; horários e cobertura precisam de validação local. As etapas são retornadas
para inspeção, ainda não agregadas em caminhada, espera ou baldeações.

## Evidência e próximos passos

Testes usam dados sintéticos, não evidência de execução com a base real.
Faltam o CSV, confirmação das UPAs de Salvador/SUS, pontos populacionais reais,
chave configurada e avaliação das condições de uso. Não há execução paga neste pacote.
Depois: piloto pequeno, validação da cobertura, decisão de viabilidade e só então lotes.
Reprodutibilidade do código não garante repetição dos resultados de API dinâmica.

## Documentação consultada

- https://developers.google.com/maps/documentation/routes/transit-route
- https://developers.google.com/maps/documentation/routes/reference/rest/v2/TopLevel/computeRoutes
- https://developers.google.com/maps/documentation/routes/policies
- https://developers.google.com/maps/documentation/routes/get-api-key
