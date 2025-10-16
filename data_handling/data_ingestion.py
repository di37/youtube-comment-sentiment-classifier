import os, sys
from os.path import dirname as up

sys.path.append(os.path.abspath(os.path.join(up(__file__), os.pardir)))

from pathlib import Path
import shutil
import logging
import kagglehub

# Logging configuration
logger = logging.getLogger('data_ingestion')
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

file_handler = logging.FileHandler('errors.log')
file_handler.setLevel(logging.ERROR)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

def download_and_copy_dataset(dataset_name: str = "atifaliak/youtube-comments-dataset", 
                               raw_data_path: str = "data/raw") -> str:
    """
    Download dataset from Kaggle and copy to local directory.
    
    Args:
        dataset_name: Kaggle dataset identifier (default: "atifaliak/youtube-comments-dataset")
        raw_data_path: Local directory to store the dataset (default: "data/raw")
    
    Returns:
        str: Path to the CSV file, or None if not found or error occurred
    """
    # Create data/raw directory if it doesn't exist
    raw_data_dir = Path(raw_data_path)
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Download dataset to kagglehub cache
        cache_path = kagglehub.dataset_download(dataset_name)
        print("✓ Dataset downloaded successfully!")
        print(f"Cache location: {cache_path}\n")
        
        # Copy files from cache to data/raw
        print(f"Copying files to {raw_data_dir}/...")
        print("="*60)
        
        copied_files = []
        csv_files = []
        for item in Path(cache_path).rglob('*'):
            if item.is_file():
                # Get relative path to preserve directory structure
                rel_path = item.relative_to(cache_path)
                dest_path = raw_data_dir / rel_path

                # Create parent directories if needed
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(item, dest_path)
                file_size = item.stat().st_size / (1024 * 1024)  # MB
                copied_files.append(str(dest_path))
                print(f"  ✓ {rel_path} ({file_size:.2f} MB)")

                # Collect csv files
                if dest_path.suffix.lower() == '.csv':
                    csv_files.append(dest_path)
        
        print("="*60)
        print(f"✓ Successfully copied {len(copied_files)} file(s)")
        print(f"\nDataset saved to: {raw_data_dir.absolute()}")
        
        # Find the csv file path
        if len(csv_files) == 0:
            print("✗ No CSV file found in dataset.")
            csv_file_path = None
        elif len(csv_files) == 1:
            csv_file_path = str(csv_files[0])
            print(f"CSV file found: {csv_file_path}")
        else:
            print("Multiple CSV files found. Please select one:")
            for idx, fp in enumerate(csv_files):
                print(f"[{idx}]: {fp}")
            csv_file_path = str(csv_files[0])  # Default to first one
            print(f"Defaulting to: {csv_file_path}")
        
        logger.debug('Dataset downloaded and copied successfully to %s', raw_data_dir)
        return csv_file_path

    except Exception as e:
        logger.error('Error downloading dataset: %s', e)
        print(f"✗ Error: {e}")
        print("\nAlternative: You can manually download from Kaggle:")
        print("1. Visit: https://www.kaggle.com/datasets")
        print("2. Search for 'youtube comments sentiment'")
        print("3. Download and place in data/raw/ directory")
        return None

