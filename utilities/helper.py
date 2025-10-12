import os, sys
from os.path import dirname as up

sys.path.append(os.path.abspath(os.path.join(up(__file__), os.pardir)))

import yaml
import pandas as pd
import os
import logging

# logging configuration
logger = logging.getLogger('model_building')
logger.setLevel('DEBUG')

console_handler = logging.StreamHandler()
console_handler.setLevel('DEBUG')

file_handler = logging.FileHandler('model_building_errors.log')
file_handler.setLevel('ERROR')

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)


def load_params(params_path: str) -> dict:
    """Load parameters from a YAML file."""
    try:
        with open(params_path, 'r') as file:
            params = yaml.safe_load(file)
        logger.debug('Parameters retrieved from %s', params_path)
        return params
    except FileNotFoundError:
        logger.error('File not found: %s', params_path)
        raise
    except yaml.YAMLError as e:
        logger.error('YAML error: %s', e)
        raise
    except Exception as e:
        logger.error('Unexpected error: %s', e)
        raise

def load_data(data_path: str) -> pd.DataFrame:
    """Load data from a CSV file."""
    try:
        df = pd.read_csv(data_path)
        logger.debug('Data loaded from %s', data_path)
        return df
    except pd.errors.ParserError as e:
        logger.error('Failed to parse the CSV file: %s', e)
        raise
    except Exception as e:
        logger.error('Unexpected error occurred while loading the data: %s', e)
        raise

def save_data(train_data: pd.DataFrame, val_data: pd.DataFrame, test_data: pd.DataFrame, data_path: str) -> None:
    """Save the processed train, validation, and test datasets."""
    try:
 
        os.makedirs(data_path, exist_ok=True)  # Ensure the directory is created

        if data_path == "data/raw":
            train_data.to_csv(os.path.join(data_path, "train.csv"), index=False)
            val_data.to_csv(os.path.join(data_path, "val.csv"), index=False)
            test_data.to_csv(os.path.join(data_path, "test.csv"), index=False)
        elif data_path == "data/interim":
            train_data.to_csv(os.path.join(data_path, "train_processed.csv"), index=False)
            val_data.to_csv(os.path.join(data_path, "val_processed.csv"), index=False)
            test_data.to_csv(os.path.join(data_path, "test_processed.csv"), index=False)
        
        logger.debug(f"Processed data saved to {data_path}")
    except Exception as e:
        logger.error(f"Error occurred while saving data: {e}")
        raise


def get_root_directory() -> str:
    """Get the root directory (two levels up from this script's location)."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(current_dir, '../../'))