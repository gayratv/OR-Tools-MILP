#!/usr/bin/env bash

# Скрипт сам получает SECRET_ID через IMDS, тянет файлы (через declare -A FILES),
# достаёт .env из Lockbox, ждёт готовности и запускает compose.
# URL’ы можно задать прямо в скрипте (с плейсхолдерами) или переопределить через переменные окружения.

set -euo pipefail

APP_DIR="/opt/app"
BIN_DIR="$APP_DIR/bin"
ASSETS_DIR="$APP_DIR/assets"
mkdir -p "$BIN_DIR" "$ASSETS_DIR" "$APP_DIR/config"

# ====== URL-ы (замени на свои или прокинь через env) ======
URL_WAIT="${URL_WAIT:-https://raw.githubusercontent.com/<owner>/<repo>/<ref>/scripts/wait_for_files.sh}"
URL_COMPOSE="${URL_COMPOSE:-https://raw.githubusercontent.com/<owner>/<repo>/<ref>/deploy/docker-compose.yml}"
URL_DOCKERFILE="${URL_DOCKERFILE:-https://raw.githubusercontent.com/<owner>/<repo>/<ref>/deploy/Dockerfile}"
# Необязательные:
URL_MODEL="${URL_MODEL:-}"        # например: https://.../artifacts/big_model.bin
URL_APP_CFG="${URL_APP_CFG:-}"    # например: https://.../config/app.yaml

echo "==> Fetch SECRET_ID from instance metadata"
IMDS="http://169.254.169.254/computeMetadata/v1"
SECRET_ID="$(curl -fsS -H 'Metadata-Flavor: Google' "$IMDS/instance/attributes/SECRET_ID")"
if [[ -z "${SECRET_ID:-}" ]]; then
  echo "ERROR: SECRET_ID is empty in instance metadata" >&2
  exit 1
fi

echo "==> Download helper: wait_for_files.sh"
curl -fsSL -o "$BIN_DIR/wait_for_files.sh" "$URL_WAIT"
chmod +x "$BIN_DIR/wait_for_files.sh"

echo "==> Download application files"
declare -A FILES=(
  ["$APP_DIR/docker-compose.yml"]="$URL_COMPOSE"
  ["$APP_DIR/Dockerfile"]="$URL_DOCKERFILE"
)
[[ -n "$URL_MODEL"   ]] && FILES["$ASSETS_DIR/big_model.bin"]="$URL_MODEL"
[[ -n "$URL_APP_CFG" ]] && FILES["$APP_DIR/config/app.yaml"]="$URL_APP_CFG"

for dst in "${!FILES[@]}"; do
  url="${FILES[$dst]}"
  echo " -> $dst"
  install -d -m 0755 "$(dirname "$dst")"
  curl -fsSL -o "$dst" "$url"
done

echo "==> Fetch .env from Lockbox using SA IAM token"
IAM_TOKEN="$(curl -fsS -H 'Metadata-Flavor: Google' \
  "$IMDS/instance/service-accounts/default/token" | jq -r .access_token)"

PAYLOAD_JSON="$(curl -fsS -H "Authorization: Bearer ${IAM_TOKEN}" \
  "https://payload.lockbox.api.cloud.yandex.net/lockbox/v1/secrets/${SECRET_ID}/payload")"

ENV_FILE="$APP_DIR/.env"
BIN_SEC_DIR="$APP_DIR/.secrets-bin"
mkdir -p "$BIN_SEC_DIR"

{
  echo "# generated from Lockbox $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  echo "$PAYLOAD_JSON" | jq -r '.entries[]? | select(.textValue != null) | "\(.key)=\(.textValue)"'
} > "$ENV_FILE"
chmod 600 "$ENV_FILE"

echo "$PAYLOAD_JSON" \
  | jq -c '.entries[]? | select(.binaryValue != null) | {key, value: .binaryValue}' \
  | while read -r line; do
      k="$(echo "$line" | jq -r '.key')"
      v_b64="$(echo "$line" | jq -r '.value')"
      out="$BIN_SEC_DIR/$k"
      echo " -> writing $out"
      echo "$v_b64" | base64 --decode > "$out"
      chmod 600 "$out"
    done

echo "==> Wait for required files"
"$BIN_DIR/wait_for_files.sh" \
  -f "$ENV_FILE" \
  -p "$ASSETS_DIR/*.bin" \
  --min-size 1 \
  --stable 3 \
  --timeout 600

echo "==> docker compose build && up -d"
cd "$APP_DIR"
docker compose config >/dev/null
docker compose build
docker compose up -d

echo "==> Done."
