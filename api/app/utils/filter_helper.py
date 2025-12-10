from collections import defaultdict
import json
from fastapi import HTTPException
import pandas as pd


def return_df_empty(base_example, applyed_filters):
    example = base_example.copy()
    example["applyed_filters"] = applyed_filters
    example["option_echarts"]["xAxis"] = {"data": []}
    example["option_echarts"]["series"] = []
    example["data_criacao"] = pd.Timestamp.now().strftime(
        "%Y-%m-%d %H:%M:%S")
    return example


def is_multi_series(metadata):
    viz_type = metadata.get("viz", "").lower()
    # Se o metadata for SIMPLES, ou se não houver um category_field válido, é Simples.
    return ("multipla" in viz_type or "múltipla" in viz_type)


def detect_validation_fields(df, base_example, applyed_filters, metadata):
    # Detecção de campos e validação
    xAxis_field = None
    category_field = None
    value_field = None
    df_cols = df.columns.tolist()

    # Sempre aplica o campo ano ou nome_option_f7 ao eixo X
    if not xAxis_field or xAxis_field not in df_cols:
        xAxis_field = next(
            (c for c in df_cols if c == 'nome_option_f7' or "ano" in c.lower()), df_cols[0])
    # tenta achar alguma coluna que contenha cat, categoria, ou faixa
    if not category_field or category_field not in df_cols:
        category_field = next((c for c in df_cols if "cat" in c.lower(
        ) or "faixa" in c.lower()), df_cols[1] if len(df_cols) > 1 else "__NO_CATEGORY__")
    # tenta encontrar campos para valores ou quantidade
    if not value_field or value_field not in df_cols:
        value_field = next(
            (c for c in df_cols
             if "val" in c.lower()
             or "quant" in c.lower()
             or "qtd" in c.lower()
             or "tx" in c.lower()),
            df_cols[-1]
        )

    if xAxis_field not in df_cols or value_field not in df_cols:
        example = return_df_empty(base_example, apply_filters)
        return {"metadata": metadata, "data_example": example}

    return xAxis_field, value_field, category_field


def load_files(DATA_DIR, indicator_id, ):
    # Setup e carregamento dos arquivos
    indicator_folder = DATA_DIR / f"ind_{indicator_id}"
    csv_path = indicator_folder / "raw_data.csv"
    metadata_path = indicator_folder / "metadata.json"
    data_example_path = indicator_folder / "data_example.json"

    for path, name in [(csv_path, "raw_data.csv"), (metadata_path, "metadata.json"), (data_example_path, "data_example.json")]:
        if not path.exists():
            raise HTTPException(
                status_code=404, detail=f"{name} não encontrado")

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    with open(data_example_path, "r", encoding="utf-8") as f:
        base_example = json.load(f)

    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    return df, metadata, base_example


def apply_filters(request, df):
    # Aplicação de filtros
    grouped_filters = defaultdict(list)
    for key, value in request.query_params.multi_items():
        if key.startswith("nome_option_f"):
            grouped_filters[key.strip()].append(value.strip())
    applyed_filters = []
    # grouped_filters  {'nome_option_f3': ['Centro Oeste', 'Nordeste'], 'nome_option_f7': ['2011', '2014']}

    # Aplica TODOS os filtros
    for param_name, raw_values in grouped_filters.items():

        id_filtro = int(param_name.replace("nome_option_f", ""))
        filter_column = param_name

        values = [v for v in raw_values if v]
        applyed_filters.append({"id_filtro": id_filtro, "id_option": values})
        # ex:  [{'id_filtro': 7, 'id_option': ['2016', '2017']}]

        # transforma os valores a serem filtrados para string
        filter_values = [str(v) for v in values]
        # transforma a coluna do dataframe em string
        df_column = df[filter_column].astype(str)

        # checa se todos são numericos e permite apenas um ponto decimal (ex: 2020.0)
        if all(v.replace('.', '', 1).isdigit() for v in values):
            try:
                # se conseguir converter faz a filtragem como numero
                numeric_values = [float(v) for v in values]
                df_column = pd.to_numeric(
                    df[filter_column], errors='coerce')
                filter_values = numeric_values
            except ValueError:
                pass

        # Aplica o filtro atual ao df (Lógica AND)
        # Resumo: Pega somente as linhas onde a coluna está nos valores escolhidos e não é nula.
        df = df[df_column.isin(filter_values) & df_column.notnull()]

    return applyed_filters, df


