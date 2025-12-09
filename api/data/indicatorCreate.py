import shutil
import json
from pathlib import Path

# --- CONFIGURAÇÃO ---
# Defina o diretório onde as pastas ind_ estão localizadas
# Se as pastas estiverem na raiz do seu projeto, use o path correto.
DATA_DIR = Path(".")

# Lista de IDs base a serem duplicados
BASE_INDICATORS = [1299, 4445, 4885, 6220, 6588]  # 5 Indicadores

# Número de vezes que cada conjunto de base deve ser duplicado (5 * 6 = 30 novos)
NUM_ITERATIONS = 6

# ID inicial para as novas pastas (ind_7020, ind_7021, etc.)
CURRENT_ID = 8020

# --- LÓGICA DE POPULAÇÃO ---
print(f"Iniciando a duplicação a partir do ID: {CURRENT_ID}")
print(
    f"Total de {len(BASE_INDICATORS) * NUM_ITERATIONS} novos indicadores a serem criados.")

for i in range(NUM_ITERATIONS):
    for base_id in BASE_INDICATORS:
        source_dir = DATA_DIR / f"ind_{base_id}"
        new_dir = DATA_DIR / f"ind_{CURRENT_ID}"

        if not source_dir.exists():
            print(
                f"ATENÇÃO: Pasta de origem {source_dir} não encontrada. Pulando...")
            continue

        # 1. Duplica o diretório completo
        shutil.copytree(source_dir, new_dir, dirs_exist_ok=True)

        # 2. Atualiza o metadata.json
        metadata_path = new_dir / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # Altera os campos conforme solicitado:
            metadata["data"] = f"/get_dados_view/{CURRENT_ID}/"
            metadata["id"] = CURRENT_ID

            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=4)

            print(f" -> Criado e atualizado: {new_dir} (ID: {CURRENT_ID})")

        else:
            print(f"ERRO: metadata.json não encontrado em {new_dir}")

        # Incrementa o ID para a próxima pasta
        CURRENT_ID += 1

print("\nProcesso concluído! Pastas de teste criadas com sucesso.")
