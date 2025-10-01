# Пример 3. Индекс элемента и проверка наличия поля (FOR ORDINALITY, EXISTS PATH)

CREATE TABLE product_attrs (
  sku VARCHAR(20) PRIMARY KEY,
  attrs JSON NOT NULL
);

INSERT INTO product_attrs VALUES
('P1', JSON_OBJECT('tags', JSON_ARRAY('popular','new'), 'discount', 5)),
('P2', JSON_OBJECT('tags', JSON_ARRAY('clearance'))),
('P3', JSON_OBJECT('tags', JSON_ARRAY('bundled','gift')));


# Запрос 3a: распакуем теги с позицией.
SELECT
  pa.sku,
  jt.pos ,  -- 1,2,3,...
  jt.tag
FROM product_attrs pa
JOIN JSON_TABLE(
  pa.attrs, '$.tags[*]'
  COLUMNS(
    pos  FOR ORDINALITY,
    tag VARCHAR(30) PATH '$'
  )
) jt ON 1=1
ORDER BY pa.sku, jt.pos;

# Запрос 3b: есть ли скидка у товара?
SELECT
  pa.sku,
  jt.has_discount
FROM product_attrs pa
JOIN JSON_TABLE(
  pa.attrs, '$'
  COLUMNS(
    has_discount INT EXISTS PATH '$.discount'
  )
) jt ON 1=1
ORDER BY pa.sku;
