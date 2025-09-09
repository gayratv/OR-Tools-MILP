import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus
from input_data import InputData, ClassInfo
from pprint import pprint
from sqlalchemy import text
from typing import Dict, Set, List
import re


def _create_db_engine(db_path: str):
    """Создает 'движок' SQLAlchemy для подключения к базе MS Access."""
    conn_str_raw = (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        fr"DBQ={db_path};"
    )
    quoted_conn_str = quote_plus(conn_str_raw)
    return create_engine(f"access+pyodbc:///?odbc_connect={quoted_conn_str}")


def _sanitize_lp_name(name: str) -> str:
    """
    Заменяет символы в строке, которые могут вызвать проблемы в LP-файлах,
    на безопасные для создания валидного идентификатора.
    """
    if not isinstance(name, str):
        return str(name)
    # Заменяем последовательности пробелов и других проблемных символов на один '_'.
    # Это помогает избежать ошибок парсинга в решателях вроде HiGHS.
    return re.sub(r'[\s/.():\-]+', '_', name)


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
            # Очищаем строки от лишних пробелов и санитайзим для LP-формата.
            return df[column_name].str.strip().apply(_sanitize_lp_name).tolist()


        except Exception as e:
            print(f"ВНИМАНИЕ: Не удалось загрузить {view_name}. Возвращен пустой список. Ошибка: {e}")
            return []

    # def get_dict(view_name: str, key_cols: list, value_col: str, print_dict: bool = False) -> dict:
    def get_dict(view_name: str, key_cols: list, value_col: str, value_is_numeric: bool = False, print_dict: bool = False) -> dict:

        """Читает представление и возвращает как словарь { (ключи): значение }."""
        try:
            df = pd.read_sql(f"SELECT * FROM {view_name}", engine)
            if df.empty:
                return {}

            # Очищаем и санитайзим все строковые столбцы.
            # Это касается и ключей, и строковых значений будущего словаря.
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].str.strip().apply(_sanitize_lp_name)

            # Явное преобразование столбца со значениями в числовой, а затем в целый тип.
            # Это решает проблему с float (например, 2.0 вместо 2)
            if value_is_numeric:
                # Явное преобразование столбца со значениями в числовой, а затем в целый тип.
                # Это решает проблему с float (например, 2.0 вместо 2).
                df[value_col] = pd.to_numeric(df[value_col], errors='coerce').fillna(0).astype(int)

            # Устанавливаем колонки-ключи как индекс и преобразуем оставшуюся колонку в словарь
            dict1 = df.set_index(key_cols)[value_col].to_dict()
            if print_dict:
                pprint(dict1)
            return dict1

        except Exception as e:
            print(f"ВНИМАНИЕ: Не удалось загрузить {view_name}. Возвращен пустой словарь. Ошибка: {e}")
            return {}

    def get_class_info_list(view_name: str) -> List[ClassInfo]:
        """Читает представление и возвращает список объектов ClassInfo."""
        try:
            df = pd.read_sql(f"SELECT * FROM {view_name}", engine)
            if df.empty:
                return []

            return [ClassInfo(name=row['класс_eng'], grade=int(row['grade'])) for _, row in df.iterrows()]
        except Exception as e:
            print(f"ВНИМАНИЕ: Не удалось загрузить {view_name}. Возвращен пустой список ClassInfo. Ошибка: {e}")
            return []

    # --- Загрузка данных из ваших представлений в Access ---
    # Предполагается, что вы создали представления с именами vClasses, vSubjects и т.д.

    # 1. Списки
    classes = get_class_info_list("vCLASS")
    # print(classes)
    # return


    # subjects = ["math", "cs", "eng", "labor", "history"]
    subjects = get_list("vSubject_all", "предмет_eng")


    # teachers = ["Ivanov E K ", "Petrov", "Sidorov", "Nikolaev", "Smirnov", "Voloshin"]
    teachers = get_list("vTeacher", "teacher")

    # split_subjects = {"eng", "cs", "labor"}
    split_subjects = set(get_list("vSubject_split", "предмет_eng"))

    # paired_subjects = {"labor"}
    paired_subjects = set(get_list("vPaired_subjects", "предмет_eng"))

    # 2. Словари (учебные планы, назначения)
    # plan_hours = {("5A", "math"): 2, ("5B", "math"): 2, ...}
    plan_hours = get_dict("vНагрузка_по_классам", ["класс_eng", "предмет_eng"], "Hours",value_is_numeric=True)
    # pprint(plan_hours)
    # return

    # subgroup_plan_hours = {("5A", "eng", 1): 2, ("5A", "eng", 2): 2, ...}
    subgroup_plan_hours = get_dict("v_subgroup_plan_hours", ["класс_eng", "предмет_eng", "ПОДГРУППА Idgg"], "Hours",value_is_numeric=True)
    # pprint(subgroup_plan_hours)
    # return


    # assigned_teacher = {("5A", "math"): "Ivanov E K ", ...}
    assigned_teacher = get_dict("v_assigned_teacher", ["класс_eng", "предмет_eng"], "teacher")
    # pprint(assigned_teacher)

    # subgroup_assigned_teacher = {("5A", "eng", 1): "Sidorov", ...}
    subgroup_assigned_teacher = get_dict("v_subgroup_assigned_teacher", ["класс_eng", "предмет_eng", "ПОДГРУППА Idgg"], "teacher",)
    # pprint(subgroup_assigned_teacher)
    # return


    # 3. Более сложные структуры
    # days_off = {"Petrov": {"Mon", "Tue"}}
    df_days_off = pd.read_sql("SELECT * FROM v_days_off", engine)
    if not df_days_off.empty:
        # Санитайзим имена учителей, чтобы они совпадали с основным списком учителей
        df_days_off['TeacherName'] = df_days_off['TeacherName'].str.strip().apply(_sanitize_lp_name)
    days_off = df_days_off.groupby('TeacherName')['DayName'].apply(set).to_dict() if not df_days_off.empty else {}
    # pprint (days_off)
    # return

    # Жесткие запреты на слоты для классов
    # forbidden_slots = {('5A', 'Mon', 1), ('5A', 'Tue', 2)}
    df_forbidden = pd.read_sql("SELECT * FROM v_forbidden_slots", engine)
    if not df_forbidden.empty:
        # Санитайзим имена классов
        class_col_name = df_forbidden.columns[0] # Предполагаем, что первый столбец - имя класса
        if df_forbidden[class_col_name].dtype == 'object':
            df_forbidden[class_col_name] = df_forbidden[class_col_name].str.strip().apply(_sanitize_lp_name)
    forbidden_slots = {(rec[0], rec[1], int(rec[2])) for rec in df_forbidden.to_records(index=False)}

    # pprint(forbidden_slots)
    # return


    # Веса для предпочтений
    # class_slot_weight = {("5A", "Fri", 7): 10.0, ("5A", "Fri", 6): 5.0}
    # Штраф или бонус за назначение урока классу 'c' в конкретный день 'd' и период 'p'.
    class_slot_weight = get_dict("v_class_slot_weight", ["ClassName", "day_of_week", "slot"], "weight",value_is_numeric=True)
    # pprint(class_slot_weight)
    # return

    #       Штраф или бонус за назначение урока учителю 't' в конкретный день 'd' и период 'p'.
    # teacher_slot_weight = {("Petrov", "Tue", 1): 8.0}
    teacher_slot_weight = get_dict("v_teacher_slot_weight", ["TeacherName", "day_of_week", "slot"], "weight",value_is_numeric=True)
    # pprint(teacher_slot_weight)
    # return

    # class_subject_day_weight = {("5B", "math", "Mon"): 6.0}
    class_subject_day_weight = get_dict("v_class_subject_day_weight", ["ClassName", "SubjectName", "day_of_week"], "weight",value_is_numeric=True)

    # Совместимость пар
    # compatible_pairs = {('cs', 'eng')}
    df_compat = pd.read_sql("SELECT * FROM v_сompatible_pairs", engine)
    if not df_compat.empty:
        # Санитайзим имена предметов в обеих колонках
        for col in df_compat.columns:
            if df_compat[col].dtype == 'object':
                df_compat[col] = df_compat[col].str.strip().apply(_sanitize_lp_name)
    compatible_pairs = {tuple(sorted(pair)) for pair in df_compat.to_records(index=False)}
    # pprint(compatible_pairs)
    # return

    # days=["Mon", "Tue", "Wed", "Thu", "Fri"]
    days = get_list("сп_days_of_week", "day_of_week")
    # pprint(days)
    # return

    english_subject_name = "Eng"

    # Явные запреты слотов у преподавателей: teacher -> [(day, period), ...]
    # учитель не работает в этот день и слот
    # teacher_forbidden_slots = {
    #     "Petrov": [("Tue", 1)],
    #     "Nikolaev": [("Thu", 7)],
    # }
    teacher_forbidden_slots: Dict[str, list] = {}
    try:
        df_teacher_forbidden = pd.read_sql("SELECT * FROM v_teacher_forbidden_slots", engine)
        if not df_teacher_forbidden.empty:
            # Группируем по учителю и собираем кортежи (день, слот) в список
            teacher_forbidden_slots = (
                df_teacher_forbidden.groupby('teacher')[['DayName', 'slot']]
                .apply(lambda x: [tuple(y) for y in x.to_numpy()], include_groups=False)
                .to_dict()
            )
    except Exception as e:
        print(f"ВНИМАНИЕ: Не удалось загрузить v_teacher_forbidden_slots. Возвращен пустой словарь. Ошибка: {e}")

    # pprint(teacher_forbidden_slots)
    # return

    # Максимальное число уроков в день по параллели, например {2: 4, 3: 5, 4: 5}
    # grade_max_lessons_per_day=  {2: 4, 3: 5, 4: 5}
    grade_max_lessons_per_day = get_dict(
        "сп_макс_уроков_в_день",
        key_cols=["grade"],
        value_col="max_lessons_per_day",
        value_is_numeric=True)
    # pprint(grade_max_lessons_per_day)
    # return

    # subjects_not_last_lesson={5: {"math"}, 7: {"math", "physics"}}
    subjects_not_last_lesson: Dict[int, set] = {}
    try:
        df_not_last = pd.read_sql("SELECT * FROM v_subjects_not_last_lesson", engine)
        if not df_not_last.empty:
            # Группируем по параллели (grade) и собираем предметы в множество (set)
            subjects_not_last_lesson = df_not_last.groupby('grade')['subject'].apply(set).to_dict()
    except Exception as e:
        print(f"ВНИМАНИЕ: Не удалось загрузить v_subjects_not_last_lesson. Возвращен пустой словарь. Ошибка: {e}")
    # pprint(subjects_not_last_lesson)
    # return

    # elementary_english_periods
    # Разрешённые номера уроков для английского в начальной школе. Пример: {2, 3, 4}.

    elementary_english_periods: Set[int] = set()
    try:
        # Предполагается, что существует представление 'v_elementary_english_periods'
        # со столбцом 'period_number', содержащим разрешенные номера уроков.
        df_elem_eng_periods = pd.read_sql("SELECT period_number FROM elementary_english_periods", engine)
        if not df_elem_eng_periods.empty:
            # Преобразуем столбец в набор целых чисел
            elementary_english_periods = set(df_elem_eng_periods['period_number'].astype(int).tolist())
    except Exception as e:
        print(f"ВНИМАНИЕ: Не удалось загрузить v_elementary_english_periods. Возвращен пустой набор. Ошибка: {e}")
    # pprint(elementary_english_periods)
    # return

    # grade_subject_max_consecutive_days
    # Ограничения по максимальному числу подряд идущих дней, когда у параллели может быть один и тот же предмет. Пример: {3: {"PE": 2}}.

    grade_subject_max_consecutive_days: Dict[int, Dict[str, int]] = {}
    try:
        # Предполагается, что существует представление 'v_grade_subject_max_consecutive_days'
        # со столбцами 'grade', 'subject', 'max_days'.
        df_max_days = pd.read_sql("SELECT * FROM v_grade_subject_max_consecutive_days", engine)
        if not df_max_days.empty:
            # Группируем по 'grade', а затем для каждой группы создаем вложенный словарь {subject: max_days}
            for grade, group in df_max_days.groupby('grade'):
                grade_subject_max_consecutive_days[int(grade)] = (
                    group.set_index('subject')['max_days'].astype(int).to_dict()
                )
    except Exception as e:
        print(f"ВНИМАНИЕ: Не удалось загрузить v_grade_subject_max_consecutive_days. Возвращен пустой словарь. Ошибка: {e}")
    # pprint(grade_subject_max_consecutive_days)
    # return
    
    # must_sync_split_subjects
    # Набор сплит-предметов, которые должны вестись синхронно у всех подгрупп.
    # must_sync_split_subjects = {"labor"}
    must_sync_split_subjects = set(get_list("v_must_sync_split_subjects", "subject_name"))
    # pprint(must_sync_split_subjects)
    # return

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
        compatible_pairs=compatible_pairs,
        paired_subjects=paired_subjects,
        english_subject_name=english_subject_name,
        teacher_forbidden_slots=teacher_forbidden_slots,
        grade_max_lessons_per_day=grade_max_lessons_per_day,
        subjects_not_last_lesson=subjects_not_last_lesson,
        elementary_english_periods=elementary_english_periods,
        grade_subject_max_consecutive_days=grade_subject_max_consecutive_days,
        must_sync_split_subjects=must_sync_split_subjects
    )


