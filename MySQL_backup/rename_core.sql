-- alter.sql
-- Скрипт для переименования таблиц с целью улучшения структуры и читаемости схемы БД.

-- Переименование таблиц, относящихся к ядру приложения (пользователи и задания)
-- с добавлением префикса `core_`.
-- Переименование таблиц с результатами расчетов с добавлением префикса `calc_`.

RENAME TABLE
  `users` TO `core_users`,
  `jobs` TO `core_jobs`,
  `calculation_results` TO `calc_results`,
  `schedule_details` TO `calc_schedule_details`;
