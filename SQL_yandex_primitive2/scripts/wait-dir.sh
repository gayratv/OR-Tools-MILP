#!/bin/bash

set -Eeuo pipefail
for i in {1..100}
do
  if [ -d /home/yc-user/yandex-cloud/bin ]; then
    echo "OK: /home/yc-user/yandex-cloud/bin found." | tee -a /var/log/runcmd-debug.log
    exit 0
  fi
  echo "Waiting for /home/yc-user/yandex-cloud/bin ($i)" | tee -a /var/log/runcmd-debug.log
  sleep 1
done

echo "ERROR: /home/yc-user/yandex-cloud/bin not found after 100s" | tee -a /var/log/runcmd-debug.log
exit 1

#ls  /app/scripts/wd.sh
#chmod +x /app/scripts/wd.sh
