# Пример 1. «Позиции заказа» из JSON-массива

CREATE TABLE orders (
  order_id INT PRIMARY KEY,
  items JSON NOT NULL
);

INSERT INTO orders (order_id, items) VALUES
(101, JSON_ARRAY(
  JSON_OBJECT('sku','P1','qty',2,'price',19.99),
  JSON_OBJECT('sku','P2','qty',1,'price',5.50)
)),
(102, JSON_ARRAY(
  JSON_OBJECT('sku','P1','qty',3,'price',19.99),
  JSON_OBJECT('sku','P3','qty',2,'price',12.00)
));

SELECT
  o.order_id,
  jt.sku,
  jt.qty,
  jt.price,
  (jt.qty * jt.price) AS line_total
FROM orders AS o
JOIN JSON_TABLE(
  o.items, '$[*]' COLUMNS (
    sku   VARCHAR(20)  PATH '$.sku',
    qty   INT          PATH '$.qty'
        DEFAULT '0' ON EMPTY
        DEFAULT '0' ON ERROR,
    price DECIMAL(10,2) PATH '$.price' NULL ON ERROR
  )
) AS jt ON 1=1
ORDER BY o.order_id, jt.sku;

-- агрегирование по заказу:
SELECT
  o.order_id,
  SUM(jt.qty * jt.price) AS order_total
FROM orders o
JOIN JSON_TABLE(
  o.items, '$[*]' COLUMNS (
    qty   INT           PATH '$.qty',
    price DECIMAL(10,2) PATH '$.price'
  )
) jt ON 1=1
GROUP BY o.order_id;

SELECT VERSION();