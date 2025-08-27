# Описание основных структур данных и переменных модели расписания

# --- Входные данные (Python-структуры) ---
# days: список дней недели, например ["Mon", "Tue", ...]
# periods: список номеров уроков, например [1,2,3,4,5,6,7]
# classes: список классов, например ["5A", "5B"]
# subjects: список предметов, например ["math", "cs", "eng"]
# teachers: список учителей, например ["Ivanov", "Petrov"]
# plan_hours: словарь {(class, subject): часы в неделю}
# assigned_teacher: словарь {(class, subject): teacher}
# days_off: словарь {teacher: {дни, когда не работает}}
# teacher_preferences: {teacher -> {day -> weight}} — мягкие предпочтения по дням
# class_preferences: {class -> {day -> weight}} — мягкие предпочтения по дням


from input_data import InputData


def make_default_compat():
    """Разрешённые пары одновременных split-предметов"""
    allowed = set()

    def add(a, b):
        allowed.add(tuple(sorted((a, b))))

    add("eng", "eng")
    add("trud", "trud")
    add("informatika", "eng")
    return allowed


def create_timetable_data() -> InputData:
    # Веса для составной целевой функции - см. OptimizationWeights


    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    periods = [1, 2, 3, 4, 5, 6, 7]
    classes = ["5A", "5B"]
    subjects = ["math", "cs", "eng", "labor"]
    split_subjects = {"eng", "cs", "cs"}

    teachers = ["Ivanov", "Petrov", "Sidorov", "Nikolaev"]

    subgroup_plan_hours = {
        ("5A", "eng", 2): 1, ("5A", "eng", 2): 1,
        ("5B", "eng", 2): 1, ("5B", "eng", 2): 1
    }

    subgroup_assigned_teacher = {
        ("5A", "eng", 1): "Sidorov", ("5A", "eng", 2): "Nikolaev",
        ("5B", "eng", 1): "Sidorov", ("5B", "eng", 2): "Nikolaev"
    }

    plan_hours = {
        ("5A", "math"): 2, ("5A", "cs"): 2, ("5A", "eng"): 2, ("5A", "labor"): 2,
        ("5B", "math"): 2, ("5B", "cs"): 2, ("5B", "eng"): 2, ("5B", "labor"): 2,
    }

    assigned_teacher = {("5A", "math"): "Ivanov", ("5B", "math"): "Ivanov"}

    # дни когда учитель не работает
    days_off = {
        "Petrov": {"Mon"},
        "Ivanov": set(),
        "Sidorov": set(),
        "Nikolaev": set(),
    }

    # Пример предпочтений:
    #  - Штрафуем поздние слоты у 5A по пятницам
    class_slot_weight = {
        ("5A", "Fri", 7): 10.0,
        ("5A", "Fri", 6): 5.0,
    }
    #  - Учитель Петров не любит 1-й урок во вторник
    teacher_slot_weight = {
        ("Petrov", "Tue", 1): 8.0,
    }
    #  - Классу 5B лучше не ставить math по понедельникам
    class_subject_day_weight = {
        ("5B", "math", "Mon"): 6.0,
    }

    data = InputData(
        days=days, periods=periods, classes=classes, subjects=subjects, teachers=teachers,
        split_subjects=split_subjects,
        plan_hours=plan_hours,
        subgroup_plan_hours=subgroup_plan_hours,
        assigned_teacher=assigned_teacher,
        subgroup_assigned_teacher=subgroup_assigned_teacher,
        compatible_pairs=make_default_compat(),
        days_off=days_off,
        class_slot_weight=class_slot_weight,
        teacher_slot_weight=teacher_slot_weight,
        class_subject_day_weight=class_subject_day_weight
    )

    return data
