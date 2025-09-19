#!/usr/bin/env bash

# Используем heredoc для определения многострочной переменной.
# Это самый удобный способ для форматирования JSON.
read -r -d '' PAYLOAD_JSON_LF <<'EOF'
[
  {
    'key': 'username',
    'text_value': 'myusername'
  }
]
EOF

PAYLOAD_JSON=$(echo "$PAYLOAD_JSON_LF" | tr -d '\n\t')

yc lockbox secret create \
 --name sample-secret \
 --description "Пример секрета" \
 --payload "${PAYLOAD_JSON}"
