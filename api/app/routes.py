from fastapi import APIRouter, HTTPException, Request
from fastapi import APIRouter, HTTPException
import json
from fastapi import Request
import pandas as pd
from pathlib import Path

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

    # Verifica arquivos (Lógica de 404 mantida)
    for path, name in [(csv_path, "raw_data.csv"), (metadata_path, "metadata.json"), (data_example_path, "data_example.json")]:
        if not path.exists():
            raise HTTPException(
                status_code=404, detail=f"{name} não encontrado")

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    with open(data_example_path, "r", encoding="utf-8") as f:
        base_example = json.load(f)

    df = pd.read_csv(csv_path)

    # 🛠️ CORREÇÃO CRÍTICA 1: Limpa os nomes das colunas (evita erro com 'nome_option_f10 ')
    df.columns = df.columns.str.strip()

    applyed_filters = []

    # 2. FILTRAGEM DINÂMICA E SEGURA (TIPAGEM)
    for param_name, param_value in request.query_params.items():
        if not param_name.startswith("nome_option_f"):
            continue

        try:
            id_filtro = int(param_name.replace("nome_option_f", ""))
        except ValueError:
            continue

        coluna_para_filtrar = param_name.strip()

        if coluna_para_filtrar not in df.columns:
            continue

        # Limpeza dos valores de filtro (remove espaços e separa por vírgula)
        values = [v.strip() for v in param_value.split(",") if v.strip()]
        applyed_filters.append({"id_filtro": id_filtro, "id_option": values})

        # Prepara para filtragem: default é STRING
        filter_values = [str(v) for v in values]
        df_column = df[coluna_para_filtrar].astype(str)

        # 🛠️ CORREÇÃO CRÍTICA 2: Trata como Numérico se os valores forem dígitos
        if all(v.replace('.', '', 1).isdigit() for v in values):
            try:
                numeric_values = [float(v) for v in values]
                # Converte a coluna do DF para numérica para comparação exata de float
                df_column = pd.to_numeric(
                    df[coluna_para_filtrar], errors='coerce')
                filter_values = numeric_values
            except ValueError:
                # Mantém como string se a conversão falhar inesperadamente
                pass

        # Aplica o filtro (ignora NaNs)
        df = df[df_column.isin(filter_values) & df_column.notnull()]

    example = base_example.copy()
    example["applyed_filters"] = applyed_filters

    if df.empty:
        example["option_echarts"]["xAxis"]["data"] = []
        example["option_echarts"]["series"] = []
        example["data_criacao"] = pd.Timestamp.now().strftime(
            "%Y-%m-%d %H:%M:%S")
        return {"metadata": metadata, "data_example": example}

    # 3. DETECÇÃO DINÂMICA DOS CAMPOS DO GRÁFICO (Heurística Universal)
    xAxis_field = base_example["option_echarts"].get("campo")
    category_field = base_example["option_echarts"].get("campo_categoria")
    value_field = base_example["option_echarts"].get("campo_valor")

    df_cols = df.columns.tolist()

    # Eixo X: Prioriza 'ano' ou a primeira coluna
    if not xAxis_field or xAxis_field not in df_cols:
        xAxis_field = next(
            (c for c in df_cols if "ano" in c.lower()), df_cols[0])

    # Categoria: Prioriza 'faixa_etaria', 'cat' ou a segunda coluna
    if not category_field or category_field not in df_cols:
        category_field = next((c for c in df_cols if "cat" in c.lower(
        ) or "faixa" in c.lower()), df_cols[1] if len(df_cols) > 1 else "categoria_default")

    # Valor: Prioriza 'quantidade', 'val', 'tx' ou a última coluna
    if not value_field or value_field not in df_cols:
        value_field = next((c for c in df_cols if "val" in c.lower(
        ) or "quant" in c.lower() or "tx" in c.lower()), df_cols[-1])

    if xAxis_field not in df_cols or value_field not in df_cols:
        # Retorna vazio se os campos essenciais para o gráfico não forem encontrados
        example["option_echarts"]["xAxis"]["data"] = []
        example["option_echarts"]["series"] = []
        example["data_criacao"] = pd.Timestamp.now().strftime(
            "%Y-%m-%d %H:%M:%S")
        return {"metadata": metadata, "data_example": example}

    # 4. PREPARAÇÃO FINAL DO DF
    df[xAxis_field] = pd.to_numeric(df[xAxis_field], errors="coerce")
    df[value_field] = pd.to_numeric(df[value_field], errors="coerce")
    df = df.dropna(subset=[xAxis_field, value_field])
    df = df.sort_values(xAxis_field)

    # 5. CONSTRUÇÃO DINÂMICA DA SÉRIE
    x_axis = df[xAxis_field].unique().tolist()
    example["option_echarts"]["xAxis"]["data"] = x_axis

    series = []

    # Condição para tratar Série Única (4445, 4885, 6588) ou Múltiplas Séries (1299, 1288)
    is_single_series = (
        category_field not in df.columns or df[category_field].nunique() <= 1)

    if is_single_series:
        # SÉRIE ÚNICA: Lista simples de valores Y
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
        # MÚLTIPLAS SÉRIES: Pares [index_x, valor_y]
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
