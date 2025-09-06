# input_data.py
# -----------------------------------------------------------------------------
# Единый контейнер входных данных и весов для задачи составления школьного расписания.
# ОЧИЩЕНО: нет полей teacher_weekly_cap / teacher_daily_cap / class_daily_cap.
# -----------------------------------------------------------------------------

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Union, Optional

# ---------- Удобные псевдонимы типов ----------
Days = List[str]            # ["Mon","Tue","Wed","Thu","Fri"]
Periods = List[int]         # [1,2,3,4,5,6,7]
Classes = List[str]         # ["5A","5B", ...]
Subjects = List[str]        # ["math","eng","cs","labor", ...]
Teachers = List[str]        # ["Ivanov","Petrov", ...]
Subgroups = List[int]       # обычно [1, 2]

# План часов (НЕподгрупповые предметы): (class, subject) -> hours_per_week
PlanHours = Dict[Tuple[str, str], int]

# План часов (подгруппы): (class, subject, subgroup) -> hours_per_week
SubgroupPlanHours = Dict[Tuple[str, str, int], int]

# Закрепление учителей:
#  - для НЕподгрупповых предметов: (class, subject) -> teacher
AssignedTeacher = Dict[Tuple[str, str], str]
#  - для подгрупповых предметов: (class, subject, subgroup) -> teacher
SubgroupAssignedTeacher = Dict[Tuple[str, str, int], str]

# Недоступные дни учителя: teacher -> {"Mon","Fri", ...}
DaysOff = Dict[str, Set[str]]

# Мягкие веса (положительные = штраф; отрицательные = бонус):
#  - по слоту класса (class, day, period)
ClassSlotWeight = Dict[Tuple[str, str, int], float]
#  - по слоту учителя (teacher, day, period)
TeacherSlotWeight = Dict[Tuple[str, str, int], float]
#  - по сочетанию (class, subject, day)
ClassSubjectDayWeight = Dict[Tuple[str, str, str], float]

# Жёсткие запреты слотов на уровне класса: {(class, day, period), ...}
ForbiddenSlots = Set[Tuple[str, str, int]]

# Запреты слотов у преподавателя: teacher -> [(day, period), ...]
TeacherForbiddenSlots = Dict[str, List[Tuple[str, int]]]

# «Максимум повторов предмета в день»:
#  - bool=True   -> максимум 1 раз в день
#  - int         -> максимум k раз в день
#  - dict[subj]  -> максимум k_s для каждого предмета
# MaxRepeatsPerDay = Union[bool, int, Dict[str, int]]

# «Минимум разных дней в неделю для предмета»:
#  ключ (class, subject) -> минимум N дней в неделе, где предмет появляется
MinDaysPerSubject = Dict[Tuple[str, str], int]


