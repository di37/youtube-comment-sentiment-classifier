# Register model to MLflow Model Registry
# Note: Uses aliases instead of deprecated stages (MLflow 2.9+)
# Aliases provide flexible model version management (e.g., 'staging', 'production', 'champion')
# Load models using: mlflow.pyfunc.load_model(f"models:/{model_name}@{alias}")

import os, sys
from os.path import dirname as up

sys.path.append(os.path.abspath(os.path.join(up(__file__), os.pardir)))

import json
import mlflow
import logging
import os

# Set up MLflow tracking URI
mlflow.set_tracking_uri("http://3.29.129.159:5000/")

from dotenv import load_dotenv
load_dotenv()

# Set AWS credentials (replace with your actual credentials)
os.environ['AWS_ACCESS_KEY_ID'] = os.getenv('AWS_ACCESS_KEY_ID')
os.environ['AWS_SECRET_ACCESS_KEY'] = os.getenv('AWS_SECRET_ACCESS_KEY')
os.environ['AWS_DEFAULT_REGION'] = os.getenv('AWS_DEFAULT_REGION')



# logging configuration
logger = logging.getLogger('model_registration')
logger.setLevel('DEBUG')

console_handler = logging.StreamHandler()
console_handler.setLevel('DEBUG')

file_handler = logging.FileHandler('model_registration_errors.log')
file_handler.setLevel('ERROR')

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

def load_model_info(file_path: str) -> dict:
    """Load the model info from a JSON file."""
    try:
        with open(file_path, 'r') as file:
            model_info = json.load(file)
        logger.debug('Model info loaded from %s', file_path)
        return model_info
    except FileNotFoundError:
        logger.error('File not found: %s', file_path)
        raise
    except Exception as e:
        logger.error('Unexpected error occurred while loading the model info: %s', e)
        raise

def register_model(model_name: str, model_info: dict, alias: str = "staging"):
    """Register the model to the MLflow Model Registry and set an alias.
    
    Args:
        model_name: Name to register the model under
        model_info: Dictionary containing 'run_id' and 'model_path' (artifact path)
        alias: Alias to assign to the model version (e.g., 'staging', 'production', 'champion')
    """
    try:
        # Construct the model URI in the format: runs:/<run_id>/<artifact_path>
        # Note: model_path should be just the artifact path (e.g., 'lgbm_model'), not the full S3 URI
        model_uri = f"runs:/{model_info['run_id']}/{model_info['model_path']}"
        
        logger.debug(f'Registering model with URI: {model_uri}')
        
        # Register the model
        model_version = mlflow.register_model(model_uri, model_name)
        
        # Set an alias for the model version (replaces the deprecated stage transition)
        client = mlflow.tracking.MlflowClient()
        client.set_registered_model_alias(
            name=model_name,
            alias=alias,
            version=model_version.version
        )
        
        logger.debug(f'Model {model_name} version {model_version.version} registered with alias "{alias}".')
        print(f'\n✓ Model registered successfully!')
        print(f'  - Model: {model_name}')
        print(f'  - Version: {model_version.version}')
        print(f'  - Alias: {alias}')
        print(f'  - Load URI: models:/{model_name}@{alias}\n')
    except Exception as e:
        logger.error('Error during model registration: %s', e)
        raise

def main():
    try:
        model_info_path = 'experiment_info.json'
        model_info = load_model_info(model_info_path)
        
        model_name = "yt_chrome_plugin_model"
        register_model(model_name, model_info)
    except Exception as e:
        logger.error('Failed to complete the model registration process: %s', e)
        print(f"Error: {e}")

if __name__ == '__main__':
    main()