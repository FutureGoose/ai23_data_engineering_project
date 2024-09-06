import subprocess
import json
from pathlib import Path
from tqdm import tqdm

def run_bq_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {command}")
        print(result.stderr)
        return None
    return json.loads(result.stdout)


def save_json_to_file(data, file_path):
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=2)


def process_dataset(dataset, output_dir):
    tables = run_bq_command(f"bq ls --format=prettyjson {dataset}")
    if tables is None:
        return
    
    dataset_dir = output_dir / dataset
    dataset_dir.mkdir(exist_ok=True)
    
    for table in tqdm(tables, desc=f"Processing tables in {dataset}", leave=False):
        table_id = table['tableReference']['tableId']
        table_info = run_bq_command(f"bq show --format=prettyjson {dataset}.{table_id}")
        if table_info is not None:
            file_path = dataset_dir / f"{table_id}.json"
            save_json_to_file(table_info, file_path)


def list_datasets():
    datasets = run_bq_command("bq ls --format=prettyjson")
    if datasets is None:
        return []
    return [dataset['datasetReference']['datasetId'] for dataset in datasets]


def main():
    output_dir = Path("database_schemas")
    output_dir.mkdir(exist_ok=True)

    datasets = list_datasets()
    for dataset in tqdm(datasets, desc="Processing datasets"):
        process_dataset(dataset, output_dir)


if __name__ == "__main__":
    main()