import boto3
import dotenv


env = dotenv.dotenv_values()


class Config:
    AWS_ACCESS_KEY_ID = env.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env.get("AWS_SECRET_ACCESS_KEY")

    S3_SERVICE_NAME = "s3"
    S3_ENDPOINT_URL = "https://storage.yandexcloud.net"


def get_session():
    session = boto3.session.Session()

    return session.client(
        service_name=Config.S3_SERVICE_NAME,
        endpoint_url=Config.S3_ENDPOINT_URL,
        aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
    )


bucket_name = env.get("AWS_BUCKET_NAME")

s3 = get_session()

if s3.list_objects(Bucket=bucket_name).get("Contents"):
    for key in s3.list_objects(Bucket=bucket_name)["Contents"]:
        print(key["Key"])
