from collections import defaultdict
import pandas as pd


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
