from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple
import itertools
import pulp

# ==============================
# Типы
# ==============================
Days = List[str]
Periods = List[int]
Classes = List[str]
Subjects = List[str]
Teachers = List[str]
Subgroups = List[int]  # например [1, 2]

# План часов (НЕ делящихся на подгруппы): (class, subject) -> hours
PlanHours = Dict[Tuple[str, str], int]
# План часов (ДЛЯ подгрупп): (class, subject, subgroup) -> hours
SubgroupPlanHours = Dict[Tuple[str, str, int], int]

# Закрепления учителей
AssignedTeacher = Dict[Tuple[str, str], str]                 # для НЕподгрупповых предметов
SubgroupAssignedTeacher = Dict[Tuple[str, str, int], str]     # для подгрупповых предметов

DaysOff = Dict[str, Set[str]]  # teacher -> {days}

# Мягкие предпочтения (веса): положительные = штраф, отрицательные = бонус
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

    # Предметы, которые проводятся по подгруппам (ровно две: 1 и 2)
    split_subjects: Set[str] = field(default_factory=set)
    subgroup_ids: Subgroups = field(default_factory=lambda: [1, 2])

    # Учебные планы
    plan_hours: PlanHours = field(default_factory=dict)                     # для НЕподгрупповых
    subgroup_plan_hours: SubgroupPlanHours = field(default_factory=dict)    # для подгрупповых

    # Закрепления учителей
    assigned_teacher: AssignedTeacher = field(default_factory=dict)                 # (c,s) -> t
    subgroup_assigned_teacher: SubgroupAssignedTeacher = field(default_factory=dict) # (c,s,g) -> t

    # Выходные учителей
    days_off: DaysOff = field(default_factory=dict)

    # Ограничения по нагрузке
    teacher_weekly_cap: int = 35

    # Мягкие цели: веса (опционально)
    class_slot_weight: ClassSlotWeight = field(default_factory=dict)
    teacher_slot_weight: TeacherSlotWeight = field(default_factory=dict)
    class_subject_day_weight: ClassSubjectDayWeight = field(default_factory=dict)

    # Разрешённые одновременные комбинации подгрупповых предметов внутри одного класса/слота
    # Множество НЕУПОРЯДОЧЕННЫХ пар (s1, s2), включая «одинаковые», например ("eng", "eng")
    compatible_pairs: Set[Tuple[str, str]] = field(default_factory=set)


# ==============================
# Модель MILP
# ==============================

