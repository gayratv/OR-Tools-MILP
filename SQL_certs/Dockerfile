    # Используем официальный образ MySQL как основу
    FROM mysql:8.4

    # Копируем файл конфигурации
    COPY ./mysql/conf.d/my.cnf /etc/mysql/conf.d/my.cnf

    # Копируем скрипты инициализации
    COPY ./mysql/init/ /docker-entrypoint-initdb.d/

    # Копируем сертификаты
    COPY ./mysql/certs/ /certs/

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
