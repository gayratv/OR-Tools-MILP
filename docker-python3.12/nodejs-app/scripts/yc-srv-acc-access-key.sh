#!/usr/bin/bash

#https://yandex.cloud/ru/docs/iam/operations/sa/create

Создать статический ключ доступа
https://yandex.cloud/ru/docs/iam/operations/authentication/manage-access-keys#create-access-key

yc iam service-account list

Создайте ключ доступа для сервисного аккаунта sc-scheduller-msg-queue

yc iam access-key create --service-account-name sc-scheduller-msg-queue

Удалить статический ключ доступа
yc iam access-key list \
  --service-account-name sc-scheduller-msg-queue

yc iam access-key delete <идентификатор_ключа>
