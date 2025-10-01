# напиши SQL запрос- покажи данные для ключа 'x' для solution_maps_json в TABLE calculation_results

SELECT
    result_id,
    JSON_EXTRACT(solution_maps_json, '$.x') AS x_data
FROM
    calculation_results;

SELECT
    result_id,
    JSON_EXTRACT(solution_maps_json, '$.z') AS x_data
FROM
    calculation_results
limit 50;

# Этот запрос извлечет данные из ключа 'x',
# преобразует каждую пару "ключ-значение" в отдельную строку и
# разберет сложный ключ (например, "('5A', 'PE', 'Fri', 1)") на отдельные столбцы.

SELECT
    cr.result_id,
    cr.job_id,

     -- Логика разбора ключа теперь будет работать с настоящим строковым ключом
     -- Используем REPLACE вместо TRIM для большей надежности при удалении ненужных символов
     REPLACE(REPLACE(SUBSTRING_INDEX(SUBSTRING_INDEX(jt.key_string, ',', 1), '(', -1), "'", ''), " ", "") AS class,
     REPLACE(REPLACE(SUBSTRING_INDEX(SUBSTRING_INDEX(jt.key_string, ',', 2), ',', -1), "'", ''), " ", "") AS subject,
     REPLACE(REPLACE(SUBSTRING_INDEX(SUBSTRING_INDEX(jt.key_string, ',', 3), ',', -1), "'", ''), " ", "") AS day,
     -- ИСПРАВЛЕНИЕ: Заменяем скобку и пробел с помощью REPLACE, чтобы избежать ошибок TRIM
     -- 1. SUBSTRING_INDEX(..., -1) извлекает последнюю часть ключа, например " 1)"
     -- 2. REPLACE удаляет ')'
     -- 3. Внешний REPLACE удаляет ' '
     REPLACE(REPLACE(SUBSTRING_INDEX(jt.key_string, ',', -1), ')', ''), ' ', '') AS period,
     -- Извлекаем значение, используя полученный ключ
     JSON_UNQUOTE(JSON_EXTRACT(cr.solution_maps_json, CONCAT('$.x."', jt.key_string, '"'))) AS value
FROM
    calculation_results cr,
    -- 1. Получаем массив ключей
    -- 2. Превращаем массив в таблицу из одной колонки (key_string)
    JSON_TABLE(
        JSON_KEYS(cr.solution_maps_json, '$.x'),
        '$[*]' COLUMNS (
            key_string VARCHAR(100) PATH '$'
        )
    ) AS jt
WHERE
    cr.job_id = 1
HAVING
    value > 0;


# Этот запрос для каждой строки, где job_id = 1, посчитает и выведет количество ключей в объекте solution_maps_json.x.
-- =====================================================================================
-- Запрос для подсчета количества ключей в объекте 'x' для job_id = 1
-- =====================================================================================
-- Используется функция JSON_LENGTH(), которая эффективно считает
-- количество пар "ключ:значение" в JSON-объекте.

SELECT
    result_id,
    job_id,
    JSON_LENGTH(solution_maps_json, '$.x') AS x_key_count
FROM
    calculation_results
WHERE
    job_id = 1;

-- =====================================================================================
-- Запрос для подсчета количества ключей, у которых value = 1, с группировкой по job_id
-- =====================================================================================
-- 1. JSON_TABLE извлекает все значения из объекта 'x' в виртуальную колонку 'value'.
-- 2. WHERE фильтрует только те строки, где это значение равно 1.
-- 3. COUNT(*) и GROUP BY подсчитывают количество таких строк для каждого job_id.

SELECT
    cr.job_id,
    COUNT(*) AS count_of_value_1
FROM
    calculation_results cr,
    JSON_TABLE(
        cr.solution_maps_json,
        '$.x.*' COLUMNS (
            value INT PATH '$'
        )
    ) AS jt
WHERE
    jt.value = 1 and cr.job_id = 1
GROUP BY
    cr.job_id;

# =============== Z
-- =====================================================================================
-- Адаптированный запрос для извлечения данных из ключа 'z' (5 элементов в ключе)
-- =====================================================================================
SELECT
    cr.result_id,
    cr.job_id,

     -- Адаптированная логика разбора ключа для 5 элементов
     REPLACE(REPLACE(SUBSTRING_INDEX(SUBSTRING_INDEX(jt.key_string, ',', 1), '(', -1), "'", ''), " ", "") AS class,
     REPLACE(REPLACE(SUBSTRING_INDEX(SUBSTRING_INDEX(jt.key_string, ',', 2), ',', -1), "'", ''), " ", "") AS subject,
     -- Новая колонка для 3-го элемента в ключе (например, teacher_id)
     REPLACE(REPLACE(SUBSTRING_INDEX(SUBSTRING_INDEX(jt.key_string, ',', 3), ',', -1), "'", ''), " ", "") AS subgoup_id,
     -- Смещаем индексы для оставшихся колонок
     REPLACE(REPLACE(SUBSTRING_INDEX(SUBSTRING_INDEX(jt.key_string, ',', 4), ',', -1), "'", ''), " ", "") AS day,
     REPLACE(REPLACE(SUBSTRING_INDEX(jt.key_string, ',', -1), ')', ''), ' ', '') AS period,

     -- Извлекаем значение, используя ключ из объекта 'z'
     JSON_UNQUOTE(JSON_EXTRACT(cr.solution_maps_json, CONCAT('$.z."', jt.key_string, '"'))) AS value
FROM
    calculation_results cr,
    -- 1. Получаем массив ключей из объекта 'z'
    JSON_TABLE(
        JSON_KEYS(cr.solution_maps_json, '$.z'),
        '$[*]' COLUMNS (
            key_string VARCHAR(100) PATH '$'
        )
    ) AS jt
WHERE
    cr.job_id = 1
HAVING
    value > 0;