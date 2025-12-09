from fastapi import APIRouter, HTTPException, Request
from fastapi import APIRouter, HTTPException
import json
from fastapi import Request
import pandas as pd
from pathlib import Path
from collections import defaultdict
from .utils import process_map_indicator


router = APIRouter()

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MAPS_DIR = Path(__file__).resolve().parent.parent / "data/maps"


def get_indicator_folders():
    # Retorna apenas os IDs após "ind_"
    return [p.name.split("_")[1] for p in DATA_DIR.iterdir() if p.is_dir() and p.name.startswith("ind_")]


@router.get("/maps/{map_name}")
def get_map(map_name: str):
    """
    Retorna um mapa GeoJSON baseado no nome enviado.
    Exemplo: /maps/GO_mac → retorna GO_mac.json
    """

    filename = f"{map_name}.json"
    map_path = MAPS_DIR / filename

    if not map_path.exists():
        raise HTTPException(status_code=404, detail="Mapa não encontrado")

    with open(map_path, "r", encoding="utf-8") as f:
        geojson = json.load(f)

    return geojson


# A função get_indicator_folders() não precisa mudar.
# Apenas a função list_indicators():

@router.get("/indicators")
def list_indicators(limit: int = 10, offset: int = 0):
    # Busca todos os IDs (rápido, pois só lê nomes de pastas)
    all_indicators = get_indicator_folders()
    total_count = len(all_indicators)

    # Aplica o fatiamento (slicing)
    # Ex: offset=10, limit=10 -> retorna indicadores do índice 10 ao 20
    start = offset
    end = offset + limit
    paginated_indicators = all_indicators[start:end]

    # Retorna os indicadores da página atual + metadados de paginação
    return {
        "indicators": paginated_indicators,
        "total": total_count,
        "limit": limit,
        "offset": offset,
    }


@router.get("/indicators/{indicator_id}")
def get_indicator(indicator_id: str):
    # It creates the fullname folder with prfix 'ind_'
    indicator_folder_name = f"ind_{indicator_id}"  # Ex: "ind_1299"

    # It uses the full name to verify if the folder exists
    if indicator_id not in get_indicator_folders():
        raise HTTPException(status_code=404, detail="Indicador não encontrado")

    # it uses the full name to build  the path
    indicator_path = DATA_DIR / indicator_folder_name

    with open(indicator_path / "metadata.json", "r") as f:
        metadata = json.load(f)

    with open(indicator_path / "data_example.json", "r") as f:
        data_example = json.load(f)

    return {"metadata": metadata, "data_example": data_example}


# NOTA: DATA_DIR e APIRouter devem ser definidos em seu arquivo principal
# Exemplo: DATA_DIR = Path("./dados")
# router = APIRouter()


@router.get("/indicators/{indicator_id}/filter")
def filter_indicator(indicator_id: str, request: Request):
    # 1. SETUP E VERIFICAÇÃO DE ARQUIVOS
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

    # 2. AGRUPAMENTO E FILTRAGEM (Lógica OR + AND)

    # 2.1. Agrupa os valores da query por nome do parâmetro
    grouped_filters = defaultdict(list)
    for key, value in request.query_params.multi_items():
        if key.startswith("nome_option_f"):
            grouped_filters[key.strip()].append(value.strip())

    applyed_filters = []

    # 2.2. Itera sobre os filtros agrupados e aplica a lógica OR
    for param_name, raw_values in grouped_filters.items():

        try:
            id_filtro = int(param_name.replace("nome_option_f", ""))
        except ValueError:
            continue

        coluna_para_filtrar = param_name

        if coluna_para_filtrar not in df.columns:
            continue

        values = [v for v in raw_values if v]
        applyed_filters.append({"id_filtro": id_filtro, "id_option": values})

        # Prepara para filtragem: default é STRING
        filter_values = [str(v) for v in values]
        df_column = df[coluna_para_filtrar].astype(str)

        # Trata como Numérico se os valores forem dígitos
        if all(v.replace('.', '', 1).isdigit() for v in values):
            try:
                numeric_values = [float(v) for v in values]
                df_column = pd.to_numeric(
                    df[coluna_para_filtrar], errors='coerce')
                filter_values = numeric_values
            except ValueError:
                pass

        # Aplica o filtro: .isin(filter_values) aplica a lógica OR (OU) para a coluna
        df = df[df_column.isin(filter_values) & df_column.notnull()]

    # 2.3. Verifica se o DF ficou vazio após o filtro
    if df.empty:
        example = base_example.copy()
        example["applyed_filters"] = applyed_filters
        example["option_echarts"]["xAxis"] = {"data": []}
        example["option_echarts"]["series"] = []
        example["data_criacao"] = pd.Timestamp.now().strftime(
            "%Y-%m-%d %H:%M:%S")
        return {"metadata": metadata, "data_example": example}

    # 3. DETECÇÃO DINÂMICA DO TIPO DE GRÁFICO
    is_map_indicator = (
        "visualMap" in base_example["option_echarts"] or
        ("viz" in metadata and "mapa" in metadata["viz"].lower())
    )

    if is_map_indicator:
        # Se for Mapa, usa a função auxiliar e retorna
        return process_map_indicator(df, metadata, base_example, applyed_filters)

    # 4. DETECÇÃO DE CAMPOS PARA GRÁFICO DE LINHA/SÉRIE HISTÓRICA
    xAxis_field = base_example["option_echarts"].get("campo")
    category_field = base_example["option_echarts"].get("campo_categoria")
    value_field = base_example["option_echarts"].get("campo_valor")

    df_cols = df.columns.tolist()

    # Heurística para Eixo X
    if not xAxis_field or xAxis_field not in df_cols:
        xAxis_field = next(
            (c for c in df_cols if "ano" in c.lower()), df_cols[0])

    # Heurística para Categoria
    if not category_field or category_field not in df_cols:
        category_field = next((c for c in df_cols if "cat" in c.lower(
        ) or "faixa" in c.lower()), df_cols[1] if len(df_cols) > 1 else "categoria_default")

    # Heurística para Valor
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

    # 5. PREPARAÇÃO FINAL DO DF
    df[xAxis_field] = pd.to_numeric(df[xAxis_field], errors="coerce")
    df[value_field] = pd.to_numeric(df[value_field], errors="coerce")
    df = df.dropna(subset=[xAxis_field, value_field])
    df = df.sort_values(xAxis_field)

    # 6. CONSTRUÇÃO DINÂMICA DA SÉRIE (Linha/Barra)
    example = base_example.copy()
    example["applyed_filters"] = applyed_filters
    x_axis = df[xAxis_field].unique().tolist()
    example["option_echarts"]["xAxis"]["data"] = x_axis

    series = []
    is_single_series = (
        category_field not in df.columns or df[category_field].nunique() <= 1)

    if is_single_series:
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
    else:
        # MÚLTIPLAS SÉRIES
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

    example["option_echarts"]["series"] = series
    example["data_criacao"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

    return {"metadata": metadata, "data_example": example}
