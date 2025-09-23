import os
from dotenv import load_dotenv
import mlflow
from mlflow import MlflowClient


def setup_mlflow_client():
    load_dotenv()

    TRACKING_SERVER_HOST = "127.0.0.1"
    TRACKING_SERVER_PORT = 5000

    uri = f"http://{TRACKING_SERVER_HOST}:{TRACKING_SERVER_PORT}"

    client = MlflowClient(tracking_uri=uri, registry_uri=uri)

    return client


def setup_env():
    load_dotenv()
    # REGION: Это не обязательная часть, которую при вызове `load_dotenv()` можно не делать
    os.environ["MLFLOW_S3_ENDPOINT_URL"] = "https://storage.yandexcloud.net"
    os.environ["AWS_BUCKET_NAME"] = str(os.environ.get("S3_BUCKET_NAME"))
    os.environ["AWS_ACCESS_KEY_ID"] = str(os.environ.get("AWS_ACCESS_KEY_ID"))
    os.environ["AWS_SECRET_ACCESS_KEY"] = str(os.environ.get("AWS_SECRET_ACCESS_KEY"))

    os.environ["DB_DESTINATION_HOST"] = str(os.environ.get("DB_DESTINATION_HOST"))
    os.environ["DB_DESTINATION_PORT"] = os.environ.get("DB_DESTINATION_PORT")
    os.environ["DB_DESTINATION_NAME"] = str(os.environ.get("DB_DESTINATION_NAME"))
    os.environ["DB_DESTINATION_USER"] = str(os.environ.get("DB_DESTINATION_USER"))
    os.environ["DB_DESTINATION_PASSWORD"] = str(
        os.environ.get("DB_DESTINATION_PASSWORD")
    )

    os.environ["EXPERIMANT_NAME"] = str(os.environ.get("EXPERIMANT_NAME"))
    os.environ["REGISTRY_MODEL_NAME"] = str(os.environ.get("REGISTRY_MODEL_NAME"))
    os.environ["RUN_NAME"] = str(os.environ.get("RUN_NAME"))
    os.environ["SOURCE_TABLE_NAME"] = str(os.environ.get("SOURCE_TABLE_NAME"))
    # ENDREGION

    mlflow.set_tracking_uri(
        f"http://{os.environ.get('MLFLOW_SERVER_HOST')}:{os.environ.get('MLFLOW_SERVER_PORT')}"
    )
    mlflow.set_registry_uri(
        f"http://{os.environ.get('MLFLOW_SERVER_HOST')}:{os.environ.get('MLFLOW_SERVER_PORT')}"
    )
