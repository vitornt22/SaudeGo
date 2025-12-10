# 📊 README: Backend de Indicadores Estatísticos

Este _backend_, construído com **FastAPI** e **Pandas**, é responsável por servir dados dinâmicos para visualizações de gráficos (séries históricas, mapas) baseando-se em arquivos estáticos (CSV e JSON). Ele atua como um motor de processamento, aplicando filtros e formatando os dados para consumo no _frontend_ (ECharts).

---

## 🏗️ 1. Estrutura e Fontes de Dados

O sistema opera com base em uma estrutura de arquivos de fácil manutenção. O diretório **`data/`** é o coração da aplicação.

| Caminho                               | Conteúdo e Finalidade                                                                                                  |
| :------------------------------------ | :--------------------------------------------------------------------------------------------------------------------- |
| **`data/ind_{ID}/metadata.json`**     | Contém a ficha técnica do indicador, nome, fontes e a estrutura base das configurações do gráfico (`option_echarts`).  |
| **`data/ind_{ID}/data_example.json`** | Estrutura de inicialização e **registro de filtros aplicados** (`applyed_filters`).                                    |
| **`data/ind_{ID}/raw_data.csv`**      | **Fonte Primária de Dados.** Contém os dados brutos, tabulares e desagregados que serão lidos e filtrados pelo Pandas. |
| **`data/maps/*.json`**                | Arquivos GeoJSON necessários para desenhar mapas temáticos (ex: limites de municípios).                                |

---

## 🛣️ 2. Endpoints (Rotas da API)

### 2.1. Acesso à Informação Base

| Rota               | Método | Descrição                                                                                                                            |
| :----------------- | :----- | :----------------------------------------------------------------------------------------------------------------------------------- |
| `/indicators`      | `GET`  | Lista IDs dos indicadores disponíveis com suporte a **paginação** (`limit`, `offset`).                                               |
| `/indicators/{id}` | `GET`  | Retorna o `metadata.json` e `data_example.json` do indicador. Usado para carregar a **ficha técnica** e o estado inicial do gráfico. |
| `/maps/{map_name}` | `GET`  | Serve arquivos GeoJSON (mapas de fronteiras) diretamente para o _frontend_.                                                          |

### 2.2. O Motor de Filtros: `/indicators/{indicator_id}/filter`

Esta rota é a mais intensiva, pois processa o CSV completo.

#### 📝 Fluxo de Processamento

1.  **Leitura de Arquivos:** Carrega o `metadata.json`, `data_example.json` (como base) e o **`raw_data.csv`** (para o Pandas DataFrame).
2.  **Agrupamento de Filtros:** Os parâmetros da _query string_ são agrupados por coluna de filtro.
3.  **Lógica AND/OR:**
    - Filtros dentro do mesmo campo (ex: selecionar vários anos) são combinados com lógica **OR** (`.isin()` do Pandas).
    - Filtros de campos diferentes (ex: Ano E Município) são combinados com lógica **AND**.
4.  **Detecção de Tipo:** Determina se o gráfico resultante deve ser um **Mapa** (`process_map_indicator`) ou uma **Série Histórica/Linha** (lógica padrão).

---

## 🧭 3. Processamento Dinâmico (Pandas)

O _backend_ usa **heurística** para se adaptar a diferentes estruturas de CSVs, procurando por palavras-chave nas colunas para identificar os dados corretos.

### A. Gráfico de Linha/Série Histórica

A função procura pelas seguintes colunas para montar o gráfico de série temporal:

- **Eixo X (`xAxis_field`):** Busca por colunas contendo `"ano"`.
- **Eixo Y (`value_field`):** Busca por `"val"`, `"quant"`, `"tx"`.
- **Série (`category_field`):** Usado para múltiplas linhas (ex: "categoria", "faixa").

### B. Mapa Temático (`process_map_indicator`)

A função converte o DataFrame para o formato exigido pelo mapa (lista de `{name: value}`):

- **Campo de Nome (`name_field`):** Busca por `"mun"` ou `"nome"`.
- **Campo de Valor (`value_field`):** Busca por `"val"`, `"tx"`, `"prop"`.
- **Ajuste Visual (`visualMap`):** Calcula o valor **mínimo** e **máximo** dos dados filtrados para garantir que a escala de cores do mapa esteja sempre correta.

> 💡 **Nota:** Todos os _endpoints_ de dados (filtragem) retornam a estrutura `{"metadata": ..., "data_example": ...}`, garantindo que o _frontend_ sempre tenha a ficha técnica e a configuração atualizada do gráfico.