def load_display_maps(db_path: str) -> Dict[str, Dict[str, str]]:
    """
    Загружает из базы данных словари для сопоставления
    технических (английских) названий с полными (русскими) для отчетов.
    """
    if not db_path:
        return {}

    print("--- Загрузка словарей для отображения результатов ---")
    engine = _create_db_engine(db_path)

    try:

        subject_map = pd.read_sql('SELECT "предмет_eng", "предмет" FROM "з_excel_предметы"', engine)

        teacher_map = pd.read_sql('SELECT "teacher", "FAMIO" FROM "з_excel_учителя"', engine)

        return {
            "subject_names": subject_map.set_index('предмет_eng')['предмет'].to_dict(),
            "teacher_names": teacher_map.set_index('teacher')['FAMIO'].to_dict()
        }
    except Exception as e:
        print(f"ОШИБКА при загрузке словарей для отображения: {e}")
        return {}


if __name__ == '__main__':
    from pprint import pprint

    # Путь к базе данных для тестового запуска
    db_path_for_test = r"F:/_prg/python/OR-Tools-MILP/src/db/rasp3-new-calculation.accdb"
    # db_path_for_test = r"F:/_prg/python/OR-Tools-MILP/src/db/rasp3.accdb"

    print(f"--- Запускаем тестовую загрузку данных из {db_path_for_test} ---")
    data_from_db = load_data_from_access(db_path_for_test)

    print("\n--- Результат: загруженный объект InputData ---")
    # Используем pprint для красивого вывода dataclass
    pprint(data_from_db)