def build_series_simples(df, metadata, base_example, applyed_filters, xAxis_field, value_field):
    # 1. Cópia limpa e AGREGAÇÃO ISOLADA (APENAS POR EIXO X)
    df_temp = df.copy()
    df_temp = df_temp.reset_index(drop=True)

    # Agregação segura (apenas pelo Eixo X)
    df_grouped = (
        df_temp
        .groupby([xAxis_field], as_index=False)
        .agg({value_field: "sum"})
    )

    # ordena pelo eixo x
    df = df_grouped.sort_values(xAxis_field)

    # 2. Construção da Série (com df limpo e agregado)
    example = base_example.copy()
    example["applyed_filters"] = applyed_filters

    # pega todos os valores únicos da coluna identificada como eixo X (ano)
    x_axis = df[xAxis_field].unique().tolist()
    example["option_echarts"]["xAxis"]["data"] = x_axis

    pontos = []
    for i, row in df.iterrows():
        # Usa o índice da iteração para construir a coordenada [X, Y]
        pontos.append([i, float(row[value_field])])

    # pega o campo series pra padronizar a construção das series
    series_item = base_example["option_echarts"]["series"][0].copy() \
        if base_example.get("option_echarts", {}).get("series") else {}

    series = [{
        "id": series_item.get("id", "1"),
        "type": series_item.get("type", "line"),
        "name": metadata.get("nome", "Valor Único"),
        "data": pontos,
        "lineStyle": series_item.get("lineStyle", {}),
        "itemStyle": series_item.get("itemStyle", {})
    }]

    return series, example


def build_series_multipla(df, base_example, applyed_filters, xAxis_field, category_field, value_field):
    # 1. Cópia limpa e limpeza do indice
    df_temp = df.copy()
    df_temp = df_temp.reset_index(drop=True)

    group_cols = [xAxis_field, category_field]

    # 2. Agregação segura (obrigatoriamente por Ano e Categoria)
    df_grouped = (
        df_temp
        .groupby(group_cols, as_index=False)
        .agg({value_field: "sum"})
    )
    # ordenando por ano
    df = df_grouped.sort_values(xAxis_field)

    # 3. Construção da Série
    example = base_example.copy()
    example["applyed_filters"] = applyed_filters

    # pega todos os valores únicos da coluna identificada como eixo X (ano)
    x_axis = df[xAxis_field].unique().tolist()
    example["option_echarts"]["xAxis"]["data"] = x_axis

    series = []

    # percorrendo as categorias
    for category in df[category_field].unique():
        # seleciona apenas as linhas dessa categoria
        sub = df[df[category_field] == category]

        # construção dos pontos da serie
        pontos = []
        for _, row in sub.iterrows():
            x_index = x_axis.index(row[xAxis_field])
            pontos.append([x_index, float(row[value_field])])
            # [xIndex, valor]

        # pega o campo series pra padronizar a construção das series
        series_item = base_example["option_echarts"]["series"][0].copy(
        ) if base_example.get("option_echarts", {}).get("series") else {}

        series.append({
            "id": series_item.get("id", str(len(series) + 1)),
            "type": series_item.get("type", "line"),
            "name": str(category),
            "data": pontos,
            "lineStyle": series_item.get("lineStyle", {}),
            "itemStyle": series_item.get("itemStyle", {})
        })

    return series, example
