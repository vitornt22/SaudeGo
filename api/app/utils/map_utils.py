import pandas as pd


def is_map_indicator(metadata: dict, base_example: dict) -> bool:
    # Retorna True se for gráfico de mapa, False caso contrário.
    return (
        "visualMap" in base_example.get("option_echarts", {}) or
        ("viz" in metadata and "mapa" in metadata["viz"].lower())
    )


def process_map_indicator(df, metadata, base_example, applyed_filters):
    """
    Processa o DataFrame para o formato de Mapa (GeoJSON data array), 
    garantindo a agregação por município e a correta identificação dos campos.
    """
    example = base_example.copy()

    # Adiciona o filtro de tipo_parto="Vaginal"
    # Assumimos que o DataFrame (df) JÁ foi filtrado. Esta é a documentação do filtro.
    updated_filters = applyed_filters.copy()

    new_filter = {"id_filtro": "tipo_parto", "id_option": ["Vaginal"]}

    # Adiciona o filtro se ele ainda não estiver na lista (prevenção de duplicação)
    if not any(f.get("id_filtro") == new_filter["id_filtro"] for f in updated_filters):
        updated_filters.append(new_filter)

    example["applyed_filters"] = updated_filters

    # 1. Tenta identificar os campos de nome (município) e valor.
    name_field, value_field = serie_map_organize(df, example, metadata)

    # 2. PREPARAÇÃO DO DF
    df[value_field] = pd.to_numeric(df[value_field], errors="coerce")
    df = df.dropna(subset=[name_field, value_field])

    # 3. AGREGAÇÃO POR MUNICÍPIO
    # Agrupa pelo nome do município (name_field) e soma o campo de valor (value_field)
    df_grouped = (
        df
        .groupby([name_field], as_index=False)
        .agg({value_field: "sum"})
    )

    # 4. CONSTRUÇÃO DA SÉRIE
    example = build_map_series(df_grouped, example, name_field, value_field)

    example["data_criacao"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    return {"metadata": metadata, "data_example": example}


def build_map_series(df, example, name_field, value_field):
    """
    Constrói o array de dados do mapa (formato: [{"name": nome, "value": valor}, ...])
    e Atualiza a série do Echarts com os dados e calcula min/max para visualMap
    """
    map_data = []

    # Itera sobre o DataFrame JÁ AGRUPADO
    for _, row in df.iterrows():
        map_data.append({
            "name": str(row[name_field]),
            "value": float(row[value_field])
        })

    # Construindo a series para plotagem
    if example["option_echarts"]["series"]:
        example["option_echarts"]["series"][0]["data"] = map_data

        # Atualiza min/max para garantir que o visualMap esteja correto
        values = [d['value'] for d in map_data]
        if values:
            if "visualMap" in example["option_echarts"]:
                example["option_echarts"]["visualMap"]["min"] = min(values)
                example["option_echarts"]["visualMap"]["max"] = max(values)
            else:
                # Adiciona visualMap simples se não existir (para o frontend)
                example["option_echarts"]["visualMap"] = {
                    "min": min(values),
                    "max": max(values)
                }
    return example


def serie_map_organize(df, example, metadata):
    """
    Lógica para identificar as colunas essenciais para um mapa
    """
    df_cols = df.columns.tolist()

    # 1. Detecção do campo de NOME: Prioriza nome_option_f1
    name_field = next(
        (c for c in df_cols if "nome_option_f1" in c.lower()), df_cols[0])

    # Value_field Inclui 'qtde' e 'quantidade'
    value_field = next(
        (c for c in df_cols
         if "val" in c.lower() or "quant" in c.lower() or "qtd" in c.lower() or "tx" in c.lower() or "prop" in c.lower()
         or "quantidade" in c.lower() or "qtde" in c.lower()),  # Adicionado 'qtde' e 'quantidade'
        df_cols[-1]
    )

    if name_field not in df_cols or value_field not in df_cols:
        raise ValueError(
            f"Campos essenciais '{name_field}' ou '{value_field}' não encontrados no DataFrame para o Mapa.")

    return name_field, value_field
