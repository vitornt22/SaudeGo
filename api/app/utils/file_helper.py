import json
from pathlib import Path
from fastapi import HTTPException
import pandas as pd


def load_indicator_files(DATA_DIR, indicator_id):
    folder = DATA_DIR / f"ind_{indicator_id}"
    csv_path = folder / "raw_data.csv"
    metadata_path = folder / "metadata.json"
    example_path = folder / "data_example.json"

    for path, name in [(csv_path, "raw_data.csv"), (metadata_path, "metadata.json"), (example_path, "data_example.json")]:
        if not path.exists():
            raise HTTPException(
                status_code=404, detail=f"{name} não encontrado")

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    with open(example_path, "r", encoding="utf-8") as f:
        base_example = json.load(f)

    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()

    return df, metadata, base_example


def prepare_df(df, x_field, value_field):
    df[x_field] = pd.to_numeric(df[x_field], errors="coerce")
    df[value_field] = pd.to_numeric(df[value_field], errors="coerce")
    df = df.dropna(subset=[x_field, value_field])
    return df.sort_values(x_field)
