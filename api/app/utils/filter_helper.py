from collections import defaultdict
import pandas as pd


def extract_grouped_filters(request):
    grouped = defaultdict(list)
    for key, value in request.query_params.multi_items():
        if key.startswith("nome_option_f"):
            grouped[key.strip()].append(value.strip())
    return grouped


def apply_filters(df, grouped_filters):
    applyed_filters = []

    # parte de aplicação das filtragem com os options passados via queryString
    for param_name, raw_values in grouped_filters.items():
        # o id recebe a parte numerica que representa o id do indicador
        try:
            id_filtro = int(param_name.replace("nome_option_f", ""))
        except ValueError:
            continue

        filter_column = param_name

        # checa se  o padrão de nome_option_f{id_filtro} existe no csv
        if filter_column not in df.columns:
            continue

        # percorre todos os valores de cada coluna de filtragem
        values = [v for v in raw_values if v]

        # adiciona os ids dos filtros e os valores escolhidos no applyed_filters
        # isso permite que depois seja retornado no data_example.json
        applyed_filters.append({"id_filtro": id_filtro, "id_option": values})

        # Prepara para filtragem: default é STRING
        filter_values = [str(v) for v in values]
        df_column = df[filter_column].astype(str)

        # Trata como Numérico se os valores forem dígitos
        if all(v.replace('.', '', 1).isdigit() for v in values):
            try:
                numeric_values = [float(v) for v in values]
                df_column = pd.to_numeric(
                    df[filter_column], errors='coerce')
                filter_values = numeric_values
            except ValueError:
                pass

        # Aplica o filtro: .isin(filter_values) aplica a lógica OR (OU) para a coluna
        df = df[df_column.isin(filter_values) & df_column.notnull()]
        return df, applyed_filters


def detect_series(df, base_example, metadata):
    example = base_example.copy()

    # DETECÇÃO DE CAMPOS PARA GRÁFICO DE LINHA/SÉRIE HISTÓRICA
    xAxis_field = base_example["option_echarts"].get("campo")
    category_field = base_example["option_echarts"].get("campo_categoria")
    value_field = base_example["option_echarts"].get("campo_valor")

    # Lista todas as colunas do dataframe
    df_cols = df.columns.tolist()

    # Lógica para Eixo X
    if not xAxis_field or xAxis_field not in df_cols:
        xAxis_field = next(
            (c for c in df_cols if "ano" in c.lower()), df_cols[0])

    # A logica geral para identificar as series com base nos identificadores
    # repassados, é pegar os campos referentes a categoria (cat, faixa) e valor/quantidade

    #  Lógica para Categoria
    if not category_field or category_field not in df_cols:
        category_field = next((c for c in df_cols if "cat" in c.lower(
        ) or "faixa" in c.lower()), df_cols[1] if len(df_cols) > 1 else "categoria_default")

    # Logica para  Valor
    if not value_field or value_field not in df_cols:
        value_field = next((c for c in df_cols if "val" in c.lower(
        ) or "quant" in c.lower() or "tx" in c.lower()), df_cols[-1])

    # Validação
    if xAxis_field not in df_cols or value_field not in df_cols:
        example["option_echarts"]["xAxis"] = {"data": []}
        example["option_echarts"]["series"] = []
        example["data_criacao"] = pd.Timestamp.now().strftime(
            "%Y-%m-%d %H:%M:%S")
        return {"metadata": metadata, "data_example": example}

    # organização final do dataframe
    df[xAxis_field] = pd.to_numeric(df[xAxis_field], errors="coerce")
    df[value_field] = pd.to_numeric(df[value_field], errors="coerce")
    df = df.dropna(subset=[xAxis_field, value_field])
    df = df.sort_values(xAxis_field)

    return xAxis_field, category_field, value_field


def build_single_serie(df, base_example, series, metadata, value_field):
    # SÉRIE ÚNICA
    pontos_data = df[value_field].tolist()
    series_item = base_example["option_echarts"]["series"][0].copy(
    ) if base_example["option_echarts"]["series"] else {}

    series.append({
        "id": series_item.get("id", "1"),
        "type": series_item.get("type", "line"),
        "name": metadata.get("nome", "Valor Único"),
        "data": pontos_data,
        "lineStyle": series_item.get("lineStyle", {}),
        "itemStyle": series_item.get("itemStyle", {})
    })
    return series


def build_multiple_series(df,  series, x_axis, xAxis_field, category_field, value_field):
    for category in df[category_field].unique():
        sub = df[df[category_field] == category]
        pontos = [[x_axis.index(row[xAxis_field]), float(
            row[value_field])] for _, row in sub.iterrows()]
        series.append({
            "type": "line",
            "name": str(category),
            "data": pontos,
            "lineStyle": {},
            "itemStyle": {}
        })
    return series


def build_series(df, base_example, applyed_filters, xAxis_field, category_field, metadata, value_field):
    example = base_example.copy()
    example["applyed_filters"] = applyed_filters
    x_axis = df[xAxis_field].unique().tolist()
    example["option_echarts"]["xAxis"]["data"] = x_axis

    series = []
    is_single_series = (
        category_field not in df.columns or df[category_field].nunique() <= 1)

    if is_single_series:
        series = build_single_serie(
            df, base_example, series, metadata, value_field)
    else:
        series = build_multiple_series(
            df=df,
            series=series,
            x_axis=x_axis,
            xAxis_field=xAxis_field,
            category_field=category_field,
            value_field=value_field
        )
    return series, example
