
import pandas as pd


def process_map_indicator(df, metadata, base_example, applyed_filters):
    """
    Processa o DataFrame para o formato de Mapa (GeoJSON data array).
    """
    example = base_example.copy()
    example["applyed_filters"] = applyed_filters

    name_field, value_field = serie_map_organize(df, example, metadata)

    # PREPARAÇÃO FINAL DO DF (Mapas não usam XAxis, mas precisam do valor numérico)
    df[value_field] = pd.to_numeric(df[value_field], errors="coerce")
    df = df.dropna(subset=[name_field, value_field])

    example = build_map_series(df, example, name_field, value_field)

    example["data_criacao"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    return {"metadata": metadata, "data_example": example}


def is_map_indicator(metadata: dict, base_example: dict) -> bool:
    # Retorna True se for gráfico de mapa, False caso contrário.
    return (
        "visualMap" in base_example.get("option_echarts", {}) or
        ("viz" in metadata and "mapa" in metadata["viz"].lower())
    )


def build_map_series(df, example, name_field, value_field):
    """
    Constrói o array de dados do mapa (formato: [{"name": nome, "value": valor}, ...])
    e Atualiza a série do Echarts com os dados e calcula min/max para visualMap
    """
    map_data = []
    for _, row in df.iterrows():
        map_data.append({
            "name": str(row[name_field]),
            "value": float(row[value_field])
        })

    # Construindo a series para plitagem
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

    df_cols = df.columns.tolist()
    # Logica para Mapa: Assume-se que o nome do Município está na primeira coluna
    # e o valor está na última ou na coluna 'tx'/'quant'.
    name_field = next((c for c in df_cols if "mun" in c.lower()
                      or "nome" in c.lower()), df_cols[0])
    value_field = next((c for c in df_cols if "val" in c.lower() or "quant" in c.lower(
    ) or "tx" in c.lower() or "prop" in c.lower()), df_cols[-1])

    if name_field not in df_cols or value_field not in df_cols:
        # Se os campos essenciais não existirem, retorna vazio
        example["option_echarts"]["series"] = []
        return {"metadata": metadata, "data_example": example}

    return name_field, value_field
