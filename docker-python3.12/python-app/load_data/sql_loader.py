import pandas as pd
from data_types.input_data import InputData, ClassInfo
from typing import Dict, Set, List, Tuple
import re
from mysql_io.sql_connector_pool import Database

db = Database()


def _sanitize_lp_name(name: str) -> str:
    """
    Заменяет символы в строке, которые могут вызвать проблемы в LP-файлах,
    на безопасные для создания валидного идентификатора.
    """
    if not isinstance(name, str):
        return str(name)
    # Заменяем последовательности пробелов и других проблемных символов на один '_'.
    # Это помогает избежать ошибок парсинга в решателях вроде HiGHS.
    return re.sub(r'[\\s/.():\\-]+', '_', name)


def load_data_from_sql(user_id: int, version_id: int) -> InputData:
    """
    Подключается к базе данных MS Access, загружает все необходимые данные
    из предопределенных представлений (v*) и возвращает заполненный объект InputData.
    """

    # --- Вспомогательные функции для чистоты кода ---

    def get_list(sql_query: str, column_name: str) -> list:
        """Читает один столбец из представления и возвращает как Python list."""
        try:
            df = db.fetch_all(sql_query, (version_id,))
            return [d[column_name] for d in df]


        except Exception as e:
            print(f"ВНИМАНИЕ: Не удалось загрузить {sql_query}. Возвращен пустой список. Ошибка: {e}")
            return []

    def get_dict(sql_query: str, key_cols: list, value_col: str,
                 value_is_numeric: bool = False,
                 print_dict: bool = False) -> dict:

        """Читает представление и возвращает как словарь { (ключи): значение }."""
        try:
            data = db.fetch_all(sql_query, (version_id,))
            if not data:
                return {}

            df = pd.DataFrame(data)
            if df.empty:
                return {}

            if value_is_numeric:
                # Явное преобразование столбца со значениями в числовой, а затем в целый тип.
                # Это решает проблему с float (например, 2.0 вместо 2). используем pandas
                df[value_col] = pd.to_numeric(df[value_col], errors='coerce').fillna(0).astype(int)

            # Устанавливаем колонки-ключи как индекс и преобразуем оставшуюся колонку в словарь
            dict1 = df.set_index(key_cols)[value_col].to_dict()
            if print_dict:
                pprint(dict1)
            return dict1
        except Exception as e:
            print(f"ВНИМАНИЕ: Не удалось загрузить {sql_query}. Возвращен пустой словарь. Ошибка: {e}")
            return {}

    def get_class_info_list(sql_query: str, version_id : int) -> List[ClassInfo]:
        """Читает представление и возвращает список объектов ClassInfo."""
        try:
            df = db.fetch_all(sql_query, (version_id,))

            return [ClassInfo(name=row['name_eng'], grade=int(row['grade'])) for row in df]
        except Exception as e:
            print(f"ВНИМАНИЕ: Не удалось загрузить {sql_query}. Возвращен пустой список ClassInfo. Ошибка: {e}")
            return []

    # --- Загрузка данных из ваших представлений в Access ---
    # Предполагается, что вы создали представления с именами vClasses, vSubjects и т.д.

    # 1. Списки
    classes = get_class_info_list("select name_eng, training_year as grade from input_classes where version_id = %s", version_id)
    # print(classes)
    # return

    # subjects = ["math", "cs", "eng", "labor", "history"]
    subjects = get_list("select name_eng from input_subjects where version_id = %s", "name_eng")
    # print(subjects)
    # return


    # teachers = ["Ivanov E K ", "Petrov", "Sidorov", "Nikolaev", "Smirnov", "Voloshin"]
    teachers = get_list("select name_eng from input_teachers where version_id = %s", "name_eng")
    # print(teachers)
    # return


    # split_subjects = {"eng", "cs", "labor"}
    split_subjects = set(get_list("select name_eng from input_subjects where version_id=%s and is_split_subject=true", "name_eng"))
    # print(split_subjects)
    # return

    # paired_subjects = {"labor"}
    # select s.name_eng
    # from input_paired_subjects ps
    #          inner join
    #      input_subjects s
    #      on s.id = ps.paired_subject_id and ps.version_id = s.version_id
    # where ps.version_id = 1
    query = """
            SELECT s.name_eng
            FROM input_paired_subjects ps
                     INNER JOIN input_subjects s
                                ON s.id = ps.paired_subject_id
                                    AND ps.version_id = s.version_id
            WHERE ps.version_id = %s 
            """

    paired_subjects = set(get_list(query, "name_eng"))
    # print(paired_subjects)
    # return

    # 2. Словари (учебные планы, назначения)
    # plan_hours = {("5A", "math"): 2, ("5B", "math"): 2, ...}
    query="""
        select cl.name_eng as class, sbjct.name_eng as subject, ta.weekly_hours, sbjct.is_split_subject
        from input_teacher_assignments ta
         inner join input_classes cl on
            cl.id = ta.class_id and ta.version_id = cl.version_id
         inner join input_calculated_years cy on
            cy.version_id = cl.version_id and
            cl.training_year = cy.training_year
         inner join input_subjects sbjct on
            sbjct.id = ta.subject_id and ta.version_id = sbjct.version_id
        where ta.version_id = %s
          and sbjct.is_split_subject = false;
    """
    plan_hours = get_dict(query, key_cols=["class", "subject"], value_col="weekly_hours", value_is_numeric=True)
    # pprint(plan_hours)
    # return


    # subgroup_plan_hours = {("5A", "eng", 1): 2, ("5A", "eng", 2): 2, ...}
    query="""
        select cl.name_eng as class, sbjct.name_eng as subject,ta.subgroup_id ,ta.weekly_hours, sbjct.is_split_subject
        from input_teacher_assignments ta
                 inner join input_classes cl on
                    cl.id = ta.class_id and ta.version_id = cl.version_id
                 inner join input_calculated_years cy on
                    cy.version_id = cl.version_id and
                    cl.training_year = cy.training_year
                 inner join input_subjects sbjct on
                    sbjct.id = ta.subject_id and ta.version_id = sbjct.version_id
        where ta.version_id = %s
            and sbjct.is_split_subject = true
            and ta.subgroup_id >0;
    """
    subgroup_plan_hours = get_dict(query,
                                   key_cols=["class", "subject", "subgroup_id"],
                                   value_col= "weekly_hours",
                                   value_is_numeric=True)
    # pprint(subgroup_plan_hours)
    # return

    # assigned_teacher = {("5A", "math"): "Ivanov E K ", ...}
    query="""
        select cl.name_eng as class, sbjct.name_eng as subject,teach.name_eng as teacher, sbjct.is_split_subject
        from input_teacher_assignments ta
         inner join input_classes cl on
            cl.id = ta.class_id and ta.version_id = cl.version_id
         inner join input_calculated_years cy on
            cy.version_id = cl.version_id and
            cl.training_year = cy.training_year
         inner join input_subjects sbjct on
            sbjct.id = ta.subject_id and ta.version_id = sbjct.version_id
         inner join input_teachers teach on
            teach.version_id=ta.version_id and
            teach.id=ta.teacher_id
        where ta.version_id = %s
          and sbjct.is_split_subject = false
    """
    assigned_teacher = get_dict(query,
                                   key_cols=["class", "subject"],
                                   value_col="teacher",
                                   value_is_numeric=False)
    # pprint(assigned_teacher)
    # return

    # subgroup_assigned_teacher = {("5A", "eng", 1): "Sidorov", ...}
    query="""
        select cl.name_eng as class, sbjct.name_eng as subject,teach.name_eng as teacher, ta.subgroup_id,sbjct.is_split_subject
        from input_teacher_assignments ta
                 inner join input_classes cl on
                    cl.id = ta.class_id and ta.version_id = cl.version_id
                 inner join input_calculated_years cy on
                    cy.version_id = cl.version_id and
                    cl.training_year = cy.training_year
                 inner join input_subjects sbjct on
                    sbjct.id = ta.subject_id and ta.version_id = sbjct.version_id
                inner join input_teachers teach on
                    teach.version_id=ta.version_id and
                    teach.id=ta.teacher_id
        where ta.version_id = %s
          and sbjct.is_split_subject = true    
    """
    subgroup_assigned_teacher = get_dict(query,
                                key_cols=["class", "subject","subgroup_id"],
                                value_col="teacher",
                                value_is_numeric=False)
    # pprint(subgroup_assigned_teacher)
    # return

    # 3. Более сложные структуры
    # days_off = {"Petrov": {"Mon", "Tue"}}
    query="""
        select t.name_eng as teacher,dw.day_of_week
        from input_teacher_days_off tdof
             inner join input_teachers t
                        on tdof.teacher_id = t.id
                            and tdof.version_id = t.version_id
             inner join input_days_of_week dw 
                        on tdof.day_of_week_id = dw.id
        where tdof.version_id = %s
    """
    days_off_data = db.fetch_all(query, (version_id,))
    days_off: Dict[str, Set[str]] = {}
    if days_off_data:
        df_days_off = pd.DataFrame(days_off_data)
        if not df_days_off.empty:
            days_off = df_days_off.groupby('teacher')['day_of_week'].apply(set).to_dict()

    # pprint(days_off)
    # return

    # Жесткие запреты на слоты для классов
    # forbidden_slots = {('5A', 'Mon', 1), ('5A', 'Tue', 2)}
    query="""
    select ic.name_eng as class,idow.day_of_week,icfs.slot_id from
     input_class_forbidden_slots icfs
        inner join input_classes ic
                 on icfs.class_id=ic.id and icfs.version_id=ic.version_id
        inner join input_calculated_years icy
                 on ic.training_year=icy.training_year and ic.version_id=icy.version_id
        inner join input_days_of_week idow
                 on idow.id=icfs.day_of_week_id
        where icfs.version_id = %s
    """
    # df_forbidden = pd.read_sql("SELECT * FROM v_forbidden_slots", engine)
    forbidden_slots_data = db.fetch_all(query, (version_id,))
    # forbidden_slots = {('5A', 'Mon', 1), ('5A', 'Tue', 2)}
    forbidden_slots: Set = set()
    if forbidden_slots_data:
        df_forbidden = pd.DataFrame(forbidden_slots_data)
        forbidden_slots = {(row['class'], row['day_of_week'], int(row['slot_id'])) for index, row in df_forbidden.iterrows()}

    # pprint(forbidden_slots)
    # return

    # Веса для предпочтений
    # class_slot_weight = {("5A", "Fri", 7): 10.0, ("5A", "Fri", 6): 5.0}
    # Штраф или бонус за назначение урока классу 'c' в конкретный день 'd' и период 'p'.
    query="""
        select ic.name_eng as class, idow.day_of_week, icsw.slot_id, icsw.weight
        from input_class_slot_weight icsw
                 inner join input_classes ic
                            on icsw.class_id = ic.id and icsw.version_id = ic.version_id
                 inner join input_calculated_years icy
                            on ic.training_year = icy.training_year and ic.version_id = icy.version_id
                 inner join input_days_of_week idow
                            on idow.id = icsw.day_of_week
        where icsw.version_id = %s   
    """
    class_slot_weight = get_dict(query, ["class", "day_of_week", "slot_id"], "weight",
                                 value_is_numeric=True)
    # pprint(class_slot_weight)
    # return

    #       Штраф или бонус за назначение урока учителю 't' в конкретный день 'd' и период 'p'.
    # teacher_slot_weight = {("Petrov", "Tue", 1): 8.0}
    query="""
        select t.name_eng as teacher,dw.day_of_week,tsw.slot_id,tsw.weight from
            input_teacher_slot_weight tsw
            inner join input_teachers t on t.id=tsw.teacher_id and t.version_id=tsw.version_id
            inner join input_days_of_week dw on dw.id=tsw.day_of_week_id
        where tsw.version_id = %s
    """
    teacher_slot_weight = get_dict(query, ["teacher", "day_of_week", "slot_id"], "weight",
                                   value_is_numeric=True)
    # pprint(teacher_slot_weight)
    # return

    # class_subject_day_weight = {("5B", "math", "Mon"): 6.0}
    query="""
        select c.name_eng as class,s.name_eng as subject,dw.day_of_week,csdw.weight from
        input_class_subject_day_weight csdw
        inner join input_subjects s on s.id=csdw.day_of_week_id and s.version_id=csdw.version_id
        inner join input_days_of_week dw on csdw.day_of_week_id=dw.id
        inner join input_classes c on c.id=csdw.class_id and c.version_id=csdw.version_id
        where csdw.version_id=%s    
    """
    # v_class_subject_day_weight
    class_subject_day_weight = get_dict(query, ["class", "subject", "day_of_week"],
                                        "weight", value_is_numeric=True)

    # Совместимость пар
    # compatible_pairs = {('cs', 'eng')}
    # SELECT * FROM v_сompatible_pairs
    query="""
        select s1.name_eng as subject1, s2.name_eng as subject2 from
        input_compatible_subject_pairs cp
        inner join input_subjects s1 on s1.id=cp.subject1_id and s1.version_id=cp.version_id
        inner join input_subjects s2 on s2.id=cp.subject2_id and s2.version_id=cp.version_id
        where cp.version_id=%s
    """
    compatible_pairs_data = db.fetch_all(query, (version_id,))
    compatible_pairs: Set[Tuple[str, str]] = set()
    if compatible_pairs_data:
        # Преобразуем список словарей в набор отсортированных кортежей
        compatible_pairs = {tuple(sorted(row.values())) for row in compatible_pairs_data}  # type: ignore
    # pprint(compatible_pairs)
    # return

    # days=["Mon", "Tue", "Wed", "Thu", "Fri"]
    query="""
        select day_of_week from input_days_of_week
    """
    df = db.fetch_all(query)
    days= [d["day_of_week"] for d in df]
    # print(days)


    # TODO: подумать как извлечь Eng
    # english_subject_name = "Eng"
    query="""
        select name_eng as english_name from input_subjects
        where name="Иностранный язык"
        and version_id=%s

    """
    english_subject_name=db.fetch_one(query,(version_id,))["english_name"]
    # print("english_subject_name ",english_subject_name)
    # return

    # Явные запреты слотов у преподавателей: teacher -> [(day, period), ...]
    # учитель не работает в этот день и слот
    # teacher_forbidden_slots = {
    #     "Petrov": [("Tue", 1)],
    #     "Nikolaev": [("Thu", 7)],
    # }
    #  SELECT * FROM v_teacher_forbidden_slots"
    query="""
        select t.name_eng as teacher,dw.day_of_week,tfs.slot_id from
            input_teacher_forbidden_slots tfs
            inner join input_teachers t on tfs.teacher_id=t.id and tfs.version_id=t.version_id
            inner join input_days_of_week dw on tfs.day_of_week_id=dw.id
        where tfs.version_id=%s
    """
    teacher_forbidden_slots: Dict[str, list] = {}
    try:
        teacher_forbidden_data = db.fetch_all(query, (version_id,))
        if teacher_forbidden_data:
            # Преобразуем список словарей в DataFrame
            df_teacher_forbidden = pd.DataFrame(teacher_forbidden_data)
            # Группируем по учителю и собираем кортежи (день, слот) в список
            # Имена столбцов 'day_of_week' и 'slot_id' взяты из SQL-запроса
            teacher_forbidden_slots = df_teacher_forbidden.groupby('teacher')[['day_of_week', 'slot_id']] \
                .apply(lambda g: [tuple(x) for x in g.to_numpy()], include_groups=False).to_dict()
    except Exception as e:
        print(f"ВНИМАНИЕ: Не удалось загрузить запреты слотов для учителей. Возвращен пустой словарь. Ошибка: {e}")

    pprint(teacher_forbidden_slots)
    return

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
        print(
            f"ВНИМАНИЕ: Не удалось загрузить v_grade_subject_max_consecutive_days. Возвращен пустой словарь. Ошибка: {e}")
    # pprint(grade_subject_max_consecutive_days)
    # return

    # must_sync_split_subjects
    # Набор сплит-предметов, которые должны вестись синхронно у всех подгрупп.
    # must_sync_split_subjects = {"labor"}
    must_sync_split_subjects = set(get_list("v_must_sync_split_subjects", "subject_name"))
    # pprint(must_sync_split_subjects)
    # return

    # --- Словари для красивого отображения в отчетах ---
    display_subject_names: Dict[str, str] = {}
    display_teacher_names: Dict[str, str] = {}
    try:
        subject_map_df = pd.read_sql('SELECT "предмет_eng", "предмет" FROM "з_excel_предметы"', engine)
        display_subject_names = subject_map_df.set_index('предмет_eng')['предмет'].to_dict()

        teacher_map_df = pd.read_sql('SELECT "teacher", "FAMIO" FROM "з_excel_учителя"', engine)
        display_teacher_names = teacher_map_df.set_index('teacher')['FAMIO'].to_dict()

    except Exception as e:
        print(f"ВНИМАНИЕ: Не удалось загрузить словари для отображения (display maps). Ошибка: {e}")

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
        must_sync_split_subjects=must_sync_split_subjects,
        display_subject_names=display_subject_names,
        display_teacher_names=display_teacher_names
    )


def load_display_maps(db_path: str) -> Dict[str, Dict[str, str]]:
    """
    Загружает из базы данных словари для сопоставления
    технических (английских) названий с полными (русскими) для отчетов.
    """
    # Эта функция больше не нужна, так как ее логика перенесена в load_data_from_access
    # и данные теперь являются частью объекта InputData.
    # Оставлена для обратной совместимости, если где-то вызывается.
    if not db_path:
        return {}
    return {}  # Возвращаем пустой словарь, чтобы не сломать старые вызовы


if __name__ == '__main__':
    from pprint import pprint


    print(f"--- Запускаем за загрузку данных из SQL ---")
    data_from_db = load_data_from_sql(user_id=1, version_id=1)

    # print("\n--- Результат: загруженный объект InputData ---")
    # # Используем pprint для красивого вывода dataclass
    # pprint(data_from_db)
