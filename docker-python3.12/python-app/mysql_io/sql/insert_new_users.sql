WITH new_users AS (
  INSERT INTO school_sheduller.core_users (name, phone)
  VALUES
    ('Alice',  '+49111111111'),
    ('Bob',    '+49222222222'),
    ('Charlie','+49333333333')
  RETURNING id
)
INSERT INTO school_sheduller.core_versions (user_id)
SELECT id
FROM new_users;

select VERSION();