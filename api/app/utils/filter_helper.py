from collections import defaultdict
import json
from fastapi import HTTPException
import pandas as pd


def return_df_empty(base_example, metadata, applyed_filters):
    example = base_example.copy()
    example["applyed_filters"] = applyed_filters
    example["option_echarts"]["xAxis"] = {"data": []}
    example["option_echarts"]["series"] = []
    example["data_criacao"] = pd.Timestamp.now().strftime(
        "%Y-%m-%d %H:%M:%S")
    return {"metadata": metadata, "data_example": example}


def load_files(DATA_DIR, indicator_id, ):
    # 1. SETUP E CARREGAMENTO DE ARQUIVOS (Omitido por brevidade)
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
    # 2. APLICAÇÃO DE FILTROS (Omitido por brevidade)
    grouped_filters = defaultdict(list)
    for key, value in request.query_params.multi_items():
        if key.startswith("nome_option_f"):
            grouped_filters[key.strip()].append(value.strip())
    applyed_filters = []

    # Aplica TODOS os filtros
    for param_name, raw_values in grouped_filters.items():
        try:
            id_filtro = int(param_name.replace("nome_option_f", ""))
        except ValueError:
            continue
        filter_column = param_name
        if filter_column not in df.columns:
            continue
        values = [v for v in raw_values if v]
        applyed_filters.append({"id_filtro": id_filtro, "id_option": values})
        filter_values = [str(v) for v in values]
        df_column = df[filter_column].astype(str)
        if all(v.replace('.', '', 1).isdigit() for v in values):
            try:
                numeric_values = [float(v) for v in values]
                df_column = pd.to_numeric(
                    df[filter_column], errors='coerce')
                filter_values = numeric_values
            except ValueError:
                pass
        # Aplica o filtro atual ao df (Lógica AND)
        df = df[df_column.isin(filter_values) & df_column.notnull()]

    return applyed_filters, df


def build_series_simples(df, metadata, base_example, applyed_filters, xAxis_field, value_field):
    print('\n\n\n\nn\e simples')

    # 1. Cópia limpa e AGREGAÇÃO ISOLADA (APENAS POR EIXO X)
    df_temp = df.copy()
    df_temp = df_temp.reset_index(drop=True)  # Limpa índice fantasma

    # Agregação segura (apenas pelo Eixo X)
    df_grouped = (
        df_temp
        .groupby([xAxis_field], as_index=False)
        .agg({value_field: "sum"})
    )
    df = df_grouped.sort_values(xAxis_field)

    # 2. Construção da Série (com df limpo e agregado)
    example = base_example.copy()
    example["applyed_filters"] = applyed_filters

    x_axis = df[xAxis_field].unique().tolist()
    example["option_echarts"]["xAxis"]["data"] = x_axis

    pontos = []
    for i, row in df.iterrows():
        # Usamos o índice da iteração para construir a coordenada [X, Y]
        pontos.append([i, float(row[value_field])])

    series_item = base_example["option_echarts"]["series"][0].copy() \
        if base_example.get("option_echarts", {}).get("series") else {}

    series = [{
        "id": series_item.get("id", "1"),
        "type": series_item.get("type", "line"),
        "name": metadata.get("nome", "Valor Único"),
        "data": pontos,  # FORMATO COORDENADO UNIVERSAL
        "lineStyle": series_item.get("lineStyle", {}),
        "itemStyle": series_item.get("itemStyle", {})
    }]

    return series, example


def build_series_multipla(df, metadata, base_example, applyed_filters, xAxis_field, category_field, value_field):
    print('e multipla')
    # 1. Cópia limpa e LIMPEZA TOTAL DO ÍNDICE
    df_temp = df.copy()
    # 💥 CORREÇÃO DEFINITIVA: Limpar o índice antes de agrupar para evitar o erro "cannot insert ano"
    df_temp = df_temp.reset_index(drop=True)

    # 2. Agregação segura (obrigatoriamente por Ano e Categoria)
    group_cols = [xAxis_field, category_field]

    df_grouped = (
        df_temp
        .groupby(group_cols, as_index=False)
        .agg({value_field: "sum"})
    )
    df = df_grouped.sort_values(xAxis_field)

    # 3. Construção da Série
    example = base_example.copy()
    example["applyed_filters"] = applyed_filters

    x_axis = df[xAxis_field].unique().tolist()
    example["option_echarts"]["xAxis"]["data"] = x_axis

    series = []

    for category in df[category_field].unique():
        sub = df[df[category_field] == category]

        pontos = []
        for _, row in sub.iterrows():
            x_index = x_axis.index(row[xAxis_field])
            pontos.append([x_index, float(row[value_field])])

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