def build_and_solve_timetable(
    data: InputData,
    lp_path: str = "schedule.lp",
    log: bool = True,
    # Веса цели
    alpha_runs: float = 1000.0,   # анти-окна: минимизация числа блоков
    beta_early: float = 1.0,      # ранние пары
    gamma_balance: float = 10.0,  # баланс по дням
    delta_tail: float = 50.0,     # штраф за пары после 6-й
    pref_scale: float = 1.0       # масштаб предпочтений
):
    C, S, D, P = data.classes, data.subjects, data.days, data.periods
    G = data.subgroup_ids
    splitS = set(data.split_subjects)

    model = pulp.LpProblem("School_Timetabling", sense=pulp.LpMinimize)

    # --------------------------------------------------
    # Переменные
    # --------------------------------------------------
    # НЕподгрупповые назначения: x[c,s,d, p] ∈ {0,1}
    x = pulp.LpVariable.dicts(
        "x",
        ((c, s, d, p) for c, s, d, p in itertools.product(C, S, D, P) if s not in splitS),
        lowBound=0, upBound=1, cat=pulp.LpBinary,
    )

    # Подгрупповые назначения: z[c,s,g,d,p] ∈ {0,1}
    z = pulp.LpVariable.dicts(
        "z",
        ((c, s, g, d, p) for c, s, g, d, p in itertools.product(C, S, G, D, P) if s in splitS),
        lowBound=0, upBound=1, cat=pulp.LpBinary,
    )

    # y[c,d,p] — есть ли ЛЮБОЙ урок у класса (для анти-окон и прочих целей)
    y = pulp.LpVariable.dicts(
        "y",
        ((c, d, p) for c, d, p in itertools.product(C, D, P)),
        lowBound=0, upBound=1, cat=pulp.LpBinary,
    )

    # srun[c,d,p] — начало блока занятий (anti-gaps)
    srun = pulp.LpVariable.dicts(
        "srun",
        ((c, d, p) for c, d, p in itertools.product(C, D, P)),
        lowBound=0, upBound=1, cat=pulp.LpBinary,
    )

    # w_sub[c,d,p] — индикатор «в слоте есть хотя бы одно подгрупповое занятие»
    w_sub = pulp.LpVariable.dicts(
        "wsub",
        ((c, d, p) for c, d, p in itertools.product(C, D, P)),
        lowBound=0, upBound=1, cat=pulp.LpBinary,
    )

    # pres[c,s,d,p] — индикатор «предмет s (из split) присутствует (любой подгруппа)»
    pres = pulp.LpVariable.dicts(
        "pres",
        ((c, s, d, p) for c, s, d, p in itertools.product(C, S, D, P) if s in splitS),
        lowBound=0, upBound=1, cat=pulp.LpBinary,
    )

    # --------------------------------------------------
    # Ограничения
    # --------------------------------------------------
    # (A) Учебный план
    #  A1) НЕподгрупповые: ровно H[c,s]
    for (c, s), h in data.plan_hours.items():
        assert s not in splitS, f"{(c,s)} помечен как split, но указан в plan_hours — используйте subgroup_plan_hours"
        model += pulp.lpSum(x[(c, s, d, p)] for d in D for p in P) == h, f"Plan_{c}_{s}"

    #  A2) Подгрупповые: ровно H[c,s,g] для каждой подгруппы g
    for (c, s, g), h in data.subgroup_plan_hours.items():
        assert s in splitS, f"{(c,s,g)} не split, но есть в subgroup_plan_hours"
        model += pulp.lpSum(z[(c, s, g, d, p)] for d in D for p in P) == h, f"PlanSub_{c}_{s}_g{g}"

    # (B) Связь y с x и z; и «не больше 1» для НЕподгрупповых
    for c, d, p in itertools.product(C, D, P):
        # у класса в слот максимум 1 НЕподгрупповый урок
        model += pulp.lpSum(x[(c, s, d, p)] for s in S if s not in splitS) <= 1, f"Class1slot_nosplit_{c}_{d}_{p}"

        # w_sub — индикатор наличия ЛЮБОГО подгруппового занятия
        z_sum = pulp.lpSum(z[(c, s, g, d, p)] for s in S if s in splitS for g in G)
        model += w_sub[(c, d, p)] <= z_sum
        for s in S:
            if s in splitS:
                for g in G:
                    model += w_sub[(c, d, p)] >= z[(c, s, g, d, p)]

        # Нельзя смешивать НЕподгрупповый урок и подгруппы в одном слоте
        model += pulp.lpSum(x[(c, s, d, p)] for s in S if s not in splitS) + w_sub[(c, d, p)] <= 1, f"NoMix_{c}_{d}_{p}"

        # y — индикатор «что-то идёт в слоте»
        # y >= любой x и любой z; y <= сумма (хотя бы 1 из них активен)
        for s in S:
            if s not in splitS:
                model += y[(c, d, p)] >= x[(c, s, d, p)]
            else:
                for g in G:
                    model += y[(c, d, p)] >= z[(c, s, g, d, p)]
        model += y[(c, d, p)] <= pulp.lpSum(x[(c, s, d, p)] for s in S if s not in splitS) + w_sub[(c, d, p)]

    # (C) Не больше 1 урока ОДНОГО предмета в день
    #  - для НЕподгрупповых: как раньше
    for c, s, d in itertools.product(C, S, D):
        if s not in splitS and (c, s) in data.plan_hours:
            model += pulp.lpSum(x[(c, s, d, p)] for p in P) <= 1, f"SubDaily_{c}_{s}_{d}"

    #  - для подгрупповых: по ПОДГРУППЕ (каждой) максимум 1 в день
    for c, s, g, d in itertools.product(C, S, G, D):
        if s in splitS and (c, s, g) in data.subgroup_plan_hours:
            model += pulp.lpSum(z[(c, s, g, d, p)] for p in P) <= 1, f"SubDailySub_{c}_{s}_g{g}_{d}"

    # (D) Совместимость одновременных подгрупповых занятий внутри класса/слота
    # pres[c,s,d,p] связываем с z
    for c, s, d, p in itertools.product(C, S, D, P):
        if s in splitS:
            # pres == 1 если хотя бы одна подгруппа по этому предмету в слоте
            model += pres[(c, s, d, p)] <= pulp.lpSum(z[(c, s, g, d, p)] for g in G)
            for g in G:
                model += pres[(c, s, d, p)] >= z[(c, s, g, d, p)]

    # Запрещаем все пары присутствий, которых нет в data.compatible_pairs
    # Пары рассматриваем как НЕУПОРЯДОЧЕННЫЕ, включая одинаковые (s,s)
    split_list = sorted(list(splitS))
    for c, d, p in itertools.product(C, D, P):
        for i, s1 in enumerate(split_list):
            for j, s2 in enumerate(split_list[i:]):
                s2 = s2
                pair = tuple(sorted((s1, s2)))
                if pair not in data.compatible_pairs:
                    # pres_s1 + pres_s2 <= 1  (нельзя иметь оба предмета одновременно)
                    model += pres[(c, s1, d, p)] + pres[(c, s2, d, p)] <= 1, f"CompatBan_{c}_{d}_{p}_{s1}_{s2}"

    # (E) Учителя: не вести два класса одновременно + недельная нагрузка
    for t in data.teachers:
        for d, p in itertools.product(D, P):
            # все переменные x, где учитель t закреплён
            term_x = [x[(c, s, d, p)] for (c, s), tt in data.assigned_teacher.items() if tt == t and s not in splitS]
            # все переменные z, где учитель t закреплён за подгруппой
            term_z = [z[(c, s, g, d, p)] for (c, s, g), tt in data.subgroup_assigned_teacher.items() if tt == t and s in splitS]
            if term_x or term_z:
                model += pulp.lpSum(term_x) + pulp.lpSum(term_z) <= 1, f"Teach1slot_{t}_{d}_{p}"

        # недельная нагрузка
        weekly_terms_x = [x[(c, s, d, p)] for (c, s), tt in data.assigned_teacher.items() if tt == t and s not in splitS for d in D for p in P]
        weekly_terms_z = [z[(c, s, g, d, p)] for (c, s, g), tt in data.subgroup_assigned_teacher.items() if tt == t and s in splitS for d in D for p in P]
        if weekly_terms_x or weekly_terms_z:
            model += pulp.lpSum(weekly_terms_x) + pulp.lpSum(weekly_terms_z) <= data.teacher_weekly_cap, f"TeachCap_{t}"

    # (F) Дни без уроков у учителя
    for t, off in data.days_off.items():
        for d in off:
            for p in P:
                term_x = [x[(c, s, d, p)] for (c, s), tt in data.assigned_teacher.items() if tt == t and s not in splitS]
                term_z = [z[(c, s, g, d, p)] for (c, s, g), tt in data.subgroup_assigned_teacher.items() if tt == t and s in splitS]
                if term_x or term_z:
                    model += pulp.lpSum(term_x) + pulp.lpSum(term_z) == 0, f"TeachOff_{t}_{d}_{p}"

    # (G) Anti-gaps: srun логика (как раньше, на y)
    for c, d in itertools.product(C, D):
        p0 = P[0]
        model += srun[(c, d, p0)] == y[(c, d, p0)], f"SRFirst_{c}_{d}"
        for i in range(1, len(P)):
            p = P[i]
            prev = P[i - 1]
            model += srun[(c, d, p)] >= y[(c, d, p)] - y[(c, d, prev)], f"SRLB_{c}_{d}_{p}"
            model += srun[(c, d, p)] <= y[(c, d, p)], f"SRUB_{c}_{d}_{p}"

    # (H) Баланс по дням для классов
    total_hours_c: Dict[str, int] = {c: 0 for c in C}
    # считаем общее число уроков (y) по плану как константу: non-split + split (по подгруппам считаем каждый урок отдельно)
    for (c, s), h in data.plan_hours.items():
        total_hours_c[c] += h
    for (c, s, g), h in data.subgroup_plan_hours.items():
        total_hours_c[c] += h
    avg_c: Dict[str, float] = {c: total_hours_c[c] / float(len(D)) for c in C}

    yday = pulp.LpVariable.dicts("yday", ((c, d) for c, d in itertools.product(C, D)), lowBound=0, upBound=len(P), cat=pulp.LpContinuous)
    devp = pulp.LpVariable.dicts("devp", ((c, d) for c, d in itertools.product(C, D)), lowBound=0, cat=pulp.LpContinuous)
    devn = pulp.LpVariable.dicts("devn", ((c, d) for c, d in itertools.product(C, D)), lowBound=0, cat=pulp.LpContinuous)

    for c, d in itertools.product(C, D):
        model += yday[(c, d)] == pulp.lpSum(y[(c, d, p)] for p in P), f"Yday_{c}_{d}"
        model += yday[(c, d)] - avg_c[c] <= devp[(c, d)], f"BalPos_{c}_{d}"
        model += avg_c[c] - yday[(c, d)] <= devn[(c, d)], f"BalNeg_{c}_{d}"

    # --------------------------------------------------
    # Целевая функция (составная)
    # --------------------------------------------------
    obj_runs = pulp.lpSum(srun[(c, d, p)] for c, d, p in itertools.product(C, D, P))
    obj_early = pulp.lpSum(p * y[(c, d, p)] for c, d, p in itertools.product(C, D, P))
    obj_balance = pulp.lpSum(devp[(c, d)] + devn[(c, d)] for c, d in itertools.product(C, D))
    tail_periods = [p for p in P if p > 6]
    obj_tail = pulp.lpSum(y[(c, d, p)] for c in C for d in D for p in tail_periods)

    # Пользовательские предпочтения
    obj_pref_class = pulp.lpSum(data.class_slot_weight.get((c, d, p), 0.0) * y[(c, d, p)] for c in C for d in D for p in P)
    obj_pref_teacher = pulp.lpSum(
        data.teacher_slot_weight.get((t, d, p), 0.0) * (
            pulp.lpSum(x[(c, s, d, p)] for (c, s), tt in data.assigned_teacher.items() if tt == t and s not in splitS)
            + pulp.lpSum(z[(c, s, g, d, p)] for (c, s, g), tt in data.subgroup_assigned_teacher.items() if tt == t and s in splitS)
        )
        for t in data.teachers for d in D for p in P
    )
    obj_pref_csd = pulp.lpSum(
        data.class_subject_day_weight.get((c, s, d), 0.0) * (
            pulp.lpSum(x[(c, s, d, p)] for p in P) if s not in splitS else pulp.lpSum(z[(c, s, g, d, p)] for g in G for p in P)
        )
        for c in C for s in S for d in D
    )

    model += (
        alpha_runs * obj_runs
        + beta_early * obj_early
        + gamma_balance * obj_balance
        + delta_tail * obj_tail
        + pref_scale * (obj_pref_class + obj_pref_teacher + obj_pref_csd)
    ), "CompositeObjective"

    # --------------------------------------------------
    # Решение
    # --------------------------------------------------
    model.writeLP(lp_path)
    if log:
        print(f"LP-модель сохранена в: {lp_path}")
    solver = pulp.PULP_CBC_CMD(msg=log)
    model.solve(solver)
    if log:
        print("Статус решения:", pulp.LpStatus[model.status])

        return model, x, z, y


