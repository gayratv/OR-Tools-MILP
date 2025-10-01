/* ===== Подготовка ===== */
DROP TABLE IF EXISTS tbl1;
DROP TABLE IF EXISTS tbl2;

CREATE TABLE tbl1 (
  id  INT PRIMARY KEY,
  doc JSON NOT NULL
);

INSERT INTO tbl1 (id, doc) VALUES
(1, JSON_OBJECT(
  'x', JSON_OBJECT(
    "('5A', 'PE', 'Fri', 1)", 0,
    "('5A', 'PE', 'Fri', 2)", 0,
    "('5A', 'PE', 'Fri', 3)", 1,
    "('5A', 'PE', 'Fri', 4)", 0,
    "('6B', 'Math', 'Mon', 1)", 2
  ),
  'z', JSON_ARRAY(10, 20, 30, 40, 50)
));

/* ===== 1) JSON_TABLE по МАССИВУ (должно вернуть 5 строк: 10..50) ===== */
SELECT
  t.id,
  jt.idx,
  jt.value
FROM tbl1 AS t
CROSS JOIN JSON_TABLE(
  t.doc,
  '$.z[*]' COLUMNS (
    idx   FOR ORDINALITY,
    value INT PATH '$'
  )
) AS jt
WHERE t.id = 1
ORDER BY jt.idx;

/* ===== 2) JSON_TABLE по ОБЪЕКТУ: разворачиваем ключи x =====
   ВАЖНО: используем CROSS JOIN и JSON_KEYS(JSON_EXTRACT(...,'$.x'))
*/
SELECT
  t.id,
  j.k AS x_key,
  JSON_UNQUOTE(
    JSON_EXTRACT(t.doc, CONCAT('$["x"][', JSON_QUOTE(j.k), ']'))
  ) AS x_value
FROM tbl1 AS t
CROSS JOIN JSON_TABLE(
  JSON_KEYS(JSON_EXTRACT(t.doc, '$.x')),
  '$[*]' COLUMNS (k VARCHAR(255) PATH '$')
) AS j
WHERE t.id = 1
ORDER BY x_key
LIMIT 500;

/* ===== 3) Тот же пункт 2, но с синтаксисом через запятую вместо JOIN ===== */
SELECT
  t.id,
  j.k AS x_key,
  JSON_UNQUOTE(
    JSON_EXTRACT(t.doc, CONCAT('$["x"][', JSON_QUOTE(j.k), ']'))
  ) AS x_value
FROM tbl1 AS t,
JSON_TABLE(
  JSON_KEYS(JSON_EXTRACT(t.doc, '$.x')),
  '$[*]' COLUMNS (k VARCHAR(255) PATH '$')
) AS j
WHERE t.id = 1
ORDER BY x_key
LIMIT 500;

/* ===== 4) Проверка CTE (WITH RECURSIVE) ===== */
WITH RECURSIVE seq(n) AS (
  SELECT 0
  UNION ALL
  SELECT n + 1 FROM seq WHERE n + 1 <= 9
)
SELECT * FROM seq;

/* ===== 5) CTE + JSON: первые 3 элемента из массива z ===== */
WITH RECURSIVE seq(n) AS (
  SELECT 0
  UNION ALL
  SELECT n + 1 FROM seq WHERE n + 1 <= 2  -- индексы 0..2
)
SELECT
  s.n AS idx0,
  JSON_UNQUOTE(JSON_EXTRACT(t.doc, CONCAT('$.z[', s.n, ']'))) AS z_value
FROM tbl1 t
JOIN seq s ON s.n < JSON_LENGTH(JSON_EXTRACT(t.doc, '$.z'))
WHERE t.id = 1
ORDER BY s.n;

/* ===== 6) Таблица tbl2 + JSON_TABLE для массива объектов ===== */
CREATE TABLE tbl2 (
  id  INT PRIMARY KEY,
  doc JSON NOT NULL
);

INSERT INTO tbl2 (id, doc) VALUES
(1, JSON_OBJECT(
  'items', JSON_ARRAY(
     JSON_OBJECT('name','Alice','score',95),
     JSON_OBJECT('name','Bob','score',88),
     JSON_OBJECT('name','Cara','score',76)
  )
));

SELECT
  jt.ord,
  jt.name,
  jt.score
FROM tbl2 t
CROSS JOIN JSON_TABLE(
  t.doc,
  '$.items[*]' COLUMNS (
    ord   FOR ORDINALITY,
    name  VARCHAR(100) PATH '$.name',
    score INT          PATH '$.score'
  )
) jt
WHERE t.id = 1
ORDER BY jt.ord;