@dataclass
class InputData:
    """
    Единый контейнер всех входных данных для постановки CP-SAT задачи расписания.

    Обязательные множества:
      - days, periods, classes, subjects, teachers

    Подгруппы:
      - split_subjects: предметы, которые ведутся по двум подгруппам (например {"eng","cs","labor"})
      - subgroup_ids: номера подгрупп (обычно [1,2])

    Учебный план:
      - plan_hours: часы в неделю для НЕподгрупповых предметов
      - subgroup_plan_hours: часы в неделю для подгрупповых предметов по каждой подгруппе

    Закрепления:
      - assigned_teacher: учитель за (class, subject) — для НЕподгрупповых
      - subgroup_assigned_teacher: учитель за (class, subject, subgroup) — для подгрупповых

    Ограничения/предпочтения (жёсткие и мягкие):
      - days_off: выходные/недоступные дни учителей (на уровне дня)
      - forbidden_slots: жёсткий запрет проводить ЛЮБОЙ урок у класса в указанном слоте
      - teacher_forbidden_slots: явные запреты (day, period) для преподавателей
      - class_slot_weight / teacher_slot_weight / class_subject_day_weight: пользовательские «мягкие» предпочтения

    Совместимость подгрупп:
      - compatible_pairs: множество разрешённых НЕУПОРЯДОЧЕННЫХ пар (s1, s2) split-предметов,
        которые могут идти одновременно в одном классе и слоте.
        Хранить как tuple(sorted((s1, s2))). Разрешение одного и того же предмета параллельно — пара ("eng","eng").

    Дополнительные «политики» (все необязательны):
      - paired_subjects: предметы, которые желательно ставить парами (два подряд)
      - max_repeats_per_day: максимум повторений предмета в день (bool/int/dict)
      - min_days_per_subject: минимум разных дней в неделю для заданного (class, subject)
      - must_sync_split_subjects: сплит-предметы, требующие одновременности подгрупп
      - max_consecutive_lessons_for_class / for_teacher: максимум подряд (скаляр или словари по объектам)
    """

    # --- Базовые множества ---
    days: Days
    periods: Periods
    classes: Classes
    subjects: Subjects
    teachers: Teachers

    # --- Подгруппы ---
    split_subjects: Set[str] = field(default_factory=set)
    subgroup_ids: Subgroups = field(default_factory=lambda: [1, 2])

    # --- Учебные планы ---
    plan_hours: PlanHours = field(default_factory=dict)
    subgroup_plan_hours: SubgroupPlanHours = field(default_factory=dict)

    # --- Закрепления учителей ---
    assigned_teacher: AssignedTeacher = field(default_factory=dict)
    subgroup_assigned_teacher: SubgroupAssignedTeacher = field(default_factory=dict)

    # --- Недоступные дни / запреты / мягкие ---
    days_off: DaysOff = field(default_factory=dict)
    forbidden_slots: ForbiddenSlots = field(default_factory=set)
    teacher_forbidden_slots: TeacherForbiddenSlots = field(default_factory=dict)

    class_slot_weight: ClassSlotWeight = field(default_factory=dict)
    teacher_slot_weight: TeacherSlotWeight = field(default_factory=dict)
    class_subject_day_weight: ClassSubjectDayWeight = field(default_factory=dict)

    # --- Совместимости split-предметов ---
    compatible_pairs: Set[Tuple[str, str]] = field(default_factory=set)

    # --- Предпочтения по «спариванию» ---
    paired_subjects: Set[str] = field(default_factory=set)

    # --- Часто используемые «политики» (необяз.) ---
    # max_repeats_per_day: Optional[MaxRepeatsPerDay] = None
    max_repeats_per_day: Optional[Dict[str, Dict[str, int]]] = None
    min_days_per_subject: MinDaysPerSubject = field(default_factory=dict)
    must_sync_split_subjects: Set[str] = field(default_factory=set)

    # «Максимум подряд» для классов/учителей (скаляр или словари по объектам)
    max_consecutive_lessons_for_class: Optional[Union[int, Dict[str, int]]] = None
    max_consecutive_lessons_for_teacher: Optional[Union[int, Dict[str, int]]] = None


@dataclass
class OptimizationWeights:
    """
    Весовые коэффициенты и параметры решателя для составной целевой функции.
    """
    # --- Веса целей ---
    alpha_runs: int = 10             # «анти-окна» для КЛАССОВ (минимизация числа блоков занятий)
    alpha_runs_teacher: int = 2      # «анти-окна» для УЧИТЕЛЕЙ
    beta_early: int = 1              # предпочтение более ранних слотов
    gamma_balance: int = 1           # баланс по дням (минимизируем разброс нагрузки)
    delta_tail: int = 10             # штраф за «хвосты» после last_ok_period
    epsilon_pairing: int = 20        # штраф за «одинокие» уроки, если предмет «спарный»

    pref_scale: int = 1              # масштаб для пользовательских предпочтений
    last_ok_period: int = 6          # после этого слота начинаются «хвосты» (используется в delta_tail)

    # (Опционально можно добавить use_lexico и т.п., если используете лексикографику)
    use_lexico: bool = False
    lexico_primary: str = "teacher_windows"  # или "class_windows"

    # Параметры решателя
    num_search_workers: int = 20
    random_seed: Optional[int] = None
    time_limit_s: Optional[float] = None
    relative_gap_limit: float = 0.05
