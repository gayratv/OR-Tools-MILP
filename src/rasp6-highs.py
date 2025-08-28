import itertools
import pulp
import highspy
from typing import Dict

from input_data import InputData
from print_schedule import print_by_classes, print_by_teachers, summary_load
from export_all_to_excel import export_all_to_excel

def audit_subject(data, x, z, subj="eng"):
    print(f"\n=== AUDIT: {subj} ===")
    # Проверяем, что предмет в списке и помечен как split
    print("subjects has:", subj in data.subjects, " split_subjects has:", subj in data.split_subjects)

    for c in data.classes:
        # сумма из решения (по всем дням/парам/подгруппам)
        placed = 0
        for g in data.subgroup_ids:
            for d in data.days:
                for p in data.periods:
                    var = z.get((c, subj, g, d, p))
                    if var is not None and (pulp.value(var) or 0) > 0.5:
                        placed += 1
        # требуемые часы по плану
        req = sum(data.subgroup_plan_hours.get((c, subj, g), 0) for g in data.subgroup_ids)
        print(f"{c}: placed={placed}  required={req}")

        # отсутствующие закрепления — частая причина
        miss = [g for g in data.subgroup_ids if (c, subj, g) not in data.subgroup_assigned_teacher]
        if miss:
            print(f"   ! no teacher for {(c, subj)} subgroups:", miss)


def check_vars_exist(data, z, subj="eng"):
    cnt = 0
    for c in data.classes:
        for g in data.subgroup_ids:
            for d in data.days:
                for p in data.periods:
                    if (c, subj, g, d, p) in z:
                        cnt += 1
    print(f"z-variables for {subj}: {cnt}")




def make_default_compat():
    """Разрешённые пары одновременных split-предметов"""
    allowed = set()
    def add(a, b):
        allowed.add(tuple(sorted((a, b))))
    add("eng", "eng")
    add("trud", "trud")
    add("informatika", "eng")
    return allowed


