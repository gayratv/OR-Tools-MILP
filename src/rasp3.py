from dataclasses import dataclass
from typing import Dict, List, Set, Tuple
import itertools
import pulp


# ------------------------------
# МОДЕЛЬ ДАННЫХ
# ------------------------------

Days = List[str]
Periods = List[int]
Classes = List[str]
Subjects = List[str]
Teachers = List[str]

PlanHours = Dict[Tuple[str, str], int]
AssignedTeacher = Dict[Tuple[str, str], str]
DaysOff = Dict[str, Set[str]]


@dataclass
class InputData:
    days: Days
    periods: Periods
    classes: Classes
    subjects: Subjects
    teachers: Teachers
    plan_hours: PlanHours
    assigned_teacher: AssignedTeacher
    days_off: DaysOff
    teacher_weekly_cap: int = 35


# ------------------------------
# ПОСТРОЕНИЕ И РЕШЕНИЕ MILP
# ------------------------------

def build_and_solve_timetable(data: InputData, lp_path: str = "schedule.lp"):
    model = pulp.LpProblem("School_Timetabling", sense=pulp.LpMinimize)

    C, S, D, P = data.classes, data.subjects, data.days, data.periods

    # бинарные переменные: x[c,s,d,p] = 1 если урок идет в слоте
    x = pulp.LpVariable.dicts(
        "x",
        ((c, s, d, p) for c, s, d, p in itertools.product(C, S, D, P)),
        lowBound=0,
        upBound=1,
        cat=pulp.LpBinary
    )

    model += 0, "Objective"

    # --- учебный план ---
    for (c, s), hours in data.plan_hours.items():
        model += (
            pulp.lpSum(x[(c, s, d, p)] for d in D for p in P) == hours,
            f"PlanHours_{c}_{s}"
        )

    # --- у класса не более 1 урока в слот ---
    for c, d, p in itertools.product(C, D, P):
        model += (
            pulp.lpSum(x[(c, s, d, p)] for s in S) <= 1,
            f"ClassNoOverlap_{c}_{d}_{p}"
        )

    # --- НОВОЕ: не больше 1 урока одного предмета в день на класс ---
    # ∀ c,s,d: Sum_p x[c,s,d,p] ≤ 1
    for c, s, d in itertools.product(C, S, D):
        # добавляем ограничение только для тех (c,s), которые реально есть в плане (иначе — 0 часов)
        if (c, s) in data.plan_hours and data.plan_hours[(c, s)] > 0:
            model += (
                pulp.lpSum(x[(c, s, d, p)] for p in P) <= 1,
                f"SubjectDailyLimit_{c}_{s}_{d}"
            )

    # группировка (c,s) по учителю
    by_teacher: Dict[str, List[Tuple[str, str]]] = {t: [] for t in data.teachers}
    for (c, s), t in data.assigned_teacher.items():
        by_teacher[t].append((c, s))

    # --- учитель не ведёт 2 класса одновременно ---
    for t in data.teachers:
        cs_pairs = by_teacher.get(t, [])
        for d, p in itertools.product(D, P):
            if cs_pairs:
                model += (
                    pulp.lpSum(x[(c, s, d, p)] for (c, s) in cs_pairs) <= 1,
                    f"TeacherNoOverlap_{t}_{d}_{p}"
                )

    # --- недельная нагрузка учителя ≤ cap ---
    for t in data.teachers:
        cs_pairs = by_teacher.get(t, [])
        if cs_pairs:
            model += (
                pulp.lpSum(x[(c, s, d, p)] for (c, s) in cs_pairs for d in D for p in P)
                <= data.teacher_weekly_cap,
                f"TeacherWeeklyCap_{t}"
            )

    # --- выходные/недоступные дни учителя ---
    for t, off_days in data.days_off.items():
        cs_pairs = by_teacher.get(t, [])
        for d in off_days:
            for p in P:
                model += (
                    pulp.lpSum(x[(c, s, d, p)] for (c, s) in cs_pairs) == 0,
                    f"TeacherDayOff_{t}_{d}_{p}"
                )

    # сохранить LP
    model.writeLP(lp_path)
    print(f"LP-модель сохранена в: {lp_path}")

    # ---- РЕШЕНИЕ CBC ----
    solver = pulp.PULP_CBC_CMD(msg=True)  # лог решателя
    model.solve(solver)
    print("Статус решения:", pulp.LpStatus[model.status])

    if pulp.LpStatus[model.status] not in ("Optimal", "Feasible"):
        print("Решение не найдено (модель несовместна или иная проблема).")
        return

    # ------------------------------
    # ВЫВОД РАСПИСАНИЯ ПО КЛАССАМ
    # ------------------------------
    print("\n================ РАСПИСАНИЕ ПО КЛАССАМ ================")
    for c in C:
        print(f"\n=== Класс {c} ===")
        for d in D:
            row = []
            for p in P:
                subj = None
                for s in S:
                    if pulp.value(x[(c, s, d, p)]) > 0.5:
                        subj = s
                        break
                if subj:
                    t = data.assigned_teacher[(c, subj)]
                    row.append(f"{p}: {subj} ({t})")
                else:
                    row.append(f"{p}: —")
            print(f"{d} | " + ", ".join(row))

    # ------------------------------
    # ВЫВОД РАСПИСАНИЯ ПО УЧИТЕЛЯМ + НЕДЕЛЬНАЯ НАГРУЗКА
    # ------------------------------
    print("\n================ РАСПИСАНИЕ ПО УЧИТЕЛЯМ ================")
    for t in data.teachers:
        cs_pairs = by_teacher.get(t, [])
        if not cs_pairs:
            print(f"\n=== Учитель {t} ===\n(нет закрепленных предметов/классов)")
            continue

        print(f"\n=== Учитель {t} ===")
        total_load = 0
        for d in D:
            row = []
            for p in P:
                slot = None
                for (c, s) in cs_pairs:
                    if pulp.value(x[(c, s, d, p)]) > 0.5:
                        slot = f"{p}: {c} — {s}"
                        total_load += 1
                        break
                if slot:
                    row.append(slot)
                else:
                    row.append(f"{p}: —")
            print(f"{d} | " + ", ".join(row))
        print(f"Итого уроков за неделю: {total_load} (лимит {data.teacher_weekly_cap})")


