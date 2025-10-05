drop trigger school_sheduller.core_users_ai;

DELIMITER //

CREATE TRIGGER school_sheduller.core_users_ai
AFTER INSERT ON school_sheduller.core_users
FOR EACH ROW
BEGIN
# comment добавляется инструкцией default в таблице
  INSERT INTO school_sheduller.core_versions (user_id)   VALUES (NEW.id);
END//

DELIMITER ;
