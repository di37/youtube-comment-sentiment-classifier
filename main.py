from data_handling import download_and_copy_dataset
from utilities import load_params, load_data, save_data
from utilities import KAGGLE_DATASET_NAME, RAW_DATA_PATH, INTERIM_DATA_PATH
from data_handling import preprocess_comment, feature_engineering, split_data


print(">>> Stage 1: Starting the data handling pipeline...")

params = load_params("params.yaml")

test_size = params["data_ingestion"]["test_size"]
val_size = params["data_ingestion"]["val_size"]
random_state = params["data_ingestion"]["random_state"]
stratify_column = params["data_ingestion"]["stratify_column"]

# 1. Download and copy dataset
csv_path = download_and_copy_dataset(dataset_name=KAGGLE_DATASET_NAME, raw_data_path=RAW_DATA_PATH)

# 2. Load the dataset
df = load_data(csv_path)

# 3. Split the Dataset
train_data, val_data, test_data = split_data(df, test_size, val_size, random_state, stratify_column)

# 4. Save the dataset
save_data(train_data, val_data, test_data, data_path=RAW_DATA_PATH)

print(">>> Stage 1: Data handling pipeline completed successfully...")

# print(">>> Stage 2: Starting Data Preprocessing pipeline...")

# # 1. Preprocess the dataset
# train_df = feature_engineering(train_data, preprocess_comment)
# val_df = feature_engineering(val_data, preprocess_comment)
# test_df = feature_engineering(test_data, preprocess_comment)

# print(train_df.head())
# print(val_df.head())
# print(test_df.head())

# # 2. Save the dataset
# save_data(train_df, val_df, test_df, data_path=INTERIM_DATA_PATH)

# print(">>> Stage 2: Data Preprocessing pipeline completed successfully...")
