# rasp_data.py
# -----------------------------------------------------------------------------
# Тестовые данные для задачи составления школьного расписания.
# Обновлено: добавлены поля, используемые улучшенной моделью (teacher_forbidden_slots,
# must_sync_split_subjects и др.)
# -----------------------------------------------------------------------------

from input_data import InputData


def make_default_compat():
    """Разрешённые пары одновременных split‑предметов (для разных предметов).

    Логика совместимости применяется только к ПАРАМ предметов (s1 != s2):
    внутри одного слота класс может вести два РАЗНЫХ split‑предмета для разных подгрупп
    только если такая пара разрешена. Пары вида ("eng","eng") не нужны, так как
    проверка делается только для разных предметов.
    """
    allowed = set()

    def add(a, b):
        allowed.add(tuple(sorted((a, b))))

    # Разрешаем одновременно вести "cs" и "eng" (например, g1: cs; g2: eng)
    add("cs", "eng")

    # Пример: можем дополнить и другими парами при необходимости:
    # add("labor", "eng")
    # add("labor", "cs")

    return allowed


def create_manual_data() -> InputData:
    # --- Основные множества ---
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    periods = list(range(1, 8))  # 1..7
    classes = ["5A", "5B"]
    subjects = ["math", "cs", "eng", "labor"]
    teachers = ["Ivanov", "Petrov", "Sidorov", "Nikolaev", "Smirnov"]

    # Split‑предметы — ведутся по подгруппам (обычно 2 подгруппы: [1,2])
    split_subjects = {"eng", "cs", "labor"}
    subgroup_ids = [1, 2]

    # --- Учебный план ---
    # НЕ‑делимые предметы (по классам)
    plan_hours = {
        ("5A", "math"): 2,
        ("5B", "math"): 2,
    }

    # ДЕЛИМЫЕ предметы: часы задаются для каждой подгруппы отдельно
    subgroup_plan_hours = {
        # 5A
        ("5A", "eng", 1): 1, ("5A", "eng", 2): 1,
        ("5A", "cs", 1): 1,  ("5A", "cs", 2): 1,
        ("5A", "labor", 1): 1, ("5A", "labor", 2): 1,
        # 5B
        ("5B", "eng", 1): 1, ("5B", "eng", 2): 1,
        ("5B", "cs", 1): 1,  ("5B", "cs", 2): 1,
        ("5B", "labor", 1): 1, ("5B", "labor", 2): 1,
    }

    # --- Закрепления учителей ---
    # НЕ‑делимые
    assigned_teacher = {
        ("5A", "math"): "Ivanov",
        ("5B", "math"): "Ivanov",
    }
    # ДЕЛИМЫЕ (по подгруппам)
    subgroup_assigned_teacher = {
        # 5A
        ("5A", "eng", 1): "Sidorov",  ("5A", "eng", 2): "Nikolaev",
        ("5A", "cs", 1): "Petrov",    ("5A", "cs", 2): "Petrov",
        ("5A", "labor", 1): "Smirnov", ("5A", "labor", 2): "Smirnov",
        # 5B
        ("5B", "eng", 1): "Sidorov",  ("5B", "eng", 2): "Nikolaev",
        ("5B", "cs", 1): "Petrov",    ("5B", "cs", 2): "Petrov",
        ("5B", "labor", 1): "Smirnov", ("5B", "labor", 2): "Smirnov",
    }

    # --- Жёсткие/мягкие предпочтения и лимиты ---
    # Выходные/недоступные дни учителей (по дням)
    days_off = {
        "Petrov": {"Mon"},  # Петров по понедельникам не работает
        # Можно добавить и другие: "Ivanov": {"Fri"}
    }

    # Жёсткий запрет проводить ЛЮБОЙ урок у класса в указанном слоте
    forbidden_slots = {("5A", "Mon", 1)}  # 5А в Пн на 1‑м уроке занят/закрыт

    # Пользовательские «мягкие» веса предпочтений (необязательно; могут не использоваться в модели)
    class_slot_weight = {("5A", "Fri", 7): 10.0, ("5A", "Fri", 6): 5.0}
    teacher_slot_weight = {("Petrov", "Tue", 1): 8.0}
    class_subject_day_weight = {("5B", "math", "Mon"): 6.0}

    # Запрещённые слоты для конкретных преподавателей
    teacher_forbidden_slots = {
        "Petrov": [("Tue", 1)],     # кроме days_off, ещё и «Вт‑1» нельзя
        "Nikolaev": [("Thu", 7)],   # пример точечного запрета
        # "Sidorov": [("Wed", 3)]
    }

    # Список split‑предметов, которые надо вести синхронно (обе подгруппы в один слот).
    # Выбираем "eng": у g1 и g2 разные учителя (Sidorov / Nikolaev), поэтому это реализуемо.
    # НЕ выбираем "labor", потому что обе подгруппы ведёт Smirnov — иначе будет конфликт
    # по ограничению «у учителя не более 1 урока в слоте».
    must_sync_split_subjects = {"eng"}

    # Предметы, которые желательно ставить парами (два подряд).
    # В демонстрационных данных оставляем пустым.
    paired_subjects = set()

    data = InputData(
        # Базовые множества
        days=days,
        periods=periods,
        classes=classes,
        subjects=subjects,
        teachers=teachers,

        # Подгруппы
        split_subjects=split_subjects,
        subgroup_ids=subgroup_ids,

        # Учебные планы
        plan_hours=plan_hours,
        subgroup_plan_hours=subgroup_plan_hours,

        # Закрепления
        assigned_teacher=assigned_teacher,
        subgroup_assigned_teacher=subgroup_assigned_teacher,

        # Жёсткие/мягкие предпочтения
        days_off=days_off,
        forbidden_slots=forbidden_slots,
        class_slot_weight=class_slot_weight,
        teacher_slot_weight=teacher_slot_weight,
        class_subject_day_weight=class_subject_day_weight,

        # Лимиты / запреты
        teacher_forbidden_slots=teacher_forbidden_slots,

        # Совместимости split‑предметов
        compatible_pairs=make_default_compat(),

        # Частые «политики»
        must_sync_split_subjects=must_sync_split_subjects,

        # Предпочтения «спаривать» предметы
        paired_subjects=paired_subjects,
    )

    return data
