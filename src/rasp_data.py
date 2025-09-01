# Описание основных структур данных и переменных модели расписания

# --- Входные данные (Python-структуры) ---
# days: список дней недели, например ["Mon", "Tue", ...]
# periods: список номеров уроков, например [1,2,3,4,5,6,7]
# classes: список классов, например ["5A", "5B"]
# subjects: список предметов, например ["math", "cs", "eng"]
# teachers: список учителей, например ["Ivanov E K ", "Petrov"]
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

    # здесь надо записать только разные предметы
    add("cs", "eng")
    # add("labor", "labor")
    # add("cs", "cs")
    return allowed


def create_timetable_data() -> InputData:
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    periods = list(range(1, 8))
    classes = ["5A", "5B"]
    subjects = ["math", "cs", "eng", "labor", "history"]
    split_subjects = {"eng", "cs", "labor"}
    teachers = ["Ivanov E K ", "Petrov", "Sidorov", "Nikolaev", "Smirnov", "Voloshin"]

    # --- Учебный план ---
    # Только НЕ-делимые предметы
    plan_hours = {
        ("5A", "math"): 2,
        ("5B", "math"): 2,
        ("5A", "history"): 2,
        ("5B", "history"): 2,

    }

    # Только ДЕЛИМЫЕ предметы (по подгруппам)
    subgroup_plan_hours = {
        # 5A
        ("5A", "eng", 1): 2, ("5A", "eng", 2): 2,
        ("5A", "cs", 1): 2, ("5A", "cs", 2): 2,
        # ("5A", "labor", 1): 1, ("5A", "labor", 2): 1,
        # 5B
        ("5B", "eng", 1): 1, ("5B", "eng", 2): 1,
        ("5B", "cs", 1): 1, ("5B", "cs", 2): 1,
        ("5B", "labor", 1): 1, ("5B", "labor", 2): 1,
    }

    # --- Закрепление учителей ---
    # НЕ-делимые
    assigned_teacher = {
        ("5A", "math"): "Ivanov E K ",
        ("5B", "math"): "Ivanov E K ",
        ("5A", "history"): "Voloshin",
        ("5B", "history"): "Voloshin"
    }

    # ДЕЛИМЫЕ (по подгруппам)
    subgroup_assigned_teacher = {
        # 5A
        ("5A", "eng", 1): "Sidorov",
        ("5A", "eng", 2): "Nikolaev",
        ("5A", "cs", 1): "Petrov", ("5A", "cs", 2): "Petrov",
        ("5A", "labor", 1): "Smirnov", ("5A", "labor", 2): "Smirnov",
        # 5B
        ("5B", "eng", 1): "Sidorov", ("5B", "eng", 2): "Nikolaev",
        ("5B", "cs", 1): "Petrov", ("5B", "cs", 2): "Petrov",
        ("5B", "labor", 1): "Smirnov", ("5B", "labor", 2): "Smirnov",
    }

    days_off = {"Petrov": {"Mon"}}
    forbidden_slots = {('5A', 'Mon', 1)}
    class_slot_weight = {("5A", "Fri", 7): 10.0, ("5A", "Fri", 6): 5.0}
    teacher_slot_weight = {("Petrov", "Tue", 1): 8.0}
    class_subject_day_weight = {("5B", "math", "Mon"): 6.0}

    data = InputData(
        days=days, periods=periods, classes=classes, subjects=subjects, teachers=teachers,
        split_subjects=split_subjects,
        plan_hours=plan_hours,
        subgroup_plan_hours=subgroup_plan_hours,
        assigned_teacher=assigned_teacher,
        subgroup_assigned_teacher=subgroup_assigned_teacher,
        compatible_pairs=make_default_compat(),
        days_off=days_off,
        forbidden_slots=forbidden_slots,
        class_slot_weight=class_slot_weight,
        teacher_slot_weight=teacher_slot_weight,
        class_subject_day_weight=class_subject_day_weight
    )

    return data
