from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

# Типы для удобства
Days = List[str]
Periods = List[int]
Classes = List[str]
Subjects = List[str]
Teachers = List[str]
Subgroups = List[int]  # например [1, 2]

PlanHours = Dict[Tuple[str, str], int]
SubgroupPlanHours = Dict[Tuple[str, str, int], int]

AssignedTeacher = Dict[Tuple[str, str], str]
SubgroupAssignedTeacher = Dict[Tuple[str, str, int], str]

DaysOff = Dict[str, Set[str]]

ClassSlotWeight = Dict[Tuple[str, str, int], float]          # (class, day, period)
TeacherSlotWeight = Dict[Tuple[str, str, int], float]        # (teacher, day, period)
ClassSubjectDayWeight = Dict[Tuple[str, str, str], float]    # (class, subject, day)


@dataclass
class InputData:
    # Базовые множества
    days: Days
    periods: Periods
    classes: Classes
    subjects: Subjects
    teachers: Teachers

    # Подгруппы: какие предметы делятся и какие ID подгрупп
    split_subjects: Set[str] = field(default_factory=set)
    subgroup_ids: Subgroups = field(default_factory=lambda: [1, 2])

    # Учебные планы
    plan_hours: PlanHours = field(default_factory=dict)                     # (c,s) -> h, только НЕsplit
    subgroup_plan_hours: SubgroupPlanHours = field(default_factory=dict)    # (c,s,g) -> h, только split

    # Закрепление учителей
    assigned_teacher: AssignedTeacher = field(default_factory=dict)                 # (c,s) -> t, НЕsplit
    subgroup_assigned_teacher: SubgroupAssignedTeacher = field(default_factory=dict) # (c,s,g) -> t, split

    # Выходные учителей
    days_off: DaysOff = field(default_factory=dict)

    # Ограничения по нагрузке учителя
    teacher_weekly_cap: int = 35

    # Мягкие цели (опционально)
    class_slot_weight: ClassSlotWeight = field(default_factory=dict)
    teacher_slot_weight: TeacherSlotWeight = field(default_factory=dict)
    class_subject_day_weight: ClassSubjectDayWeight = field(default_factory=dict)

    # Совместимости одновременных split‑предметов внутри класса/слота.
    # Храним как неупорядоченные пары: tuple(sorted((s1,s2)))
    compatible_pairs: Set[Tuple[str, str]] = field(default_factory=set)
