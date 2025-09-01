import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus
from input_data_OptimizationWeights_types import InputData
from pprint import pprint


def _create_db_engine(db_path: str):
    """Создает 'движок' SQLAlchemy для подключения к базе MS Access."""
    conn_str_raw = (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        fr"DBQ={db_path};"
    )
    quoted_conn_str = quote_plus(conn_str_raw)
    return create_engine(f"access+pyodbc:///?odbc_connect={quoted_conn_str}")


def load_data_from_access(db_path: str) -> InputData:
    """
    Подключается к базе данных MS Access, загружает все необходимые данные
    из предопределенных представлений (v*) и возвращает заполненный объект InputData.
    """
    engine = _create_db_engine(db_path)

    # --- Вспомогательные функции для чистоты кода ---

    def get_list(view_name: str, column_name: str) -> list:
        """Читает один столбец из представления и возвращает как Python list."""
        try:
            df = pd.read_sql(f"SELECT {column_name} FROM {view_name}", engine)
            # return df[column_name].tolist()
            # Очищаем строки от лишних пробелов и символов переноса
            # return df[column_name].str.strip().tolist()
            return df[column_name].str.replace(r'\s+', ' ', regex=True).str.strip().tolist()


        except Exception as e:
            print(f"ВНИМАНИЕ: Не удалось загрузить {view_name}. Возвращен пустой список. Ошибка: {e}")
            return []

    def get_dict(view_name: str, key_cols: list, value_col: str, print_dict: bool = False) -> dict:
        """Читает представление и возвращает как словарь { (ключи): значение }."""
        try:
            df = pd.read_sql(f"SELECT * FROM {view_name}", engine)
            if df.empty:
                return {}

            # Очищаем все строковые столбцы от лишних пробелов и символов переноса.
            # Это касается и ключей, и значений будущего словаря.
            for col in df.columns:
                # Проверяем, что тип столбца - 'object', что обычно означает строки в pandas
                if df[col].dtype == 'object':
                    # df[col] = df[col].str.strip()
                    df[col] = df[col].str.replace(r'\s+', ' ', regex=True).str.strip()

            # Явное преобразование столбца со значениями в числовой, а затем в целый тип.
            # Это решает проблему с float (например, 2.0 вместо 2)
            df[value_col] = pd.to_numeric(df[value_col], errors='coerce').fillna(0).astype(int)

            # Устанавливаем колонки-ключи как индекс и преобразуем оставшуюся колонку в словарь
            dict1 = df.set_index(key_cols)[value_col].to_dict()
            if print_dict:
                pprint(dict1)
            return dict1

        except Exception as e:
            print(f"ВНИМАНИЕ: Не удалось загрузить {view_name}. Возвращен пустой словарь. Ошибка: {e}")
            return {}

    # --- Загрузка данных из ваших представлений в Access ---
    # Предполагается, что вы создали представления с именами vClasses, vSubjects и т.д.

    # 1. Простые списки
    # classes = ["5A", "5B"]
    classes = get_list("vCLASS", "NAIME")
    # subjects = ["math", "cs", "eng", "labor", "history"]
    subjects = get_list("vSubject_all", "NAIME")


    # teachers = ["Ivanov E K ", "Petrov", "Sidorov", "Nikolaev", "Smirnov", "Voloshin"]
    teachers = get_list("vTeacher", "NAIME")

    # split_subjects = {"eng", "cs", "labor"}
    split_subjects = set(get_list("vSubject_split", "NAIME"))

    # 2. Словари (учебные планы, назначения)
    # plan_hours = {("5A", "math"): 2, ("5B", "math"): 2, ...}
    plan_hours = get_dict("vНагрузка_по_классам", ["CLASS", "Subject"], "Hours")
    # print(plan_hours)
    # print(type(plan_hours))

    # subgroup_plan_hours = {("5A", "eng", 1): 2, ("5A", "eng", 2): 2, ...}
    subgroup_plan_hours = get_dict("v_subgroup_plan_hours", ["CLASS", "SubjectName", "Subgroup"], "Hours")
    # print(subgroup_plan_hours)
    # print(type(subgroup_plan_hours))


    # assigned_teacher = {("5A", "math"): "Ivanov E K ", ...}
    assigned_teacher = get_dict("v_assigned_teacher", ["CLASS", "SubjectName"], "Teacher",)
    # return

    # subgroup_assigned_teacher = {("5A", "eng", 1): "Sidorov", ...}
    subgroup_assigned_teacher = get_dict("v_subgroup_assigned_teacher", ["ClassName", "SubjectName", "SUBGROUP"], "TeacherName",)


    # 3. Более сложные структуры
    # days_off = {"Petrov": {"Mon", "Tue"}}
    df_days_off = pd.read_sql("SELECT * FROM v_days_off", engine)
    days_off = df_days_off.groupby('TeacherName')['DayName'].apply(set).to_dict() if not df_days_off.empty else {}
    # pprint (days_off)

    # Жесткие запреты на слоты для классов
    # forbidden_slots = {('5A', 'Mon', 1), ('5A', 'Tue', 2)}
    df_forbidden = pd.read_sql("SELECT * FROM v_forbidden_slots", engine)
    # forbidden_slots = set(map(tuple, df_forbidden.to_records(index=False)))
    forbidden_slots = {(rec[0], rec[1], int(rec[2])) for rec in df_forbidden.to_records(index=False)}

    # pprint(forbidden_slots)


    # Веса для предпочтений
    # class_slot_weight = {("5A", "Fri", 7): 10.0, ("5A", "Fri", 6): 5.0}
    # Штраф или бонус за назначение урока классу 'c' в конкретный день 'd' и период 'p'.
    class_slot_weight = get_dict("v_class_slot_weight", ["ClassName", "day_of_week", "slot"], "weight")
    # pprint(class_slot_weight)

    #       Штраф или бонус за назначение урока учителю 't' в конкретный день 'd' и период 'p'.
    # teacher_slot_weight = {("Petrov", "Tue", 1): 8.0}
    teacher_slot_weight = get_dict("v_teacher_slot_weight", ["TeacherName", "day_of_week", "slot"], "weight")
    # pprint(teacher_slot_weight)

    # class_subject_day_weight = {("5B", "math", "Mon"): 6.0}
    class_subject_day_weight = get_dict("v_class_subject_day_weight", ["ClassName", "SubjectName", "day_of_week"], "weight",)


    # Совместимость пар
    # compatible_pairs = {('cs', 'eng')}
    df_compat = pd.read_sql("SELECT * FROM v_сompatible_pairs", engine)
    compatible_pairs = {tuple(sorted(pair)) for pair in df_compat.to_records(index=False)}
    # pprint(compatible_pairs)

    # days=["Mon", "Tue", "Wed", "Thu", "Fri"]
    days = get_list("сп_days_of_week", "day_of_week")
    # pprint(days)


    # --- Сборка и возврат объекта InputData ---
    return InputData(
        days=days,
        periods=list(range(1, 9)),
        classes=classes, subjects=subjects, teachers=teachers,
        split_subjects=split_subjects,
        plan_hours=plan_hours, subgroup_plan_hours=subgroup_plan_hours,
        assigned_teacher=assigned_teacher, subgroup_assigned_teacher=subgroup_assigned_teacher,
        days_off=days_off,
        forbidden_slots=forbidden_slots,
        class_slot_weight=class_slot_weight,
        teacher_slot_weight=teacher_slot_weight,
        class_subject_day_weight=class_subject_day_weight,
        compatible_pairs=compatible_pairs
    )


if __name__ == '__main__':
    from pprint import pprint

    # Путь к базе данных для тестового запуска
    db_path_for_test = r"F:/_prg/python/OR-Tools-MILP/src/db/rasp3.accdb"

    print(f"--- Запускаем тестовую загрузку данных из {db_path_for_test} ---")
    data_from_db = load_data_from_access(db_path_for_test)

    print("\n--- Результат: загруженный объект InputData ---")
    # Используем pprint для красивого вывода dataclass
    pprint(data_from_db)