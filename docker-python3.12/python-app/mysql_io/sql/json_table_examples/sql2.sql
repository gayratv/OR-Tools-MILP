# Пример 2. Вложенные массивы + NESTED PATH

CREATE TABLE customers (
  customer_id INT PRIMARY KEY,
  profile JSON NOT NULL
);

INSERT INTO customers VALUES
(1, JSON_OBJECT(
  'name','Alice',
  'orders', JSON_ARRAY(
     JSON_OBJECT('no','A-1','lines', JSON_ARRAY(
        JSON_OBJECT('sku','P1','qty',1),
        JSON_OBJECT('sku','P2','qty',2)
     )),
     JSON_OBJECT('no','A-2','lines', JSON_ARRAY(
        JSON_OBJECT('sku','P3','qty',5)
     ))
  )
)),
(2, JSON_OBJECT(
  'name','Bob',
  'orders', JSON_ARRAY(
     JSON_OBJECT('no','B-1','lines', JSON_ARRAY(
        JSON_OBJECT('sku','P2','qty',1),
        JSON_OBJECT('sku','P3','qty',1)
     ))
  )
));

# Запрос: вытянем клиента → заказы → позиции.
SELECT
  c.customer_id,
  jt.cust_name,
  jt.order_no,
  jt.line_sku,
  jt.line_qty
FROM customers c
JOIN JSON_TABLE(
  c.profile, '$'
  COLUMNS (
    cust_name VARCHAR(50) PATH '$.name',
    NESTED PATH '$.orders[*]'
      COLUMNS (
        order_no  VARCHAR(20) PATH '$.no',
        NESTED PATH '$.lines[*]'
          COLUMNS (
            line_sku VARCHAR(20) PATH '$.sku',
            line_qty INT         PATH '$.qty'
          )
      )
  )
) AS jt ON 1=1
ORDER BY c.customer_id, jt.order_no, jt.line_sku;
