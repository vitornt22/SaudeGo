from fastapi import APIRouter, HTTPException
import json
import pandas as pd
from pathlib import Path

router = APIRouter()

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def get_indicator_folders():
    # Retorna apenas os IDs após "ind_"
    return [p.name.split("_")[1] for p in DATA_DIR.iterdir() if p.is_dir() and p.name.startswith("ind_")]


@router.get("/indicators")
def list_indicators():
    indicators = get_indicator_folders()
    return {"indicators": indicators}


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


@router.get("/indicators/{indicator_id}/filter")
def filter_indicator(indicator_id: str, column: str, value: str):
    # CRIA o nome COMPLETO da pasta com o prefixo 'ind_'
    indicator_folder_name = f"ind_{indicator_id}"  # Ex: "ind_1299"

    # Usa o nome completo para verificar se a pasta existe
    if indicator_folder_name not in get_indicator_folders():
        raise HTTPException(status_code=404, detail="Indicador não encontrado")

    # Usa o nome completo para construir o caminho
    indicator_path = DATA_DIR / indicator_folder_name

    # ... restante do código permanece igual
    csv_file = indicator_path / "raw_data.csv"
    if not csv_file.exists():
        raise HTTPException(
            status_code=404, detail="Dados brutos não encontrados")

    df = pd.read_csv(csv_file)
    if column not in df.columns:
        raise HTTPException(status_code=400, detail="Coluna não encontrada")

    filtered = df[df[column] == value]
    return filtered.to_dict(orient="records")
