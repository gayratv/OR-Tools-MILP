#!/usr/bin/env bash
set -euo pipefail

yc config set <имя_параметра> <значение_параметра>

yc config set folder-id b1gbgjv35qvro3lmgaci
yc config set cloud-id b1gib03pgvqrrfvhl3kb

yc config list

Получите подробную информацию о профиле с именем prod:

yc config profile get prod
yc config profile get default


yc config profile activate test
Profile 'test' activated
