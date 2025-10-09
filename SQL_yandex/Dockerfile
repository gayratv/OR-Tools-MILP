FROM mysql:8.4

# Устанавливаем необходимые утилиты
RUN microdnf install -y \
        bash \
        curl \
        mc \
        jq \
    && microdnf clean all

# Устанавливаем Yandex Cloud CLI
RUN curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash -s -- -a

# Добавляем yc и скрипты в PATH. Скрипты будут скопированы в /app
ENV PATH="/root/yandex-cloud/bin:/app:${PATH}"

# Копируем файл конфигурации
COPY ./mysql/conf.d/my.cnf /etc/mysql/conf.d/my.cnf

# Копируем скрипты инициализации
COPY ./mysql/init/ /docker-entrypoint-initdb.d/


# Создаем директорию для сертификатов, которые будут сгенерированы при запуске
RUN mkdir -p /certs

# Устанавливаем правильного владельца и права доступа.
RUN chown mysql:mysql /etc/mysql/conf.d/my.cnf && \
    # ЭТО НОВАЯ И САМАЯ ВАЖНАЯ СТРОКА: Устанавливаем безопасные права на сам конфиг
    chmod 644 /etc/mysql/conf.d/my.cnf

#    && \
#    # Устанавливаем владельца на сертификаты
#    chown -R mysql:mysql /certs && \
#    # Устанавливаем права на ключи
#    chmod 600 /certs/*-key.pem && \
#    # Устанавливаем права на публичные сертификаты
#    chmod 644 /certs/*-cert.pem /certs/ca.pem

# Копируем скрипты в рабочую директорию и делаем их исполняемыми
WORKDIR /app
COPY *.sh .
RUN chmod +x *.sh

# Указываем точку входа
ENTRYPOINT ["/app/entrypoint.sh"]