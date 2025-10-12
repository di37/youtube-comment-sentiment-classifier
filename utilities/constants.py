import os, sys
from os.path import dirname as up

sys.path.append(os.path.abspath(os.path.join(up(__file__), os.pardir)))

KAGGLE_DATASET_NAME = "atifaliak/youtube-comments-dataset"
RAW_DATA_PATH = "data/raw"

INTERIM_DATA_PATH = "data/interim"
PROCESSED_DATA_PATH = "data/processed"

