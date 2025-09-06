# input_data.py
# -----------------------------------------------------------------------------
# Единый контейнер входных данных и весов для задачи составления школьного расписания.
# Добавлены поля и веса, которые используются улучшенной моделью CP-SAT:
#  - Лексикографическая оптимизация (use_lexico, lexico_primary)
#  - Индивидуальные запреты (teacher_forbidden_slots и т.п.)
#  - Часто используемые "политики" (must_sync_split_subjects)
#  - Параметры решателя: num_search_workers, random_seed, time_limit_s, relative_gap_limit
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

# --- Новые удобные типы для расширенных настроек ---
# Скалярное значение либо словарь {объект: значение}
ScalarOrPerEntityInt = Union[int, Dict[str, int]]

# Запреты слотов у преподавателя: teacher -> [(day, period), ...]
TeacherForbiddenSlots = Dict[str, List[Tuple[str, int]]]



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
      - teacher_forbidden_slots: явные запреты слотов для преподавателей
      - forbidden_slots: жёсткий запрет проводить ЛЮБОЙ урок у класса в указанном слоте
      - class_slot_weight / teacher_slot_weight / class_subject_day_weight: пользовательские «мягкие» предпочтения

    Дополнительные «политики»:
      - paired_subjects: предметы, которые желательно ставить парами (два подряд)
      - must_sync_split_subjects: сплит‑предметы, требующие одновременности подгрупп
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

    # --- Недоступные дни / лимиты / запреты ---
    days_off: DaysOff = field(default_factory=dict)

    # Явные запреты слотов у преподавателей: teacher -> [(day, period), ...]
    teacher_forbidden_slots: TeacherForbiddenSlots = field(default_factory=dict)

    # Жёсткие запреты слотов на уровне класса: {(class, day, period), ...}
    forbidden_slots: ForbiddenSlots = field(default_factory=set)

    # --- Мягкие цели (необязательно) ---
    class_slot_weight: ClassSlotWeight = field(default_factory=dict)
    teacher_slot_weight: TeacherSlotWeight = field(default_factory=dict)
    class_subject_day_weight: ClassSubjectDayWeight = field(default_factory=dict)

    # --- Предпочтения по «спариванию» ---
    # Предметы, которые желательно ставить по 2 урока подряд
    paired_subjects: Set[str] = field(default_factory=set)

    # --- Часто используемые «политики» (необяз.) ---
    # Сплит‑предметы, у которых подгруппы должны идти синхронно (в один и тот же слот)
    must_sync_split_subjects: Set[str] = field(default_factory=set)


@dataclass
class OptimizationWeights:
    """
    Весовые коэффициенты и параметры решателя для составной целевой функции.

    Примечание к «окнам»:
    - В улучшенной модели «окна» минимизируются как суммарная длина «конверта» (количество
      занятых + пустых слотов между первым и последним занятием) для учителей/классов.
      Поэтому веса alpha_runs / alpha_runs_teacher применяются к этой метрике.

    Также добавлены:
    - use_lexico, lexico_primary: включая «двухфазную» лексикографическую оптимизацию
      (сначала окна одного типа, затем остальные цели).
    - Параметры решателя: num_search_workers, random_seed, time_limit_s, relative_gap_limit.
    """
    # --- Веса целей ---
    alpha_runs: int = 10             # «анти‑окна» для КЛАССОВ (суммарная длина конвертов по дням)
    alpha_runs_teacher: int = 2      # «анти‑окна» для УЧИТЕЛЕЙ (суммарная длина конвертов по дням)
    beta_early: int = 1              # предпочтение более ранних слотов (минимизация номера периода)
    gamma_balance: int = 1           # баланс по дням (минимизируем разброс нагрузки)
    delta_tail: int = 10             # штраф за «хвосты» — уроки после last_ok_period
    epsilon_pairing: int = 20        # штраф за «одинокие» уроки у предметов, которые должны идти парами

    # Пользовательские предпочтения (масштаб), если используются вне модели
    pref_scale: int = 1

    # После этого слота начинаются «хвосты» (используется в delta_tail)
    last_ok_period: int = 6

    # --- Лексикографическая оптимизация ---
    use_lexico: bool = False         # если True: двухфазная оптимизация (primary -> secondary)
    # Что оптимизировать первичным при use_lexico:
    # 'teacher_windows' или 'class_windows'
    lexico_primary: str = "teacher_windows"

    # --- Параметры решателя ---
    num_search_workers: int = 20                 # число воркеров OR‑Tools
    random_seed: Optional[int] = None            # фиксируем сид для воспроизводимости (None = выключено)
    time_limit_s: Optional[float] = None         # лимит времени, сек (None = без лимита)
    relative_gap_limit: float = 0.05             # относительный GAP для приближённого решения