def build_and_solve_timetable(
    data: InputData,
    lp_path: str = "schedule.lp",
    log: bool = True,
    alpha_runs: float = 1000.0,
    beta_early: float = 1.0,
    gamma_balance: float = 10.0,
    delta_tail: float = 50.0,
    pref_scale: float = 1.0,
):
    C, S, D, P = data.classes, data.subjects, data.days, data.periods
    G = data.subgroup_ids
    splitS = set(data.split_subjects) # {"eng", "cs", "labor"}' - это уже множество (set).

    prob = pulp.LpProblem("School_Timetabling", sense=pulp.LpMinimize)

    # --------------------------------------------------
    # Переменные
    # --------------------------------------------------
    x = pulp.LpVariable.dicts("x",
        ((c, s, d, p) for c,s,d,p in itertools.product(C,S,D,P) if s not in splitS),
        0,1,cat=pulp.LpBinary)
    z = pulp.LpVariable.dicts("z",
        ((c, s, g, d, p) for c,s,g,d,p in itertools.product(C,S,G,D,P) if s in splitS),
        0,1,cat=pulp.LpBinary)
    y = pulp.LpVariable.dicts("y",
        ((c,d,p) for c,d,p in itertools.product(C,D,P)),
        0,1,cat=pulp.LpBinary)
    srun = pulp.LpVariable.dicts("srun",
        ((c,d,p) for c,d,p in itertools.product(C,D,P)),
        0,1,cat=pulp.LpBinary)

    # --------------------------------------------------
    # Ограничения
    # --------------------------------------------------

    # План часов: non-split
    for (c, s), hIghs in data.plan_hours.items():
        prob += pulp.lpSum(x[(c,s,d,p)] for d in D for p in P) == hIghs

    # План часов: split по подгруппам
    for (c, s, g), subGrpNum in data.subgroup_plan_hours.items():
        prob += pulp.lpSum(z[(c,s,g,d,p)] for d in D for p in P) == subGrpNum

    # Не больше 1 non-split в слот у класса
    for c,d,p in itertools.product(C,D,P):
        prob += pulp.lpSum(x[(c,s,d,p)] for s in S if s not in splitS) <= 1 # splitS - set разбиваемых уроков

        # y связываем с x и z
        for s in S:
            if s not in splitS:
                prob += y[(c,d,p)] >= x[(c,s,d,p)]
            else:
                for g in G:
                    prob += y[(c,d,p)] >= z[(c,s,g,d,p)]
        prob += y[(c,d,p)] <= (
            pulp.lpSum(x[(c,s,d,p)] for s in S if s not in splitS) +
            pulp.lpSum(z[(c,s,g,d,p)] for s in S if s in splitS for g in G)
        )

    # Не больше 1 урока предмета в день
    for c,s,d in itertools.product(C,S,D):
        if s not in splitS and (c,s) in data.plan_hours:
            prob += pulp.lpSum(x[(c,s,d,p)] for p in P) <= 1
    for c,s,g,d in itertools.product(C,S,G,D):
        if s in splitS and (c,s,g) in data.subgroup_plan_hours:
            prob += pulp.lpSum(z[(c,s,g,d,p)] for p in P) <= 1

    # Каждая подгруппа только на одном занятии в слот
    for c,g,d,p in itertools.product(C,G,D,P):
        prob += pulp.lpSum(z[(c,s,g,d,p)] for s in S if s in splitS) <= 1

    # Совместимости split
    split_list = sorted(list(splitS))
    for c,d,p in itertools.product(C,D,P):
        for i,s1 in enumerate(split_list):
            for s2 in split_list[i:]:
                pair = tuple(sorted((s1,s2)))
                pres1 = pulp.lpSum(z[(c,s1,g,d,p)] for g in G if s1 in splitS)
                pres2 = pulp.lpSum(z[(c,s2,g,d,p)] for g in G if s2 in splitS)
                if pair not in data.compatible_pairs:
                    prob += pres1 + pres2 <= 1

    # Учителя: не более 1 урока в слот
    for t in data.teachers:
        for d,p in itertools.product(D,P):
            term_x = [x[(c,s,d,p)] for (c,s),tt in data.assigned_teacher.items() if tt==t]
            term_z = [z[(c,s,g,d,p)] for (c,s,g),tt in data.subgroup_assigned_teacher.items() if tt==t]
            if term_x or term_z:
                prob += pulp.lpSum(term_x)+pulp.lpSum(term_z) <= 1
        weekly_x = [x[(c,s,d,p)] for (c,s),tt in data.assigned_teacher.items() if tt==t for d in D for p in P]
        weekly_z = [z[(c,s,g,d,p)] for (c,s,g),tt in data.subgroup_assigned_teacher.items() if tt==t for d in D for p in P]
        if weekly_x or weekly_z:
            prob += pulp.lpSum(weekly_x)+pulp.lpSum(weekly_z) <= data.teacher_weekly_cap

    # Anti-gaps
    for c,d in itertools.product(C,D):
        p0 = P[0]
        prob += srun[(c,d,p0)] == y[(c,d,p0)]
        for i in range(1,len(P)):
            p = P[i]; prev = P[i-1]
            prob += srun[(c,d,p)] >= y[(c,d,p)] - y[(c,d,prev)]
            prob += srun[(c,d,p)] <= y[(c,d,p)]

    # Баланс по дням
    total_hours_c = {c:0 for c in C}
    for (c,s),hIghs in data.plan_hours.items():
        total_hours_c[c]+=hIghs
    for (c,s,g),hIghs in data.subgroup_plan_hours.items():
        total_hours_c[c]+=hIghs
    avg_c = {c: total_hours_c[c]/float(len(D)) for c in C}

    yday = pulp.LpVariable.dicts("yday",((c,d) for c,d in itertools.product(C,D)),0,len(P))
    devp = pulp.LpVariable.dicts("devp",((c,d) for c,d in itertools.product(C,D)),0)
    devn = pulp.LpVariable.dicts("devn",((c,d) for c,d in itertools.product(C,D)),0)
    for c,d in itertools.product(C,D):
        prob += yday[(c,d)] == pulp.lpSum(y[(c,d,p)] for p in P)
        prob += yday[(c,d)] - avg_c[c] <= devp[(c,d)]
        prob += avg_c[c] - yday[(c,d)] <= devn[(c,d)]

    # --------------------------------------------------
    # Целевая функция
    # --------------------------------------------------
    obj_runs = pulp.lpSum(srun[(c,d,p)] for c,d,p in itertools.product(C,D,P))
    obj_early = pulp.lpSum(p*y[(c,d,p)] for c,d,p in itertools.product(C,D,P))
    obj_balance = pulp.lpSum(devp[(c,d)]+devn[(c,d)] for c,d in itertools.product(C,D))
    tail_periods = [p for p in P if p>6]
    obj_tail = pulp.lpSum(y[(c,d,p)] for c in C for d in D for p in tail_periods)

    obj_pref_class = pulp.lpSum(data.class_slot_weight.get((c,d,p),0.0)*y[(c,d,p)]
                                for c in C for d in D for p in P)
    obj_pref_teacher = pulp.lpSum(
        data.teacher_slot_weight.get((t,d,p),0.0)*(
            pulp.lpSum(x[(c,s,d,p)] for (c,s),tt in data.assigned_teacher.items() if tt==t)
            + pulp.lpSum(z[(c,s,g,d,p)] for (c,s,g),tt in data.subgroup_assigned_teacher.items() if tt==t)
        )
        for t in data.teachers for d in D for p in P)
    obj_pref_csd = pulp.lpSum(
        data.class_subject_day_weight.get((c,s,d),0.0)*(
            pulp.lpSum(x[(c,s,d,p)] for p in P) if s not in splitS
            else pulp.lpSum(z[(c,s,g,d,p)] for g in G for p in P)
        )
        for c in C for s in S for d in D)

    prob += (alpha_runs*obj_runs
             + beta_early*obj_early
             + gamma_balance*obj_balance
             + delta_tail*obj_tail
             + pref_scale*(obj_pref_class+obj_pref_teacher+obj_pref_csd))

    # --------------------------------------------------
    # Решение через HiGHS
    # --------------------------------------------------
    prob.writeLP(lp_path)
    if log:
        print(f"LP-модель сохранена в: {lp_path}")

    hIghs = highspy.Highs()
    hIghs.setOptionValue("threads", 16)
    hIghs.setOptionValue("mip_rel_gap", 0.05)
    hIghs.readModel(lp_path)
    hIghs.run()

    status = hIghs.getModelStatus()
    obj = hIghs.getObjectiveValue()
    if log:
        print("Статус HiGHS:", status, "Obj:", obj)

    # Загружаем решение обратно
    sol = hIghs.getSolution().col_value
    col_names = hIghs.getLp().col_names_
    values = {name: val for name, val in zip(col_names, sol)}

    # for var in prob.variables():
    #     var.varValue = values.get(var.name, 0.0)

    missed = 0
    for var in prob.variables():
        if var.name in values:
            var.varValue = values[var.name]
        else:
            var.varValue = 0.0
            missed += 1
    print("Vars with no value from HiGHS:", missed)

    return prob, x, z, y


