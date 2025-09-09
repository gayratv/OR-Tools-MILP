"""Sample data set for the timetable model.

This module provides a small yet fully populated :class:`InputData` instance
that can be used for experiments and manual testing.  Every collection in the
data structure is filled explicitly so the file doubles as comprehensive
documentation of the expected input format.
"""

from input_data import ClassInfo, InputData, OptimizationWeights


def make_default_compat() -> set[tuple[str, str]]:
    """Return allowed pairs of concurrent split subjects.

    Some split subjects can take place in parallel for different subgroups of
    the same class (e.g. English for one subgroup and Computer Science for the
    other).  The solver needs the set of such compatible pairs expressed as
    ordered tuples with lexicographically sorted subject names.
    """

    allowed: set[tuple[str, str]] = set()

    def add(subj_a: str, subj_b: str) -> None:
        """Add an unordered pair of subjects to the compatibility set."""

        allowed.add(tuple(sorted((subj_a, subj_b))))

    # Разрешаем вести эти split‑предметы параллельно в одном классе и слоте
    add("cs", "eng")
    add("labor", "eng")
    add("labor", "cs")

    return allowed


def create_manual_data() -> InputData:
    """Create a fully populated :class:`InputData` instance.

    The function below enumerates every piece of data expected by the solver:
    base sets, lesson plans, teacher assignments and a selection of scheduling
    policies.  It is intentionally verbose so that the structure of the
    :class:`InputData` dataclass is clear from a single file.
    """

    # ------------------------------------------------------------------
    # Базовые множества
    # ------------------------------------------------------------------
    # Пять учебных дней и семь уроков в каждом дне.
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    periods = list(range(1, 8))  # 1..7

    # Три класса: две пятых параллели и один класс начальной школы.
    classes = [
        ClassInfo(name="5A", grade=5),
        ClassInfo(name="5B", grade=5),
        ClassInfo(name="2A", grade=2),
    ]

    # Перечень изучаемых предметов. История и музыка добавлены как примеры
    # обычных (неподгрупповых) дисциплин.
    subjects = [
        "math",
        "cs",
        "eng",
        "labor",
        "PE",
        "history",
        "music",
    ]

    # Список всех преподавателей, задействованных в примере.
    teachers = [
        "Ivanov",
        "Petrov",
        "Sidorov",
        "Nikolaev",
        "Smirnov",
        "Kuznetsov",  # history
        "Orlova",     # music
    ]

    # ------------------------------------------------------------------
    # Подгруппы
    # ------------------------------------------------------------------
    # Английский, информатика и труд ведутся по подгруппам, поэтому для них
    # требуется указывать часы и преподавателей отдельно для каждой подгруппы.
    split_subjects = {"eng", "cs", "labor"}
    subgroup_ids = [1, 2]

    # ------------------------------------------------------------------
    # Учебные планы
    # ------------------------------------------------------------------
    # plan_hours описывает часы для предметов без деления на подгруппы, а
    # subgroup_plan_hours — отдельно для каждой подгруппы.
    plan_hours = {
        ("5A", "math"): 2,
        ("5B", "math"): 2,
        ("5A", "PE"): 1,
        ("5B", "PE"): 1,
        ("5A", "history"): 1,
        ("5B", "history"): 1,
        ("5A", "music"): 1,
        ("5B", "music"): 1,
    }
    subgroup_plan_hours = {
        # 5-е классы
        ("5A", "eng", 1): 1,
        ("5A", "eng", 2): 1,
        ("5A", "cs", 1): 1,
        ("5A", "cs", 2): 1,
        ("5A", "labor", 1): 2,
        ("5A", "labor", 2): 2,
        ("5B", "eng", 1): 1,
        ("5B", "eng", 2): 1,
        ("5B", "cs", 1): 1,
        ("5B", "cs", 2): 1,
        ("5B", "labor", 1): 2,
        ("5B", "labor", 2): 2,
        # Класс 2A получает две части английского — по одному часу на подгруппу
        ("2A", "eng", 1): 1,
        ("2A", "eng", 2): 1,
    }

    # ------------------------------------------------------------------
    # Закрепления преподавателей
    # ------------------------------------------------------------------
    assigned_teacher = {
        ("5A", "math"): "Ivanov",
        ("5B", "math"): "Ivanov",
        ("5A", "PE"): "Smirnov",
        ("5B", "PE"): "Smirnov",
        ("5A", "history"): "Kuznetsov",
        ("5B", "history"): "Kuznetsov",
        ("5A", "music"): "Orlova",
        ("5B", "music"): "Orlova",
    }
    subgroup_assigned_teacher = {
        ("5A", "eng", 1): "Sidorov",
        ("5A", "eng", 2): "Nikolaev",
        ("5A", "cs", 1): "Petrov",
        ("5A", "cs", 2): "Petrov",
        ("5A", "labor", 1): "Smirnov",
        ("5A", "labor", 2): "Smirnov",
        ("5B", "eng", 1): "Sidorov",
        ("5B", "eng", 2): "Nikolaev",
        ("5B", "cs", 1): "Petrov",
        ("5B", "cs", 2): "Petrov",
        ("5B", "labor", 1): "Smirnov",
        ("5B", "labor", 2): "Smirnov",
        # Английский у второго класса
        ("2A", "eng", 1): "Sidorov",
        ("2A", "eng", 2): "Nikolaev",
    }

    # ------------------------------------------------------------------
    # Доступность и ограничения
    # ------------------------------------------------------------------
    days_off = {"Petrov": {"Mon"}}
    teacher_forbidden_slots = {
        "Petrov": [("Tue", 1)],
        "Nikolaev": [("Thu", 7)],
    }
    forbidden_slots = {("5A", "Mon", 1)}

    english_subject_name = "eng"

    # ------------------------------------------------------------------
    # Политики и предпочтения
    # ------------------------------------------------------------------
    grade_max_lessons_per_day = {5: 7, 2: 4}
    subjects_not_last_lesson = {2: {"math", "eng"}, 5: {"math"}}
    elementary_english_periods = {2, 3, 4}

    # - grade_subject_max_consecutive_days: ограничения по макс. подряд идущим дням для предметов по параллелям
    # физкультура не более 2 дней подряд для 5 класса
    grade_subject_max_consecutive_days = {5: {"PE": 2, "eng": 2}}
    class_slot_weight = {
        ("5A", "Fri", 7): 10.0,
        ("5A", "Fri", 6): 5.0,
    }
    teacher_slot_weight = {("Petrov", "Tue", 1): 8.0}
    class_subject_day_weight = {("5B", "math", "Mon"): 6.0}
    compatible_pairs = make_default_compat()
    paired_subjects = {"labor"}
    must_sync_split_subjects = {"labor"}

    return InputData(
        days=days,
        periods=periods,
        classes=classes,
        subjects=subjects,
        teachers=teachers,
        split_subjects=split_subjects,
        subgroup_ids=subgroup_ids,
        plan_hours=plan_hours,
        subgroup_plan_hours=subgroup_plan_hours,
        assigned_teacher=assigned_teacher,
        subgroup_assigned_teacher=subgroup_assigned_teacher,
        days_off=days_off,
        teacher_forbidden_slots=teacher_forbidden_slots,
        forbidden_slots=forbidden_slots,
        grade_max_lessons_per_day=grade_max_lessons_per_day,
        subjects_not_last_lesson=subjects_not_last_lesson,
        elementary_english_periods=elementary_english_periods,
        grade_subject_max_consecutive_days=grade_subject_max_consecutive_days,
        class_slot_weight=class_slot_weight,
        teacher_slot_weight=teacher_slot_weight,
        class_subject_day_weight=class_subject_day_weight,
        compatible_pairs=compatible_pairs,
        paired_subjects=paired_subjects,
        must_sync_split_subjects=must_sync_split_subjects,
        english_subject_name=english_subject_name
    )


def create_optimization_weights() -> OptimizationWeights:
    """Return example weights configuration for the solver."""

    return OptimizationWeights(
        alpha_runs=10,
        alpha_runs_teacher=2,
        beta_early=1,
        gamma_balance=1,
        delta_tail=10,
        epsilon_pairing=20,
        pref_scale=1,
        last_ok_period=6,
        use_lexico=False,
        lexico_primary="teacher_windows",
        num_search_workers=4,
        random_seed=42,
        time_limit_s=30.0,
        relative_gap_limit=0.05,
    )


__all__ = ["create_manual_data", "create_optimization_weights"]
