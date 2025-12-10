from fastapi import APIRouter, HTTPException, Request
from fastapi import APIRouter, HTTPException
import json
from fastapi import Request
import pandas as pd
from pathlib import Path
from collections import defaultdict

from app.utils.filter_helper import apply_filters, build_series_multipla, build_series_simples, detect_validation_fields, is_multi_series, load_files, return_df_empty

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
    # Carregando os arquivos
    df, metadata, base_example = load_files(DATA_DIR, indicator_id)

    # aplicando filtros pela queryString
    applyed_filters, df = apply_filters(request, df)

    # Retorna o df vazio caso nao haja resultados na filtragem
    if df.empty:
        example = return_df_empty(base_example, applyed_filters)
        return {"metadata": metadata, "data_example": example}

    # chama a função especifica pra retorno de mapa caso o tipo de chart seja esse
    if is_map_indicator(metadata, base_example):
        return process_map_indicator(df, metadata, base_example, applyed_filters)

    # Detecção dos campos para validação
    xAxis_field, value_field, category_field = detect_validation_fields(
        df, base_example, applyed_filters, metadata)

    # Prepara o DF com tipos numéricos antes de qualquer agregação nas funções auxiliares
    df[xAxis_field] = pd.to_numeric(df[xAxis_field], errors="coerce")
    df[value_field] = pd.to_numeric(df[value_field], errors="coerce")
    df = df.dropna(subset=[xAxis_field, value_field])

    # Preparando o retorno correto com base no tipo de série (simples ou multipla)
    if is_multi_series(metadata):
        series, example = build_series_multipla(
            df=df, base_example=base_example, applyed_filters=applyed_filters,
            xAxis_field=xAxis_field, category_field=category_field, value_field=value_field
        )
    else:
        series, example = build_series_simples(
            df=df, metadata=metadata, base_example=base_example, applyed_filters=applyed_filters,
            xAxis_field=xAxis_field, value_field=value_field
        )

    # cria o novo "data_example pra plotar o chart no frontend"
    example["option_echarts"]["series"] = series
    example["data_criacao"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    return {"metadata": metadata, "data_example": example}
