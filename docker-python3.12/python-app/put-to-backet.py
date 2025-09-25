import boto3
import os

# Получаем учетные данные и параметры из переменных окружения
endpoint_url = os.getenv("S3_ENDPOINT_URL")
region_name = os.getenv("S3_REGION_NAME")
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
bucket_name = os.getenv("S3_BUCKET_NAME")

session = boto3.session.Session()
s3 = session.client(
    service_name='s3',
    endpoint_url=endpoint_url,
    region_name=region_name,
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)
## Из файла
s3.upload_file(__file__, bucket_name, 'py_script.py')
