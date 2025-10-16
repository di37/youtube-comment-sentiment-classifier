import os, sys
from os.path import dirname as up

sys.path.append(os.path.abspath(os.path.join(up(__file__), os.pardir)))

import numpy as np
import pandas as pd
import pickle
import logging
import yaml
import mlflow
import mlflow.sklearn
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.feature_extraction.text import TfidfVectorizer
import os
import matplotlib.pyplot as plt
import seaborn as sns
import json
from mlflow.models import infer_signature

from dotenv import load_dotenv
load_dotenv()

# Set AWS credentials (replace with your actual credentials)
os.environ['AWS_ACCESS_KEY_ID'] = os.getenv('AWS_ACCESS_KEY_ID')
os.environ['AWS_SECRET_ACCESS_KEY'] = os.getenv('AWS_SECRET_ACCESS_KEY')
os.environ['AWS_DEFAULT_REGION'] = os.getenv('AWS_DEFAULT_REGION')


# logging configuration
logger = logging.getLogger('model_evaluation')
logger.setLevel('DEBUG')

# Only add handlers if they don't already exist to prevent duplicate logging
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel('DEBUG')

    file_handler = logging.FileHandler('model_evaluation_errors.log')
    file_handler.setLevel('ERROR')

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


def load_model(model_path: str):
    """Load the trained model."""
    try:
        with open(model_path, 'rb') as file:
            model = pickle.load(file)
        logger.debug('Model loaded from %s', model_path)
        return model
    except Exception as e:
        logger.error('Error loading model from %s: %s', model_path, e)
        raise


def load_vectorizer(vectorizer_path: str) -> TfidfVectorizer:
    """Load the saved TF-IDF vectorizer."""
    try:
        with open(vectorizer_path, 'rb') as file:
            vectorizer = pickle.load(file)
        logger.debug('TF-IDF vectorizer loaded from %s', vectorizer_path)
        return vectorizer
    except Exception as e:
        logger.error('Error loading vectorizer from %s: %s', vectorizer_path, e)
        raise


def evaluate_model(model, X_test: np.ndarray, y_test: np.ndarray):
    """Evaluate the model and log classification metrics and confusion matrix."""
    try:
        # Predict and calculate classification metrics
        y_pred = model.predict(X_test)
        
        # Calculate accuracy explicitly
        accuracy = accuracy_score(y_test, y_pred)
        
        # Generate classification report and confusion matrix
        report = classification_report(y_test, y_pred, output_dict=True)
        cm = confusion_matrix(y_test, y_pred)
        
        logger.debug('Model evaluation completed')

        return report, cm, accuracy
    except Exception as e:
        logger.error('Error during model evaluation: %s', e)
        raise


def log_confusion_matrix(cm, dataset_name):
    """Log confusion matrix as an artifact."""
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.title(f'Confusion Matrix for {dataset_name}')
    plt.xlabel('Predicted')
    plt.ylabel('Actual')

    # Save confusion matrix plot as a file and log it to MLflow
    cm_file_path = f'confusion_matrix_{dataset_name}.png'
    plt.savefig(cm_file_path)
    mlflow.log_artifact(cm_file_path)
    plt.close()

def save_model_info(run_id: str, artifact_path: str, file_path: str) -> None:
    """Save the model run ID and artifact path to a JSON file.
    
    Args:
        run_id: MLflow run ID
        artifact_path: Relative artifact path (e.g., 'lgbm_model'), not the full S3 URI
        file_path: Path to save the JSON file
    """
    try:
        # Create a dictionary with the info you want to save
        # Important: model_path should be just the artifact path, not the full S3 URI
        model_info = {
            'run_id': run_id,
            'model_path': artifact_path  # This should be just "lgbm_model", not the full S3 path
        }
        # Save the dictionary as a JSON file
        with open(file_path, 'w') as file:
            json.dump(model_info, file, indent=4)
        logger.debug('Model info saved to %s', file_path)
    except Exception as e:
        logger.error('Error occurred while saving the model info: %s', e)
        raise


