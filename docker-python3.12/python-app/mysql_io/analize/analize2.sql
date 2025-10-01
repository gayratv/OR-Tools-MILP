# напиши SQL запрос- покажи данные для ключа 'x' для solution_maps_json в TABLE calculation_results

SELECT
    result_id,

    JSON_EXTRACT(solution_maps_json, '$.x') AS x_data
FROM
    calculation_results;

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
    ) AS jt;