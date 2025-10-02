select id
from subjects;

-- Генерация последовательности чисел от 5 до 11 с помощью рекурсивного CTE (для MySQL 8.0+)
WITH RECURSIVE number_series AS (SELECT 5 AS n
                                 UNION ALL
                                 SELECT n + 1
                                 FROM number_series
                                 WHERE n < 11)
SELECT n
FROM number_series;


INSERT INTO subject_difficulties (subject_id, grade)
WITH RECURSIVE number_series AS (
    -- Этот CTE генерирует последовательность чисел от 5 до 11
    SELECT 5 AS n
    UNION ALL
    SELECT n + 1
    FROM number_series
    WHERE n < 11)
-- CROSS JOIN создает декартово произведение между всеми id из subjects и всеми числами из number_series
SELECT s.id,
       ns.n
FROM subjects s
         CROSS JOIN
     number_series ns
ORDER BY s.id, ns.n;

select  S.name,SD.grade,SD.difficulty,SD.id
from subject_difficulties SD
         inner join subjects S on SD.subject_id = S.id;


ALTER TABLE teachers
ADD COLUMN name_eng VARCHAR(100) AS (CONCAT('teach', id)) STORED;

ALTER TABLE teachers
ADD COLUMN name_eng VARCHAR(100) GENERATED ALWAYS AS (CONCAT('teach', id)) STORED;


select version();

# ===================
-- Добавляем столбец, пока разрешая ему быть пустым
ALTER TABLE teachers
ADD COLUMN name_eng VARCHAR(100);

-- Заполняем его для всех существующих записей
UPDATE teachers
SET name_eng = CONCAT('teach', TO_BASE64(RANDOM_BYTES(5)))
WHERE name_eng IS NULL;

-- Изменяем столбец, делая его обязательным и добавляя значение по умолчанию
ALTER TABLE teachers
MODIFY COLUMN name_eng VARCHAR(100) NOT NULL
    DEFAULT (CONCAT('teach', TO_BASE64(RANDOM_BYTES(5))));