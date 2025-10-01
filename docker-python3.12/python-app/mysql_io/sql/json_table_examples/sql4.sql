# Пример 4. Обработка пустых значений/ошибок типов (ON EMPTY/ON ERROR)

CREATE TABLE readings (
  id INT PRIMARY KEY,
  payload JSON NOT NULL
);

INSERT INTO readings VALUES
(1, JSON_OBJECT('n','42')),
(2, JSON_OBJECT('n',NULL)),
(3, JSON_OBJECT('x','oops'));  -- нет поля n, и есть строка 'oops'

# Запрос: аккуратно конвертируем к INT.
SELECT
  r.id,
  jt.n
FROM readings r
JOIN JSON_TABLE(
  r.payload, '$'
  COLUMNS (
    n INT PATH '$.n'
      DEFAULT '0' ON EMPTY   -- если поля n нет или оно JSON null → 0
      NULL ON ERROR        -- если не удаётся привести к INT → NULL
  )
) jt ON 1=1
ORDER BY r.id;
