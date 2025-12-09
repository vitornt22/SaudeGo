
import pandas as pd


def process_map_indicator(df, metadata, base_example, applyed_filters):
    """
    Processa o DataFrame para o formato de Mapa (GeoJSON data array).
    """
    example = base_example.copy()
    example["applyed_filters"] = applyed_filters

    df_cols = df.columns.tolist()

    # Heurística para Mapa: Assume-se que o nome do Município está na primeira coluna
    # e o valor está na última ou na coluna 'tx'/'quant'.
    name_field = next((c for c in df_cols if "mun" in c.lower()
                      or "nome" in c.lower()), df_cols[0])
    value_field = next((c for c in df_cols if "val" in c.lower() or "quant" in c.lower(
    ) or "tx" in c.lower() or "prop" in c.lower()), df_cols[-1])

    if name_field not in df_cols or value_field not in df_cols:
        # Se os campos essenciais não existirem, retorna vazio
        example["option_echarts"]["series"] = []
        return {"metadata": metadata, "data_example": example}

    # 1. PREPARAÇÃO FINAL DO DF (Mapas não usam XAxis, mas precisam do valor numérico)
    df[value_field] = pd.to_numeric(df[value_field], errors="coerce")
    df = df.dropna(subset=[name_field, value_field])

    # 2. Constrói o array de dados do mapa (formato: [{"name": nome, "value": valor}, ...])
    map_data = []
    for _, row in df.iterrows():
        map_data.append({
            "name": str(row[name_field]),
            "value": float(row[value_field])
        })

    # 3. Atualiza a série do Echarts com os dados e calcula min/max para visualMap
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

    example["data_criacao"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    return {"metadata": metadata, "data_example": example}
