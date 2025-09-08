# rasp_data.py
# -----------------------------------------------------------------------------
# Comprehensive test data for the school timetable problem.
# Every field from InputData and OptimizationWeights is filled explicitly so that
# the file can serve as a complete example for experiments and testing.
# -----------------------------------------------------------------------------

from input_data import ClassInfo, InputData, OptimizationWeights


def make_default_compat() -> set[tuple[str, str]]:
    """Return a set of allowed pairs of concurrent split subjects."""

    allowed: set[tuple[str, str]] = set()

    def add(subj_a: str, subj_b: str) -> None:
        allowed.add(tuple(sorted((subj_a, subj_b))))

    # Разрешаем вести эти split‑предметы параллельно в одном классе и слоте
    add("cs", "eng")
    add("labor", "eng")
    add("labor", "cs")

    return allowed


def create_manual_data() -> InputData:
    """Create a small InputData instance with all fields populated."""

    # --- Базовые множества ---
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    periods = list(range(1, 8))  # 1..7
    classes = [ClassInfo(name="5A", grade=5), ClassInfo(name="5B", grade=5)]
    subjects = ["math", "cs", "eng", "labor", "PE"]
    teachers = ["Ivanov", "Petrov", "Sidorov", "Nikolaev", "Smirnov"]

    # --- Подгруппы ---
    split_subjects = {"eng", "cs", "labor"}
    subgroup_ids = [1, 2]

    # --- Учебные планы ---
    plan_hours = {
        ("5A", "math"): 2,
        ("5B", "math"): 2,
        ("5A", "PE"): 1,
        ("5B", "PE"): 1,
    }
    subgroup_plan_hours = {
        ("5A", "eng", 1): 1,
        ("5A", "eng", 2): 1,
        ("5A", "cs", 1): 1,
        ("5A", "cs", 2): 1,
        ("5A", "labor", 1): 1,
        ("5A", "labor", 2): 1,
        ("5B", "eng", 1): 1,
        ("5B", "eng", 2): 1,
        ("5B", "cs", 1): 1,
        ("5B", "cs", 2): 1,
        ("5B", "labor", 1): 1,
        ("5B", "labor", 2): 1,
    }

    # --- Закрепления преподавателей ---
    assigned_teacher = {
        ("5A", "math"): "Ivanov",
        ("5B", "math"): "Ivanov",
        ("5A", "PE"): "Smirnov",
        ("5B", "PE"): "Smirnov",
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
    }

    # --- Доступность и ограничения ---
    days_off = {"Petrov": {"Mon"}}
    teacher_forbidden_slots = {
        "Petrov": [("Tue", 1)],
        "Nikolaev": [("Thu", 7)],
    }
    forbidden_slots = {("5A", "Mon", 1)}

    # --- Политики и предпочтения ---
    grade_max_lessons_per_day = {5: 6}
    subjects_not_last_lesson = {"math", "eng"}
    elementary_english_periods = {2, 3, 4}
    grade_subject_max_consecutive_days = {5: {"PE": 2}}
    class_slot_weight = {
        ("5A", "Fri", 7): 10.0,
        ("5A", "Fri", 6): 5.0,
    }
    teacher_slot_weight = {("Petrov", "Tue", 1): 8.0}
    class_subject_day_weight = {("5B", "math", "Mon"): 6.0}
    compatible_pairs = make_default_compat()
    paired_subjects = {"math"}
    must_sync_split_subjects = {"eng"}

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