# ------------------------------
# ПРИМЕР
# ------------------------------
if __name__ == "__main__":
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    periods = [1, 2, 3, 4, 5, 6, 7]
    classes = ["5A", "5B"]
    subjects = ["math", "cs", "eng", "labor"]
    teachers = ["Ivanov", "Petrov", "Sidorov"]

    plan_hours = {
        ("5A", "math"): 2, ("5A", "cs"): 2, ("5A", "eng"): 2, ("5A", "labor"): 2,
        ("5B", "math"): 2, ("5B", "cs"): 2, ("5B", "eng"): 2, ("5B", "labor"): 2,
    }

    assigned_teacher = {
        ("5A", "math"): "Ivanov", ("5A", "cs"): "Petrov",
        ("5A", "eng"): "Sidorov", ("5A", "labor"): "Petrov",
        ("5B", "math"): "Ivanov", ("5B", "cs"): "Petrov",
        ("5B", "eng"): "Sidorov", ("5B", "labor"): "Petrov",
    }

    days_off = {
        "Petrov": {"Mon"},   # пример: Петров не работает в понедельник
        "Ivanov": set(),
        "Sidorov": set(),
    }

    data = InputData(
        days=days,
        periods=periods,
        classes=classes,
        subjects=subjects,
        teachers=teachers,
        plan_hours=plan_hours,
        assigned_teacher=assigned_teacher,
        days_off=days_off,
        teacher_weekly_cap=35,
    )

    build_and_solve_timetable(data, lp_path="schedule.lp")
