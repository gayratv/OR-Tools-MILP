FROM mysql:8.4

# Устанавливаем необходимые утилиты
RUN microdnf install -y bash curl && microdnf clean all

# Копируем файл конфигурации
COPY ./mysql/conf.d/my.cnf /etc/mysql/conf.d/my.cnf

# Копируем скрипты инициализации
COPY ./mysql/init/ /docker-entrypoint-initdb.d/


# Устанавливаем правильного владельца и права доступа.
RUN chown mysql:mysql /etc/mysql/conf.d/my.cnf && \
    # ЭТО НОВАЯ И САМАЯ ВАЖНАЯ СТРОКА: Устанавливаем безопасные права на сам конфиг
    chmod 644 /etc/mysql/conf.d/my.cnf

# Копируем сертификаты
COPY ./certs /certs

# Устанавливаем правильного владельца и права доступа для сертификатов
RUN chown mysql:mysql /certs/ca.pem /certs/server-cert.pem /certs/server-key.pem && \
    chmod 644 /certs/ca.pem /certs/server-cert.pem && \
    chmod 600 /certs/server-key.pem

RUN mkdir -p /app/exchange && chmod 777 /app/exchange

COPY --chmod=755 entrypoint.sh /usr/local/bin/entrypoint.sh
COPY --chmod=755 make-mysql-certs-full.sh /usr/local/bin/make-mysql-certs-full.sh
COPY --chmod=755 make-mysql-certs-full.sh /usr/local/bin/download_one_file.sh



# Устанавливаем его как точку входа
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
