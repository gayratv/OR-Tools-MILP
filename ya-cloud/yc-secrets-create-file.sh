#!/usr/bin/env bash

SECRET_NAME=${1:-"mysql-certs"}
MYSQL_CERT_DIR="/mnt/f/_prg/python/OR-Tools-MILP/ya-cloud/.mysql"

echo "Создание секрета '$SECRET_NAME'"

PAYLOAD="["
FIRST=true

for cert_file in "$MYSQL_CERT_DIR"/*.pem; do
  if [ -f "$cert_file" ]; then
    if [ "$FIRST" = true ]; then
      FIRST=false
    else
      PAYLOAD+=","
    fi

    filename=$(basename "$cert_file")
    content_b64=$(base64 -w 0 "$cert_file")

    json_fragment=$(printf '{"key": "%s", "binary_value": "%s"}' "$filename" "$content_b64")
    PAYLOAD+=$json_fragment
  fi
done

PAYLOAD+="]"

echo $PAYLOAD

# Если не найдено ни одного pem-файла
if [ "$PAYLOAD" = "[]" ]; then
    echo "No .pem files found in $MYSQL_CERT_DIR"
    exit 1
fi

yc lockbox secret create \
  --name "$SECRET_NAME" \
  --description "MySQL сертификаты" \
  --payload "$PAYLOAD"



#yc lockbox secret list
#yc lockbox secret delete --name mysql-certs
