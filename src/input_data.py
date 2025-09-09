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
class ClassInfo:
    """Информация о классе: название и год обучения."""
    name: str
    grade: int


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

    Совместимость подгрупп:
      - compatible_pairs: множество разрешённых НЕУПОРЯДОЧЕННЫХ пар (s1, s2) split‑предметов,
        которые могут идти одновременно в одном классе и слоте.
        Хранить как tuple(sorted((s1, s2))). Разрешение одного и того же предмета параллельно — пара ("eng","eng").

    Дополнительные «политики»:
      - paired_subjects: предметы, которые желательно ставить парами (два подряд)
      - must_sync_split_subjects: сплит‑предметы, требующие одновременности подгрупп
      - grade_max_lessons_per_day: дневные ограничения по числу уроков
          Пример: {2: 4, 3: 5, 4: 5}
      - subjects_not_last_lesson: предметы, которые не могут быть последними в дне по параллелям
          Пример: {5: {"math"}, 7: {"math", "physics"}}
      - elementary_english_periods: допустимые номера уроков для английского в начальной школе
          Пример: {2, 3, 4}
      - grade_subject_max_consecutive_days: ограничения по макс. подряд идущим дням для предметов по параллелям
          Пример: {3: {"PE": 2}}

    classes — список ClassInfo, каждый элемент которого содержит:
      - name: строковое имя класса (например, "5A")
      - grade: номер параллели
    """

    # --- Базовые множества ---
    days: Days
    periods: Periods
    classes: List[ClassInfo]
    subjects: Subjects
    teachers: Teachers

    # название предмета английский
    english_subject_name: str

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

    # --- Дополнительные данные для школьных правил ---
    # Максимальное число уроков в день по параллели, например {2: 4, 3: 5, 4: 5}
    grade_max_lessons_per_day: Dict[int, int] = field(default_factory=lambda: {2: 4, 3: 5, 4: 5})
    # Предметы, которые не могут быть последним уроком дня по параллелям, например {5: {"math"}}
    subjects_not_last_lesson: Dict[int, Set[str]] = field(
        default_factory=lambda: {g: {"math", "physics"} for g in range(1, 9)}
    )
    # Разрешённые номера уроков для английского языка в начальной школе, например {2, 3, 4}
    elementary_english_periods: Set[int] = field(default_factory=lambda: {2, 3, 4})
    # Максимальное число подряд идущих дней с предметом по параллели, например {3: {"PE": 2}}
    grade_subject_max_consecutive_days: Dict[int, Dict[str, int]] = field(default_factory=dict)

    # --- Мягкие цели (необязательно) ---
    class_slot_weight: ClassSlotWeight = field(default_factory=dict)
    teacher_slot_weight: TeacherSlotWeight = field(default_factory=dict)
    class_subject_day_weight: ClassSubjectDayWeight = field(default_factory=dict)

    # --- Совместимости split‑предметов ---
    # Храним как отсортированные пары, напр.: {("eng","eng"), ("cs","eng"), ("labor","labor")}
    compatible_pairs: Set[Tuple[str, str]] = field(default_factory=set)

    # --- Предпочтения по «спариванию» ---
    # Предметы, которые желательно ставить по 2 урока подряд
    paired_subjects: Set[str] = field(default_factory=set)

    # --- Часто используемые «политики» (необяз.) ---
    # Сплит‑предметы, у которых подгруппы должны идти синхронно (в один и тот же слот)
    # здесь должен быть указан труд (два труда одновременно), но не eng и cs
    # must_sync_split_subjects — сплит‑предметы, у которых подгруппы должны идти синхронно(в один и тот же слот)
    # must_sync_split_subjects = {"eng", "labor"}
    # must_sync_split_subjects = {"eng"} — синхронизация только английского.
    # must_sync_split_subjects = {"eng", "cs"} — английский и информатика идут одновременно.
    # must_sync_split_subjects = {"eng", "cs", "labor"} — все три split‑предмета синхронны.
    # must_sync_split_subjects = {"physics_lab", "chem_lab"} — синхронные лабораторные работы по физике и химии.
    # must_sync_split_subjects = {"eng", "german"} — синхронное проведение английского и немецкого.

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
    num_search_workers: int = 16                 # число воркеров OR‑Tools
    random_seed: Optional[int] = None            # фиксируем сид для воспроизводимости (None = выключено)
    time_limit_s: Optional[float] = None         # лимит времени, сек (None = без лимита)
    relative_gap_limit: float = 0.05             # относительный GAP для приближённого решения

@dataclass
class OptimizationGoals:
    teacher_slot_optimization: bool = True