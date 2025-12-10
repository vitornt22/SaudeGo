from fastapi import APIRouter, HTTPException, Request
from fastapi import APIRouter, HTTPException
import json
from fastapi import Request
import pandas as pd
from pathlib import Path
from collections import defaultdict

from api.app.utils.filter_helper import build_series_multipla, build_series_simples

from .utils.map_utils import is_map_indicator, process_map_indicator

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
    indicator_folder_name = f"ind_{indicator_id}"  # Ex: "ind_1299"

    # Verifica se a pasta existe
    if indicator_id not in get_indicator_folders():
        raise HTTPException(status_code=404, detail="Indicador não encontrado")

    indicator_path = DATA_DIR / indicator_folder_name

    with open(indicator_path / "metadata.json", "r") as f:
        metadata = json.load(f)

    with open(indicator_path / "data_example.json", "r") as f:
        data_example = json.load(f)

    return {"metadata": metadata, "data_example": data_example}


@router.get("/indicators/{indicator_id}/filter")
def filter_indicator(indicator_id: str, request: Request):
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

    # 2. APLICAÇÃO DE FILTROS (Omitido por brevidade)
    grouped_filters = defaultdict(list)
    for key, value in request.query_params.multi_items():
        if key.startswith("nome_option_f"):
            grouped_filters[key.strip()].append(value.strip())
    applyed_filters = []
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
        df = df[df_column.isin(filter_values) & df_column.notnull()]

    # 3. VERIFICAÇÃO DE DF VAZIO / DETECÇÃO DE MAPA
    if df.empty:
        example = base_example.copy()
        example["applyed_filters"] = applyed_filters
        example["option_echarts"]["xAxis"] = {"data": []}
        example["option_echarts"]["series"] = []
        example["data_criacao"] = pd.Timestamp.now().strftime(
            "%Y-%m-%d %H:%M:%S")
        return {"metadata": metadata, "data_example": example}
    if is_map_indicator(metadata, base_example):
        return process_map_indicator(df, metadata, base_example, applyed_filters)

    # 4. DETECÇÃO DE CAMPOS E VALIDAÇÃO
    xAxis_field = base_example["option_echarts"].get("campo")
    category_field = base_example["option_echarts"].get("campo_categoria")
    value_field = base_example["option_echarts"].get("campo_valor")
    df_cols = df.columns.tolist()

    if not xAxis_field or xAxis_field not in df_cols:
        xAxis_field = next(
            (c for c in df_cols if c == 'nome_option_f7' or "ano" in c.lower()), df_cols[0])
    if not category_field or category_field not in df_cols:
        category_field = next((c for c in df_cols if "cat" in c.lower(
        ) or "faixa" in c.lower()), df_cols[1] if len(df_cols) > 1 else "__NO_CATEGORY__")
    if not value_field or value_field not in df_cols:
        value_field = next((c for c in df_cols if "val" in c.lower(
        ) or "quant" in c.lower() or "tx" in c.lower()), df_cols[-1])

    if xAxis_field not in df_cols or value_field not in df_cols:
        example = base_example.copy()
        example["applyed_filters"] = applyed_filters
        example["option_echarts"]["xAxis"] = {"data": []}
        example["option_echarts"]["series"] = []
        example["data_criacao"] = pd.Timestamp.now().strftime(
            "%Y-%m-%d %H:%M:%S")
        return {"metadata": metadata, "data_example": example}

    # 5. CONDIÇÃO CENTRAL: DETECÇÃO DE TIPO
    viz_type = metadata.get("viz", "").lower()
    print("\n\n\n\n\n\nn\n\ viz type: ", viz_type, "\n\n\nn\n\n")

    # Se o metadata for SIMPLES, ou se não houver um category_field válido, é Simples.
    is_multi_series = ("multipla" in viz_type or "múltipla" in viz_type)

    # 6. ORQUESTRAÇÃO E CHAMADA ÀS FUNÇÕES AUXILIARES

    # Prepara o DF com tipos numéricos antes de qualquer agregação nas funções auxiliares
    df[xAxis_field] = pd.to_numeric(df[xAxis_field], errors="coerce")
    df[value_field] = pd.to_numeric(df[value_field], errors="coerce")
    df = df.dropna(subset=[xAxis_field, value_field])

    if is_multi_series:
        print('entrou if multipla')
        series, example = build_series_multipla(
            df=df, metadata=metadata, base_example=base_example, applyed_filters=applyed_filters,
            xAxis_field=xAxis_field, category_field=category_field, value_field=value_field
        )
    else:
        series, example = build_series_simples(
            df=df, metadata=metadata, base_example=base_example, applyed_filters=applyed_filters,
            xAxis_field=xAxis_field, value_field=value_field
        )

    example["option_echarts"]["series"] = series
    example["data_criacao"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

    return {"metadata": metadata, "data_example": example}

# 2. 🟢 Funções Auxiliares (Lógica Isolada)


# A. Função para Série Única (Agrega APENAS por Ano)

# Esta função força a agregação APENAS pelo Eixo X.