if __name__ == "__main__":
    # Пример
    days = ["Mon","Tue","Wed","Thu","Fri"]
    periods = [1,2,3,4,5,6,7]
    classes = ["5A","5B"]
    subjects = ["math","eng","informatika","trud"]
    teachers = ["Ivanov","Petrov","Sidorov","Smirnov","Volkov","Fedorov","Nikolaev"]

    split_subjects = {"eng","informatika","trud"}
    plan_hours = {("5A","math"):2,("5B","math"):2}
    subgroup_plan_hours = {
        ("5A","eng",1):1,("5A","eng",2):1,
        ("5B","eng",1):1,("5B","eng",2):1
    }
    assigned_teacher = {("5A","math"):"Ivanov",("5B","math"):"Volkov"}
    subgroup_assigned_teacher = {
        ("5A","eng",1):"Sidorov",("5A","eng",2):"Nikolaev",
        ("5B","eng",1):"Sidorov",("5B","eng",2):"Nikolaev"
    }

    data = InputData(
        days=days,periods=periods,classes=classes,subjects=subjects,teachers=teachers,
        split_subjects=split_subjects,
        plan_hours=plan_hours,
        subgroup_plan_hours=subgroup_plan_hours,
        assigned_teacher=assigned_teacher,
        subgroup_assigned_teacher=subgroup_assigned_teacher,
        compatible_pairs=make_default_compat()

    )

    prob, x, z, y = build_and_solve_timetable(data, log=True)
    audit_subject(data, x, z, "eng")
    check_vars_exist(data, z, "eng")

    print_by_classes(data, x, z)
    print_by_teachers(data, x, z)
    # summary_load(data, x, z)

    # экспорт в Excel
    # export_all_to_excel("timetable.xlsx", data, x, z)
