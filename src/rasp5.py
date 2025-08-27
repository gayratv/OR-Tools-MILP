# School Timetable MILP — with subgroups + diagnostics (CBC)
# ----------------------------------------------------------------------------
# Полная модель с подгруппами, диагностическим режимом DBG и исправлением:
#  - (C2) каждая ПОДГРУППА может быть только на ОДНОМ занятии в один слот
#  - (C3) суммарно не более |G| подгрупповых занятий в слот у класса
# Эти ограничения предотвращают ситуацию, когда у класса в один момент стоит
# больше двух параллельных занятий (для g1,g2), либо одна подгруппа записана
# сразу на несколько предметов одновременно.
# ----------------------------------------------------------------------------

from typing import Dict, Tuple
import itertools
import pulp

from input_data import InputData  # вынесено в отдельный файл
from print_schedule import print_by_classes, print_by_teachers  # функции печати


def make_default_compat():
    """Разрешённые пары одновременных split‑предметов: (eng,eng), (labor,labor), (cs,eng)."""
    allowed = set()
    def add(a, b):
        allowed.add(tuple(sorted((a, b))))
    add("eng", "eng")
    add("labor", "labor")
    add("cs", "eng")
    return allowed


def build_and_solve_timetable(
    data: InputData,
    lp_path: str = "schedule.lp",
    log: bool = True,
    # Веса цели
    alpha_runs: float = 1000.0,   # анти‑окна: минимизация числа блоков занятий
    beta_early: float = 1.0,      # ранние пары
    gamma_balance: float = 1.0,   # баланс по дням
    delta_tail: float = 10.0,     # штраф за пары после 6‑й
    pref_scale: float = 1.0,
    # Диагностический режим (вкл/выкл группы ограничений)
    DBG: Dict[str, bool] = None,
):
    if DBG is None:
        DBG = {
            "teach_overlap": True,  # учитель не ведёт 2 занятия в слот
            "teach_cap": True,      # недельный лимит учителя
            "dayoff": True,         # off‑дни учителей
            "nomix": True,          # нельзя смешивать non‑split и split в одном слоте
            "compat": True,         # запрет несовместимых пар split‑предметов в слоте
        }

    C, S, D, P = data.classes, data.subjects, data.days, data.periods
    G = data.subgroup_ids
    splitS = set(data.split_subjects)

    # --------------------------------------------------
    # Жёсткая проверка входных данных
    # --------------------------------------------------
    for (c, s) in data.plan_hours:
        assert s not in splitS, f"{(c,s)} помечен как split, но указан в plan_hours — используйте subgroup_plan_hours"
        assert (c, s) in data.assigned_teacher, f"Нет учителя для {(c,s)}"
    for (c, s, g) in data.subgroup_plan_hours:
        assert s in splitS, f"{(c,s,g)} не split, но есть в subgroup_plan_hours"
        assert (c, s, g) in data.subgroup_assigned_teacher, f"Нет учителя для {(c,s,g)}"

    prob = pulp.LpProblem("School_Timetabling", sense=pulp.LpMinimize)

    # --------------------------------------------------
    # Переменные
    # --------------------------------------------------
    x = pulp.LpVariable.dicts(
        "x",
        ((c, s, d, p) for c, s, d, p in itertools.product(C, S, D, P) if s not in splitS),
        lowBound=0, upBound=1, cat=pulp.LpBinary,
    )
    z = pulp.LpVariable.dicts(
        "z",
        ((c, s, g, d, p) for c, s, g, d, p in itertools.product(C, S, G, D, P) if s in splitS),
        lowBound=0, upBound=1, cat=pulp.LpBinary,
    )
    y = pulp.LpVariable.dicts(
        "y",
        ((c, d, p) for c, d, p in itertools.product(C, D, P)),
        lowBound=0, upBound=1, cat=pulp.LpBinary,
    )
    srun = pulp.LpVariable.dicts(
        "srun",
        ((c, d, p) for c, d, p in itertools.product(C, D, P)),
        lowBound=0, upBound=1, cat=pulp.LpBinary,
    )
    w_sub = pulp.LpVariable.dicts(
        "wsub",
        ((c, d, p) for c, d, p in itertools.product(C, D, P)),
        lowBound=0, upBound=1, cat=pulp.LpBinary,
    )
    pres = pulp.LpVariable.dicts(
        "pres",
        ((c, s, d, p) for c, s, d, p in itertools.product(C, S, D, P) if s in splitS),
        lowBound=0, upBound=1, cat=pulp.LpBinary,
    )

    # --------------------------------------------------
    # Ограничения
    # --------------------------------------------------
    # План часов: non‑split
    for (c, s), h in data.plan_hours.items():
        prob += pulp.lpSum(x[(c, s, d, p)] for d in D for p in P) == h, f"Plan_{c}_{s}"

    # План часов: split по подгруппам
    for (c, s, g), h in data.subgroup_plan_hours.items():
        prob += pulp.lpSum(z[(c, s, g, d, p)] for d in D for p in P) == h, f"PlanSub_{c}_{s}_g{g}"

    # Связь y, запрет смешивания
    for c, d, p in itertools.product(C, D, P):
        # максимум 1 non‑split урок у класса в слоте
        prob += pulp.lpSum(x[(c, s, d, p)] for s in S if s not in splitS) <= 1, f"Class1slot_nosplit_{c}_{d}_{p}"
        # w_sub индикатор
        z_sum = pulp.lpSum(z[(c, s, g, d, p)] for s in S if s in splitS for g in G)
        prob += w_sub[(c, d, p)] <= z_sum
        for s in S:
            if s in splitS:
                for g in G:
                    prob += w_sub[(c, d, p)] >= z[(c, s, g, d, p)]
        # нельзя смешивать non‑split и split в одном слоте (можно отключить в DBG)
        if DBG.get("nomix", True):
            prob += pulp.lpSum(x[(c, s, d, p)] for s in S if s not in splitS) + w_sub[(c, d, p)] <= 1, f"NoMix_{c}_{d}_{p}"
        # y‑индикатор
        for s in S:
            if s not in splitS:
                prob += y[(c, d, p)] >= x[(c, s, d, p)]
            else:
                for g in G:
                    prob += y[(c, d, p)] >= z[(c, s, g, d, p)]
        prob += y[(c, d, p)] <= pulp.lpSum(x[(c, s, d, p)] for s in S if s not in splitS) + w_sub[(c, d, p)]

    # Не больше 1 урока одного предмета в день: non‑split
    for c, s, d in itertools.product(C, S, D):
        if s not in splitS and (c, s) in data.plan_hours:
            prob += pulp.lpSum(x[(c, s, d, p)] for p in P) <= 1, f"SubDaily_{c}_{s}_{d}"
    # Для подгрупп — по каждой подгруппе ≤ 1 в день
    for c, s, g, d in itertools.product(C, S, G, D):
        if s in splitS and (c, s, g) in data.subgroup_plan_hours:
            prob += pulp.lpSum(z[(c, s, g, d, p)] for p in P) <= 1, f"SubDailySub_{c}_{s}_g{g}_{d}"

    # (C2) Каждая подгруппа может быть только на ОДНОМ занятии в слот
    #      ∀ c,g,d,p: Σ_{s∈split} z[c,s,g,d,p] ≤ 1
    for c, g, d, p in itertools.product(C, G, D, P):
        prob += pulp.lpSum(z[(c, s, g, d, p)] for s in S if s in splitS) <= 1, f"SubgroupSlot_{c}_g{g}_{d}_{p}"

    # (C3) (избыточно) суммарно не более |G| подгрупповых занятий в слот
    for c, d, p in itertools.product(C, D, P):
        prob += pulp.lpSum(z[(c, s, g, d, p)] for s in S if s in splitS for g in G) <= len(G), f"SubgroupSlotTotal_{c}_{d}_{p}"

    # Совместимости split‑предметов
    split_list = sorted(list(splitS))
    for c, d, p in itertools.product(C, D, P):
        for i, s1 in enumerate(split_list):
            for s2 in split_list[i:]:
                pair = tuple(sorted((s1, s2)))
                # pres связываем (независимо от DBG)
                prob += pres[(c, s1, d, p)] <= pulp.lpSum(z[(c, s1, g, d, p)] for g in G)
                prob += pres[(c, s2, d, p)] <= pulp.lpSum(z[(c, s2, g, d, p)] for g in G)
                for g in G:
                    prob += pres[(c, s1, d, p)] >= z[(c, s1, g, d, p)]
                    prob += pres[(c, s2, d, p)] >= z[(c, s2, g, d, p)]
                # запрет несовместимых пар можно отключить через DBG
                if DBG.get("compat", True) and pair not in data.compatible_pairs:
                    prob += pres[(c, s1, d, p)] + pres[(c, s2, d, p)] <= 1, f"CompatBan_{c}_{d}_{p}_{s1}_{s2}"

    # Учителя: занятость и недельный лимит
    for t in data.teachers:
        for d, p in itertools.product(D, P):
            term_x = [x[(c, s, d, p)] for (c, s), tt in data.assigned_teacher.items() if tt == t and s not in splitS]
            term_z = [z[(c, s, g, d, p)] for (c, s, g), tt in data.subgroup_assigned_teacher.items() if tt == t and s in splitS]
            if term_x or term_z:
                if DBG.get("teach_overlap", True):
                    prob += pulp.lpSum(term_x) + pulp.lpSum(term_z) <= 1, f"Teach1slot_{t}_{d}_{p}"
        weekly_x = [x[(c, s, d, p)] for (c, s), tt in data.assigned_teacher.items() if tt == t and s not in splitS for d in D for p in P]
        weekly_z = [z[(c, s, g, d, p)] for (c, s, g), tt in data.subgroup_assigned_teacher.items() if tt == t and s in splitS for d in D for p in P]
        if weekly_x or weekly_z:
            if DBG.get("teach_cap", True):
                prob += pulp.lpSum(weekly_x) + pulp.lpSum(weekly_z) <= data.teacher_weekly_cap, f"TeachCap_{t}"

    # Off‑days
    for t, off in data.days_off.items():
        for d in off:
            for p in P:
                term_x = [x[(c, s, d, p)] for (c, s), tt in data.assigned_teacher.items() if tt == t and s not in splitS]
                term_z = [z[(c, s, g, d, p)] for (c, s, g), tt in data.subgroup_assigned_teacher.items() if tt == t and s in splitS]
                if term_x or term_z:
                    if DBG.get("dayoff", True):
                        prob += pulp.lpSum(term_x) + pulp.lpSum(term_z) == 0, f"TeachOff_{t}_{d}_{p}"

    # Anti‑gaps на y
    for c, d in itertools.product(C, D):
        p0 = P[0]
        prob += srun[(c, d, p0)] == y[(c, d, p0)], f"SRFirst_{c}_{d}"
        for i in range(1, len(P)):
            p = P[i]
            prev = P[i - 1]
            prob += srun[(c, d, p)] >= y[(c, d, p)] - y[(c, d, prev)], f"SRLB_{c}_{d}_{p}"
            prob += srun[(c, d, p)] <= y[(c, d, p)], f"SRUB_{c}_{d}_{p}"

    # Баланс по дням
    total_hours_c = {c: 0 for c in C}
    for (c, s), h in data.plan_hours.items():
        total_hours_c[c] += h
    for (c, s, g), h in data.subgroup_plan_hours.items():
        total_hours_c[c] += h
    avg_c = {c: total_hours_c[c] / float(len(D)) for c in C}

    yday = pulp.LpVariable.dicts("yday", ((c, d) for c, d in itertools.product(C, D)), lowBound=0, upBound=len(P), cat=pulp.LpContinuous)
    devp = pulp.LpVariable.dicts("devp", ((c, d) for c, d in itertools.product(C, D)), lowBound=0, cat=pulp.LpContinuous)
    devn = pulp.LpVariable.dicts("devn", ((c, d) for c, d in itertools.product(C, D)), lowBound=0, cat=pulp.LpContinuous)

    for c, d in itertools.product(C, D):
        prob += yday[(c, d)] == pulp.lpSum(y[(c, d, p)] for p in P), f"Yday_{c}_{d}"
        prob += yday[(c, d)] - avg_c[c] <= devp[(c, d)], f"BalPos_{c}_{d}"
        prob += avg_c[c] - yday[(c, d)] <= devn[(c, d)], f"BalNeg_{c}_{d}"

    # --------------------------------------------------
    # Целевая функция
    # --------------------------------------------------
    obj_runs = pulp.lpSum(srun[(c, d, p)] for c, d, p in itertools.product(C, D, P))
    obj_early = pulp.lpSum(p * y[(c, d, p)] for c, d, p in itertools.product(C, D, P))
    obj_balance = pulp.lpSum(devp[(c, d)] + devn[(c, d)] for c, d in itertools.product(C, D))
    tail_periods = [p for p in P if p > 6]
    obj_tail = pulp.lpSum(y[(c, d, p)] for c in C for d in D for p in tail_periods)

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

    prob += (
        alpha_runs * obj_runs
        + beta_early * obj_early
        + gamma_balance * obj_balance
        + delta_tail * obj_tail
        + pref_scale * (obj_pref_class + obj_pref_teacher + obj_pref_csd)
    ), "CompositeObjective"

    # --------------------------------------------------
    # Решение
    # --------------------------------------------------
    prob.writeLP(lp_path)
    if log:
        print(f"LP-модель сохранена в: {lp_path}")

    # status_code = prob.solve(pulp.PULP_CBC_CMD(msg=log))

    # HiGHS: 16 потоков и 5% относительный GAP; fallback -> CBC
    try:
        solver = pulp.PULP_HIGHS_CMD(
            msg=log,
            threads=16,  # задействуем 16 потоков
            mip_rel_gap=0.05  # 5% допускаемый относительный GAP
            # при желании можно добавить time_limit=120
        )
    except Exception:
        # если HiGHS недоступен в вашей сборке PuLP — откатываемся на CBC
        solver = pulp.PULP_CBC_CMD(msg=log)

    status_code = prob.solve(solver)
    print("Статус решения:", pulp.LpStatus[prob.status], "(code:", status_code, ")")

    if log:
        print("Статус решения:", pulp.LpStatus[prob.status], "(code:", status_code, ")")

    return prob, x, z, y


