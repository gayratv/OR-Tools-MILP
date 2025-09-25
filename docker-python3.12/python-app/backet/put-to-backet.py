#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from pathlib import Path
import boto3
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env, который находится в родительской директории
dotenv_path = Path(__file__).parent.parent / 'responce/.env'
load_dotenv(dotenv_path=dotenv_path)

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

# Создать новый бакет
s3.create_bucket(Bucket=bucket_name)

# Загрузить объекты в бакет

## Из строки
s3.put_object(Bucket=bucket_name, Key='object_name', Body='TEST', StorageClass='COLD')

## Из файла
s3.upload_file(__file__, bucket_name, 'py_script.py')
s3.upload_file(__file__, bucket_name, 'script/py_script.py')

# Получить список объектов в бакете
for key in s3.list_objects(Bucket=bucket_name)['Contents']:
    print(key['Key'])

# # Удалить несколько объектов
# forDeletion = [{'Key': 'object_name'}, {'Key': 'script/py_script.py'}]
# response = s3.delete_objects(Bucket=bucket_name, Delete={'Objects': forDeletion})
#
# # Получить объект
# get_object_response = s3.get_object(Bucket=bucket_name, Key='py_script.py')
# print(get_object_response['Body'].read())
