# Relatório do Frontend de Visualização de Indicadores

A aplicação _frontend_ é um painel de indicadores dinâmico que opera em um ambiente **Django** (servindo os templates e a estrutura de hospedagem), mas cuja lógica de dados e visualização é totalmente delegada ao JavaScript, que se comunica diretamente com a API de Indicadores (FastAPI).

---

## 1. Arquitetura e Divisão de Responsabilidades

O _frontend_ adota uma arquitetura desacoplada para gerenciamento de dados:

| Camada                  | Tecnologia                             | Responsabilidade Principal                                                                                                                  |
| :---------------------- | :------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------ |
| **Apresentação (View)** | Django Templates / Bootstrap           | Serve o HTML base, o CSS e os arquivos JavaScript. Gerencia o layout inicial e os componentes de interface.                                 |
| **Lógica e Dados**      | JavaScript (Puro, ECharts, Choices.js) | Todo o fluxo de dados: carregamento assíncrono, criação de elementos DOM (`createChartCard`), gestão de filtros e renderização de gráficos. |
| **Serviço de Dados**    | FastAPI (Backend)                      | Processamento do CSV, aplicação de filtros, e formatação do JSON final (`option_echarts`).                                                  |

### 1.1. Componentes JS Chave

O núcleo da interatividade é construído sobre bibliotecas especializadas:

- **ECharts:** Responsável por desenhar todas as visualizações, consumindo o objeto `option_echarts` formatado pelo _backend_.
- **Choices.js:** Utilizado na função `openFilterModal` para criar _selects_ amigáveis com suporte a múltipla seleção e _tags_ de opções.
- **Fetch API :** Usado para chamadas assíncronas para a API (exclusivamente o FastAPI, ignorando as rotas do Django para dados de indicador).

---

## 2. 🔄 Fluxo de Dados e Interação

O fluxo de dados é totalmente gerenciado pelo JavaScript e direcionado por eventos do usuário.

### 2.1. Carga Inicial do Dashboard

1.  O **Django** carrega o _template_ HTML.
2.  O JavaScript inicia (`DOMContentLoaded`).
3.  O JS chama `/indicators` (FastAPI) para obter a lista de IDs de indicadores.
4.  O JS itera, chamando `/indicators/{id}` para obter o **`metadata`** e o **`data_example`** (dados iniciais).
5.  A função `createChartCard` injeta o HTML do card no DOM e anexa os ouvintes de eventos (`click`) aos botões de filtros.

### 2.2. O Ciclo de Aplicação de Filtros (Interação Dinâmica)

Este ciclo representa a principal carga de comunicação do _frontend_ com o _backend_:

1.  **Pré-seleção de Filtros:**
    - `openFilterModal` lê o campo **`applyed_filters`** do JSON do _backend_ (passado via `data_example`).
    - Utiliza o método `setChoiceByValue` do Choices.js para **pré-selecionar** as opções correspondentes, refletindo o estado atual do gráfico.
2.  **Envio da Requisição:**
    - Ao clicar em "Aplicar Filtros", o JS coleta os valores selecionados (strings) de todos os _selects_.
    - Monta a _query string_ (e.g., `nome_option_f7=2025&nome_option_f1=Goiânia`).
    - Envia o `GET` assíncrono para a rota de filtro do FastAPI: `/indicators/{id}/filter?{query_string}`.
3.  **Atualização da Visualização:**
    - O JS exibe um _loader_ durante o processamento do CSV pelo _backend_.
    - Ao receber o JSON de resposta, a função `createChartCard` é chamada novamente, atualizando os dados e **redesenhando o gráfico** no container ECharts.

---

## 3. Requisitos de Renderização (ECharts)

Para garantir a plotagem correta, o JS deve lidar com os requisitos de cada tipo de visualização:

1.  **Mapas Temáticos:** O JS deve primeiro buscar e registrar o GeoJSON (via `/maps/{map_name}`) no ECharts antes de plotar os dados filtrados.
2.  **Séries Históricas:** Os dados são injetados diretamente nas configurações `xAxis` e `series` do ECharts.

> **Princípio Central:** O _frontend_ confia que o _backend_ sempre fornecerá o JSON final (metadata + data_example) pronto para ser injetado no ECharts, simplificando a lógica de apresentação e focando na interação do usuário.
