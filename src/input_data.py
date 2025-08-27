# input_data.py
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

# ---------- Типы для удобства ----------
Days = List[str]          # ["Mon","Tue","Wed","Thu","Fri"]
Periods = List[int]       # [1,2,3,4,5,6,7]
Classes = List[str]       # ["5A","5B", ...]
Subjects = List[str]      # ["math","eng","cs","labor", ...]
Teachers = List[str]      # ["Ivanov","Petrov", ...]
Subgroups = List[int]     # обычно [1, 2]

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


@dataclass
class InputData:
    """
    Единый контейнер всех входных данных для постановки MILP-задачи расписания.

    Обязательные множества:
      - days, periods, classes, subjects, teachers

    Подгруппы:
      - split_subjects: предметы, которые ведутся по двум подгруппам (обычно {"eng","cs","labor"})
      - subgroup_ids: номера подгрупп (обычно [1,2])

    Учебный план:
      - plan_hours: часы в неделю для НЕподгрупповых предметов
      - subgroup_plan_hours: часы в неделю для подгрупповых предметов по каждой подгруппе

    Закрепления:
      - assigned_teacher: учитель за (class, subject) — для НЕподгрупповых
      - subgroup_assigned_teacher: учитель за (class, subject, subgroup) — для подгрупповых

    Ограничения/предпочтения:
      - days_off: выходные/недоступные дни учителей
      - teacher_weekly_cap: лимит недельной нагрузки учителя
      - class_slot_weight, teacher_slot_weight, class_subject_day_weight: мягкие цели

    Совместимость подгрупп:
      - compatible_pairs: множество разрешённых НЕУПОРЯДОЧЕННЫХ пар (s1, s2) split-предметов,
        которые могут идти одновременно внутри одного класса и слота. Включайте и одинаковые пары,
        если разрешаете параллельные подгруппы одного и того же предмета: например ("eng","eng").
        Храните как tuple(sorted((s1,s2))).
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

    # --- Недоступные дни / лимиты ---
    days_off: DaysOff = field(default_factory=dict)
    teacher_weekly_cap: int = 35

    # --- Мягкие цели (необязательно) ---
    class_slot_weight: ClassSlotWeight = field(default_factory=dict)
    teacher_slot_weight: TeacherSlotWeight = field(default_factory=dict)
    class_subject_day_weight: ClassSubjectDayWeight = field(default_factory=dict)

    # --- Совместимости split-предметов ---
    # храним как отсортированные пары, напр.: {("eng","eng"), ("cs","eng"), ("labor","labor")}
    compatible_pairs: Set[Tuple[str, str]] = field(default_factory=set)
