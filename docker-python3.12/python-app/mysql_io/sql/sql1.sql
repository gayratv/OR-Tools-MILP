SELECT
  JSON_UNQUOTE(JSON_EXTRACT(t.keys_arr, CONCAT('$[', n.n, ']')))                    AS x_key,
  JSON_UNQUOTE(
    JSON_EXTRACT(
      t.x_obj,
      CONCAT(
        '$."',
        REPLACE(
          JSON_UNQUOTE(JSON_EXTRACT(t.keys_arr, CONCAT('$[', n.n, ']'))),
          '"','\\"'
        ),
        '"'
      )
    )
  ) AS x_value
FROM (
  SELECT
    JSON_EXTRACT(cr.solution_maps_json, '$.x')                                  AS x_obj,
    JSON_KEYS(JSON_EXTRACT(cr.solution_maps_json, '$.x'))                       AS keys_arr
  FROM calculation_results cr
  WHERE cr.job_id = 1
) AS t
JOIN (
  /* генератор чисел 0..999 без таблиц/CTE */
  SELECT ones.n + tens.n*10 + hundreds.n*100 AS n
  FROM (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
        UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) ones
  CROSS JOIN (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
              UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) tens
  CROSS JOIN (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
              UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) hundreds
) AS n
  ON n.n < JSON_LENGTH(t.keys_arr)
ORDER BY n.n
LIMIT 500;
