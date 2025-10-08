FROM mysql:8.4
# Устанавливаем только runtime-зависимости для pyodbc
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        curl \
        mc \
        jq \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*



# Добавляем yc и скрипты в PATH
ENV PATH="/home/appuser/yandex-cloud/bin:/home/appuser/scripts:${PATH}"

# Меняем владельца всех файлов и делаем скрипты исполняемыми
RUN chown -R appuser:appuser /home/appuser && \
    chmod +x /home/appuser/scripts/*.sh && \
    chmod +x /home/appuser/app/entrypoint.sh


RUN curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash -s -- -a

# Копируем файл конфигурации
COPY ./mysql/conf.d/my.cnf /etc/mysql/conf.d/my.cnf

# Копируем скрипты инициализации
COPY ./mysql/init/ /docker-entrypoint-initdb.d/

# Копируем сертификаты
#COPY ./mysql/certs/ /certs/

# Устанавливаем правильного владельца и права доступа.
RUN chown mysql:mysql /etc/mysql/conf.d/my.cnf && \
    # ЭТО НОВАЯ И САМАЯ ВАЖНАЯ СТРОКА: Устанавливаем безопасные права на сам конфиг
    chmod 644 /etc/mysql/conf.d/my.cnf && \
    # Устанавливаем владельца на сертификаты
    chown -R mysql:mysql /certs && \
    # Устанавливаем права на ключи
    chmod 600 /certs/*-key.pem && \
    # Устанавливаем права на публичные сертификаты
    chmod 644 /certs/*-cert.pem /certs/ca.pem

WORKDIR /app
COPY *.sh .
RUN chmod +x *.sh

ENTRYPOINT ["/app/entrypoint.sh"]