# ==============================
# __main__: пример + печать
# ==============================
if __name__ == "__main__":
    # Базовые множества
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    periods = [1, 2, 3, 4, 5, 6, 7]
    classes = ["5A", "5B"]
    subjects = ["math", "eng", "cs", "labor"]  # math — общий; eng/cs/labor — split
    teachers = ["Ivanov", "Petrov", "Sidorov", "Smirnov", "Volkov", "Fedorov", "Nikolaev"]

    split_subjects = {"eng", "cs", "labor"}

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

    assigned_teacher = {
        ("5A", "math"): "Ivanov",
        ("5B", "math"): "Volkov",
    }
    subgroup_assigned_teacher = {
        ("5A", "eng", 1): "Sidorov", ("5A", "eng", 2): "Nikolaev",
        ("5A", "cs", 1): "Petrov",  ("5A", "cs", 2): "Fedorov",
        ("5A", "labor", 1): "Smirnov", ("5A", "labor", 2): "Volkov",
        ("5B", "eng", 1): "Sidorov", ("5B", "eng", 2): "Nikolaev",
        ("5B", "cs", 1): "Petrov",  ("5B", "cs", 2): "Fedorov",
        ("5B", "labor", 1): "Smirnov", ("5B", "labor", 2): "Volkov",
    }

    days_off = {
        "Petrov": {"Mon"},
        "Ivanov": set(),
        "Sidorov": set(),
        "Smirnov": set(),
        "Volkov": set(),
        "Fedorov": set(),
        "Nikolaev": set(),
    }

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

    # Диагностический режим: можно точечно выключать ограничения
    DBG = {
        "teach_overlap": True,
        "teach_cap": True,
        "dayoff": False,
        "nomix": False,
        "compat": False,
    }

    prob, x, z, y = build_and_solve_timetable(
        data,
        lp_path="schedule.lp",
        log=True,
        alpha_runs=1000.0,
        beta_early=1.0,
        gamma_balance=1.0,
        delta_tail=10.0,
        pref_scale=1.0,
        DBG=DBG,
    )

    # Печать расписаний
    print_by_classes(data, x, z)
    print_by_teachers(data, x, z)
