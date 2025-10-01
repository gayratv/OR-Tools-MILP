# покажи ключи верхнего уровня для solution_maps_json в TABLE calculation_results
# напиши запрос- покажи ключи верхнего уровня для solution_maps_json в TABLE calculation_results

# JSON_KEYS(solution_maps_json) получает ключи в виде массива,
SELECT DISTINCT
    JSON_KEYS(solution_maps_json) AS top_level_keys
FROM
    calculation_results;


# каждый ключ в отдельной строке
SELECT DISTINCT
    j.key_name
FROM
    calculation_results,
    JSON_TABLE(
        JSON_KEYS(solution_maps_json),
        '$[*]' COLUMNS (key_name VARCHAR(255) PATH '$')
    ) AS j
ORDER BY
    j.key_name;