def main():
    mlflow.set_tracking_uri("http://3.29.129.159:5000/")

    mlflow.set_experiment('dvc-pipeline-runs-2')
    from utilities import load_params, load_data
    
    with mlflow.start_run() as run:
        try:
            # Load parameters from YAML file
            params = load_params('params.yaml')

            # Log parameters
            for key, value in params.items():
                mlflow.log_param(key, value)
            
            # Load model and vectorizer
            model = load_model('lgbm_model.pkl')
            vectorizer = load_vectorizer('tfidf_vectorizer.pkl')

            # Load test data for signature inference
            test_data = load_data('data/interim/test_processed.csv')

            # Prepare test data
            X_test_tfidf = vectorizer.transform(test_data['clean_comment'].values)
            X_test_tfidf = X_test_tfidf.toarray()
            numerical_features = ['word_count', 'num_stop_words', 'num_chars', 'num_chars_cleaned']
            X_test_numerical = test_data[numerical_features].values
            X_test = np.hstack([X_test_tfidf, X_test_numerical])
            
            # print(X_test.shape)
            y_test = test_data['category'].values

            # Create a DataFrame for signature inference (using first few rows as an example)
            # Combine TF-IDF feature names with numerical feature names
            tfidf_feature_names = vectorizer.get_feature_names_out().tolist()
            all_feature_names = tfidf_feature_names + numerical_features
            input_example = pd.DataFrame(X_test[:5], columns=all_feature_names)

            # Infer the signature
            signature = infer_signature(input_example, model.predict(X_test[:5]))

            # Log model to MLflow using sklearn.log_model
            # This properly registers the model with MLflow so it can be registered later
            logger.debug('Logging model to MLflow...')
            print(f"Logging model to MLflow...")
            
            mlflow.sklearn.log_model(
                sk_model=model,
                artifact_path="lgbm_model",
                signature=signature,
                input_example=input_example
            )
            
            logger.debug('Model successfully logged to MLflow')
            print(f"✓ Model logged successfully")

            # Save model info with just the artifact path (not the full S3 URI)
            # The artifact path is needed for model registration
            artifact_path = "lgbm_model"  # This is the relative path within the run
            artifact_uri = mlflow.get_artifact_uri()  # Full S3 URI for logging purposes
            logger.debug(f'Model artifact URI: {artifact_uri}/{artifact_path}')
            save_model_info(run.info.run_id, artifact_path, 'experiment_info.json')
            
            # Also log model pickle file and vectorizer as artifacts
            logger.debug('Logging additional artifacts...')
            # mlflow.log_artifact('lgbm_model.pkl')
            mlflow.log_artifact('tfidf_vectorizer.pkl')
            logger.debug('Additional artifacts logged')
            
            # Print model location for verification
            print(f"\n{'='*50}")
            print(f"Model logged to: {artifact_uri}/{artifact_path}")
            print(f"Run ID: {run.info.run_id}")
            print(f"Experiment ID: {run.info.experiment_id}")
            print(f"Model URI for registration: runs:/{run.info.run_id}/{artifact_path}")
            print(f"{'='*50}\n")

            # Evaluate model and get metrics
            report, cm, accuracy = evaluate_model(model, X_test, y_test)

            # Display accuracy in console
            print(f"\n{'='*50}")
            print(f"Test Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
            print(f"{'='*50}\n")

            # Log overall accuracy to MLflow
            mlflow.log_metric("test_accuracy", accuracy)

            # Log classification report metrics for the test data
            for label, metrics in report.items():
                if isinstance(metrics, dict):
                    mlflow.log_metrics({
                        f"test_{label}_precision": metrics['precision'],
                        f"test_{label}_recall": metrics['recall'],
                        f"test_{label}_f1-score": metrics['f1-score']
                    })

            # Log confusion matrix
            log_confusion_matrix(cm, "Test Data")

            # Add important tags
            mlflow.set_tag("model_type", "LightGBM")
            mlflow.set_tag("task", "Sentiment Analysis")
            mlflow.set_tag("dataset", "YouTube Comments")

        except Exception as e:
            logger.error(f"Failed to complete model evaluation: {e}")
            print(f"Error: {e}")

if __name__ == '__main__':
    main()