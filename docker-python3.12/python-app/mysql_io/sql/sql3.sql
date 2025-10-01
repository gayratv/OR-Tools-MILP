SELECT
  k.k        AS x_key,
  JSON_UNQUOTE(v.v) AS x_value
FROM tbl1 AS t
CROSS JOIN JSON_TABLE(        -- значения объекта x
  t.doc,
  '$.x.*' COLUMNS (
    seq FOR ORDINALITY,
    v   JSON PATH '$'
  )
) AS v
CROSS JOIN JSON_TABLE(        -- ключи объекта x
  JSON_KEYS(t.doc, '$.x'),
  '$[*]' COLUMNS (
    seq FOR ORDINALITY,
    k   VARCHAR(255) PATH '$'
  )
) AS k
WHERE t.id = 1
  AND v.seq = k.seq           -- склейка по порядковому номеру
ORDER BY v.seq
LIMIT 500;