# ==============================
# Пример инициализации совместимостей
# ==============================
# Пример для трёх подгрупповых предметов: "eng" (иностранный), "cs" (информатика), "labor" (труд)
# Разрешённые одновременные пары внутри класса/слота:
#  - (eng, eng)
#  - (labor, labor)
#  - (cs, eng)  # информатика одновременно с иностранным
# Для удобства они задаются как неупорядоченные пары (s1,s2) с сортировкой.

def make_default_compat():
    allowed = set()
    def add(a, b):
        allowed.add(tuple(sorted((a, b))))
    add("eng", "eng")
    add("labor", "labor")
    add("cs", "eng")
    return allowed


# ==============================
# __main__: пример запуска + печать расписаний
# ==============================
if __name__ == "__main__":
    # Базовые множества
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    periods = [1, 2, 3, 4, 5, 6, 7]
    classes = ["5A", "5B"]
    subjects = ["math", "eng", "cs", "labor"]  # math — общий; eng/cs/labor — по подгруппам
    teachers = ["Ivanov", "Petrov", "Sidorov", "Smirnov"]

    # Подгрупповые предметы
    split_subjects = {"eng", "cs", "labor"}

    # План часов:
    #  - math по 2 часа на класс (общий)
    #  - у split-предметов по 1 часу на каждую подгруппу (итого 2 часа на класс-предмет)
    plan_hours = {
        ("5A", "math"): 2,
        ("5B", "math"): 2,
    }
    subgroup_plan_hours = {
        ("5A", "eng", 1): 1, ("5A", "eng", 2): 1,
        ("5A", "cs", 1): 1,  ("5A", "cs", 2): 1,
        ("5A", "labor", 1): 1, ("5A", "labor", 2): 1,
        ("5B", "eng", 1): 1, ("5B", "eng", 2): 1,
        ("5B", "cs", 1): 1,  ("5B", "cs", 2): 1,
        ("5B", "labor", 1): 1, ("5B", "labor", 2): 1,
    }

    # Закрепления учителей: общий и подгруппы
    assigned_teacher = {
        ("5A", "math"): "Ivanov",
        ("5B", "math"): "Ivanov",
    }
    subgroup_assigned_teacher = {
        ("5A", "eng", 1): "Sidorov", ("5A", "eng", 2): "Sidorov",
        ("5A", "cs", 1): "Petrov",  ("5A", "cs", 2): "Petrov",
        ("5A", "labor", 1): "Smirnov", ("5A", "labor", 2): "Smirnov",
        ("5B", "eng", 1): "Sidorov", ("5B", "eng", 2): "Sidorov",
        ("5B", "cs", 1): "Petrov",  ("5B", "cs", 2): "Petrov",
        ("5B", "labor", 1): "Smirnov", ("5B", "labor", 2): "Smirnov",
    }

    # Выходные (пример): Петров не работает по понедельникам
    days_off = {
        "Petrov": {"Mon"},
        "Ivanov": set(),
        "Sidorov": set(),
        "Smirnov": set(),
    }

    # Совместимость подгрупповых предметов
    compatible_pairs = make_default_compat()

    data = InputData(
        days=days,
        periods=periods,
        classes=classes,
        subjects=subjects,
        teachers=teachers,
        split_subjects=split_subjects,
        plan_hours=plan_hours,
        subgroup_plan_hours=subgroup_plan_hours,
        assigned_teacher=assigned_teacher,
        subgroup_assigned_teacher=subgroup_assigned_teacher,
        days_off=days_off,
        class_slot_weight={},
        teacher_slot_weight={},
        class_subject_day_weight={},
        compatible_pairs=compatible_pairs,
    )

    model, x, z, y = build_and_solve_timetable(
        data,
        lp_path="schedule.lp",
        log=True,
        alpha_runs=1000.0,
        beta_early=1.0,
        gamma_balance=10.0,
        delta_tail=50.0,
        pref_scale=1.0,
    )

    # -----------------
    # Печать расписания
    # -----------------
    def print_by_classes():
        print("================ РАСПИСАНИЕ ПО КЛАССАМ ================")
        for c in classes:
            print(f"=== Класс {c} ===")
            for d in days:
                row = []
                for p in periods:
                    # общий предмет (не split)
                    subj = None
                    for s in subjects:
                        if s in split_subjects:
                            continue
                        var = x.get((c, s, d, p))
                        if var is not None and pulp.value(var) > 0.5:
                            subj = f"{s} ({assigned_teacher[(c,s)]})"
                            break
                    # если не общий — проверяем подгруппы
                    if subj is None:
                        pieces = []
                        for s in subjects:
                            if s not in split_subjects:
                                continue
                            g_strs = []
                            for g in data.subgroup_ids:
                                varz = z.get((c, s, g, d, p))
                                if varz is not None and pulp.value(varz) > 0.5:
                                    t = data.subgroup_assigned_teacher[(c, s, g)]
                                    g_strs.append(f"{s}[g{g}::{t}]")
                            if g_strs:
                                pieces.extend(g_strs)
                        if pieces:
                            subj = "+".join(pieces)
                    row.append(f"{p}: {subj if subj else '—'}")
                print(f"{d} | "+", ".join(row))

    def print_by_teachers():
        print("================ РАСПИСАНИЕ ПО УЧИТЕЛЯМ ================")
        for t in teachers:
            print(f"=== Учитель {t} ===")
            total = 0
            for d in days:
                row = []
                for p in periods:
                    slot = None
                    # общие предметы
                    for (c, s), tt in assigned_teacher.items():
                        if tt != t:
                            continue
                        var = x.get((c, s, d, p))
                        if var is not None and pulp.value(var) > 0.5:
                            slot = f"{p}: {c} — {s}"
                            total += 1
                            break
                    if slot is None:
                        # подгруппы
                        for (c, s, g), tt in subgroup_assigned_teacher.items():
                            if tt != t:
                                continue
                            varz = z.get((c, s, g, d, p))
                            if varz is not None and pulp.value(varz) > 0.5:
                                slot = f"{p}: {c} — {s}[g{g}]"
                                total += 1
                                break
                    row.append(slot if slot else f"{p}: —")
                print(f"{d} | "+", ".join(row))
            print(f"Итого уроков за неделю: {total}")

    print_by_classes()
    print_by_teachers()
