import os, sys
from os.path import dirname as up

sys.path.append(os.path.abspath(os.path.join(up(__file__), os.pardir)))

import numpy as np
import pandas as pd

import pickle
import yaml
import logging
import lightgbm as lgb
from sklearn.feature_extraction.text import TfidfVectorizer

# logging configuration
logger = logging.getLogger('model_building')
logger.setLevel('DEBUG')

# Only add handlers if they don't already exist to prevent duplicate logging
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel('DEBUG')

    file_handler = logging.FileHandler('model_building_errors.log')
    file_handler.setLevel('ERROR')

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


def apply_tfidf(train_data: pd.DataFrame, max_features: int, ngram_range: tuple) -> tuple:
    """Apply TF-IDF with ngrams to the data."""
    try:
        vectorizer = TfidfVectorizer(max_features=max_features, ngram_range=ngram_range)

        X_train = train_data['clean_comment'].values
        y_train = train_data['category'].values

        # Perform TF-IDF transformation
        X_train_tfidf = vectorizer.fit_transform(X_train)

        logger.debug(f"TF-IDF transformation complete. Train shape: {X_train_tfidf.shape}")

        # Save the vectorizer in the root directory
        with open(os.path.join('tfidf_vectorizer.pkl'), 'wb') as f:
            pickle.dump(vectorizer, f)

        logger.debug('TF-IDF applied with trigrams and data transformed')
        return X_train_tfidf, y_train
    except Exception as e:
        logger.error('Error during TF-IDF transformation: %s', e)
        raise


def train_lgbm(
    X_train: np.ndarray,
    y_train: np.ndarray,
    n_estimators: int,
    max_depth: int,
    num_leaves: int,
    min_child_samples: int,
    learning_rate: float,
    colsample_bytree: float,
    subsample: float,
    reg_alpha: float,
    reg_lambda: float
) -> lgb.LGBMClassifier:
    """Train a LightGBM model with full parameter set."""
    try:
        best_model = lgb.LGBMClassifier(
            objective='multiclass',
            num_class=3,
            metric="multi_logloss",
            is_unbalance=True,
            class_weight="balanced",
            learning_rate=learning_rate,
            max_depth=max_depth,
            n_estimators=n_estimators,
            num_leaves=num_leaves,
            min_child_samples=min_child_samples,
            colsample_bytree=colsample_bytree,
            subsample=subsample,
            reg_alpha=reg_alpha,
            reg_lambda=reg_lambda
        )
        best_model.fit(X_train, y_train)
        logger.debug('LightGBM model training completed')
        return best_model
    except Exception as e:
        logger.error('Error during LightGBM model training: %s', e)
        raise



def save_model(model, file_path: str) -> None:
    """Save the trained model to a file."""
    try:
        with open(file_path, 'wb') as file:
            pickle.dump(model, file)
        logger.debug('Model saved to %s', file_path)
    except Exception as e:
        logger.error('Error occurred while saving the model: %s', e)
        raise


def main():
    try:
        from utilities import load_params, load_data
        # from utilities import RAW_DATA_PATH, INTERIM_DATA_PATH

        # Load parameters from the root directory
        params = load_params('params.yaml')
        ngram_range = tuple(params['model_building']['ngram_range'])
        max_features = params['model_building']['max_features']

        # Tree structure
        n_estimators = params['model_building']['n_estimators']
        max_depth = params['model_building']['max_depth']
        num_leaves = params['model_building']['num_leaves']
        min_child_samples = params['model_building']['min_child_samples']
        
        # Learning Rate
        learning_rate = params['model_building']['learning_rate']
        
        # Sampling
        colsample_bytree = params['model_building']['colsample_bytree']
        subsample = params['model_building']['subsample']
       
        # Regularization
        reg_alpha = params['model_building']['reg_alpha']
        reg_lambda = params['model_building']['reg_lambda']

        # print(f"ngram_range: {ngram_range}")
        # print(f"max_features: {max_features}")
        # print(f"n_estimators: {n_estimators}")
        # print(f"max_depth: {max_depth}")
        # print(f"num_leaves: {num_leaves}")
        # print(f"min_child_samples: {min_child_samples}")
        # print(f"learning_rate: {learning_rate}")
        # print(f"colsample_bytree: {colsample_bytree}")
        # print(f"subsample: {subsample}")
        # print(f"reg_alpha: {reg_alpha}")
        # print(f"reg_lambda: {reg_lambda}")

        # Load the preprocessed training data from the interim directory
        train_data = load_data('data/interim/train_processed.csv')
        print(train_data.head())

        # Apply TF-IDF feature engineering on training data
        X_train_tfidf, y_train = apply_tfidf(train_data, max_features, ngram_range)

        numerical_features = ['word_count', 'num_stop_words', 'num_chars', 'num_chars_cleaned']
        X_train_numerical = train_data[numerical_features].values
        
        # Combine text features with numerical features
        X_train_tfidf = X_train_tfidf.toarray()
        X_train = np.hstack([X_train_tfidf, X_train_numerical])
        # X_train = np.hstack([X_train_tfidf, X_train_numerical])
        # print(X_train.shape)

        # Train the LightGBM model using hyperparameters from params.yaml
        best_model = train_lgbm(X_train, y_train, n_estimators, max_depth, num_leaves, min_child_samples, learning_rate, colsample_bytree, subsample, reg_alpha, reg_lambda)

        # Save the trained model in the root directory
        save_model(best_model, 'lgbm_model.pkl')

    except Exception as e:
        logger.error('Failed to complete the feature engineering and model building process: %s', e)
        print(f"Error: {e}")


if __name__ == '__main__':
    main()