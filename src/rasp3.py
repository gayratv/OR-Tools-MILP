# Описание основных структур данных и переменных модели расписания

# --- Входные данные (Python-структуры) ---
# days: список дней недели, например ["Mon", "Tue", ...]
# periods: список номеров уроков, например [1,2,3,4,5,6,7]
# classes: список классов, например ["5A", "5B"]
# subjects: список предметов, например ["math", "cs", "eng"]
# teachers: список учителей, например ["Ivanov", "Petrov"]
# plan_hours: словарь {(class, subject): часы в неделю}
# assigned_teacher: словарь {(class, subject): teacher}
# days_off: словарь {teacher: {дни, когда не работает}}
# teacher_preferences: {teacher -> {day -> weight}} — мягкие предпочтения по дням
# class_preferences: {class -> {day -> weight}} — мягкие предпочтения по дням

# --- Переменные MILP (pulp) ---
# x[(c,s,d,p)] ∈ {0,1} — бинарная переменная: =1 если класс c изучает предмет s в день d на уроке p.
# y[(c,d,p)] ∈ {0,1} — бинарная переменная: =1 если у класса c есть ЛЮБОЙ урок в слот (d,p).
# s_run[(c,d,p)] ∈ {0,1} — бинарная переменная: =1 если слот (d,p) является началом блока занятий (anti-gap логика).

# --- Ограничения ---
# 1. Учебный план: сумма x по всем дням/урокам для (c,s) = требуемые часы.
# 2. У класса не более 1 урока одновременно: сумма x[(c,s,d,p)] ≤ 1.
# 3. Связь x и y: y[(c,d,p)] ≥ x[(c,s,d,p)] и y[(c,d,p)] ≤ Σ_s x[(c,s,d,p)].
# 4. Не более 1 урока одного предмета в день: Σ_p x[(c,s,d,p)] ≤ 1.
# 5. Ограничения по учителям: не более 1 урока одновременно; недельный максимум ≤ cap.
# 6. Дни отдыха учителей: в эти дни у них не может быть уроков.
# 7. Anti-gap: s_run ≥ y(p) - y(p-1) и s_run ≤ y(p). Начало блока фиксируется.

# --- Целевая функция ---
# obj_runs: минимизация числа блоков (anti-окна).
# obj_early: минимизация поздних уроков (тянуть к ранним).
# obj_balance: баланс нагрузки по дням (сумма квадратов отклонений от среднего).
# obj_tail: штраф за «хвосты» после 6-го урока.
# obj_pref: мягкие предпочтения учителей и классов.

# Итоговая цель: Minimize alpha*obj_runs + beta*obj_early + gamma*obj_balance + delta*obj_tail + obj_pref


from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple
import itertools
import pulp

# ------------------------------
# Типы
# ------------------------------
Days = List[str]
Periods = List[int]
Classes = List[str]
Subjects = List[str]
Teachers = List[str]

PlanHours = Dict[Tuple[str, str], int]
AssignedTeacher = Dict[Tuple[str, str], str]
DaysOff = Dict[str, Set[str]]

# Предпочтения / штрафы (мягкие цели)
# Положительные значения = штрафы (хуже), отрицательные = бонусы (лучше)
# Все ключи необязательны — если нет в словаре, то 0.
ClassSlotWeight = Dict[Tuple[str, str, int], float]          # (class, day, period) -> weight
TeacherSlotWeight = Dict[Tuple[str, str, int], float]        # (teacher, day, period) -> weight
ClassSubjectDayWeight = Dict[Tuple[str, str, str], float]    # (class, subject, day) -> weight


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

    # Мягкие цели: веса (по умолчанию пусто)
    class_slot_weight: ClassSlotWeight = field(default_factory=dict)
    teacher_slot_weight: TeacherSlotWeight = field(default_factory=dict)
    class_subject_day_weight: ClassSubjectDayWeight = field(default_factory=dict)


# ------------------------------
# Построение и решение модели
# ------------------------------

def build_and_solve_timetable(
    data: InputData,
    lp_path: str = "schedule.lp",
    log: bool = True,
    # Веса для составной целевой функции
    alpha_runs: float = 1000.0,   # анти-окна: минимизация числа блоков занятий
    beta_early: float = 1.0,      # лёгкое предпочтение ранних уроков
    gamma_balance: float = 10.0,  # баланс по дням (L1-отклонение от среднего)
    delta_tail: float = 50.0,     # штраф за «хвосты» после 6-го урока (soft ban)
    pref_scale: float = 1.0       # масштаб для пользовательских предпочтений
):
    """
    Модель MILP школьного расписания с мягкими целями:
      - анти-окна (минимизация числа блоков у классов);
      - ранние уроки (минимизировать суммарный индекс слотов);
      - баланс по дням (минимизировать |уроков в день - среднее|);
      - «запрет хвостов» после 6-го урока (штраф за поздние слоты);
      - предпочтения/штрафы от пользователя (классы, учителя, предмет-день).
    """

    C, S, D, P = data.classes, data.subjects, data.days, data.periods
    last_ok_period = 6  # после этого слота начинаются «хвосты» (мягко штрафуем)

    model = pulp.LpProblem("School_Timetabling", sense=pulp.LpMinimize)

    # Переменные назначения
    x = pulp.LpVariable.dicts(
        "x", ((c, s, d, p) for c, s, d, p in itertools.product(C, S, D, P)),
        lowBound=0, upBound=1, cat=pulp.LpBinary
    )
    # y[c,d,p] = 1 если в слоте есть ЛЮБОЙ урок у класса c
    y = pulp.LpVariable.dicts(
        "y", ((c, d, p) for c, d, p in itertools.product(C, D, P)),
        lowBound=0, upBound=1, cat=pulp.LpBinary
    )
    # srun[c,d,p] — начало блока занятий у класса
    srun = pulp.LpVariable.dicts(
        "srun", ((c, d, p) for c, d, p in itertools.product(C, D, P)),
        lowBound=0, upBound=1, cat=pulp.LpBinary
    )

    # Для баланса: суммарные уроки в день у класса (целое)
    yday = pulp.LpVariable.dicts(
        "yday", ((c, d) for c, d in itertools.product(C, D)),
        lowBound=0, upBound=len(P), cat=pulp.LpInteger
    )
    # Отклонения от среднего по дням (неотрицательные непрерывные)
    dev_pos = pulp.LpVariable.dicts(
        "devp", ((c, d) for c, d in itertools.product(C, D)), lowBound=0, cat=pulp.LpContinuous
    )
    dev_neg = pulp.LpVariable.dicts(
        "devn", ((c, d) for c, d in itertools.product(C, D)), lowBound=0, cat=pulp.LpContinuous
    )

    # ------------------------------
    # Ограничения
    # ------------------------------

    # Учебный план
    for (c, s), h in data.plan_hours.items():
        model += pulp.lpSum(x[(c, s, d, p)] for d in D for p in P) == h, f"Plan_{c}_{s}"

    # У класса не более 1 урока в слот; связь y с x
    for c, d, p in itertools.product(C, D, P):
        model += pulp.lpSum(x[(c, s, d, p)] for s in S) <= 1, f"Class1slot_{c}_{d}_{p}"
        for s in S:
            model += y[(c, d, p)] >= x[(c, s, d, p)]
        model += y[(c, d, p)] <= pulp.lpSum(x[(c, s, d, p)] for s in S)

    # Не больше 1 урока одного предмета в день на класс
    for c, s, d in itertools.product(C, S, D):
        if (c, s) in data.plan_hours and data.plan_hours[(c, s)] > 0:
            model += pulp.lpSum(x[(c, s, d, p)] for p in P) <= 1, f"SubDaily_{c}_{s}_{d}"

    # Группировка по учителям
    by_teacher: Dict[str, List[Tuple[str, str]]] = {t: [] for t in data.teachers}
    for (c, s), t in data.assigned_teacher.items():
        by_teacher[t].append((c, s))

    # Учитель не ведёт два класса одновременно
    for t in data.teachers:
        cs_pairs = by_teacher.get(t, [])
        for d, p in itertools.product(D, P):
            if cs_pairs:
                model += pulp.lpSum(x[(c, s, d, p)] for (c, s) in cs_pairs) <= 1, f"Teach1slot_{t}_{d}_{p}"

    # Недельная нагрузка учителя ≤ cap
    for t in data.teachers:
        cs_pairs = by_teacher.get(t, [])
        if cs_pairs:
            model += pulp.lpSum(x[(c, s, d, p)] for (c, s) in cs_pairs for d in D for p in P) <= data.teacher_weekly_cap, f"TeachCap_{t}"

    # Дни без уроков у учителя
    for t, off_days in data.days_off.items():
        cs_pairs = by_teacher.get(t, [])
        for d in off_days:
            for p in P:
                model += pulp.lpSum(x[(c, s, d, p)] for (c, s) in cs_pairs) == 0, f"TeachOff_{t}_{d}_{p}"

    # Логика блоков занятий (anti-gaps)
    for c, d in itertools.product(C, D):
        p0 = P[0]
        # model += srun[(c, d, p0)] >= y[(c, d, p0)]
        # model += srun[(c, d, p0)] <= y[(c, d, p0)]
        model += srun[(c, d, p0)] == y[(c, d, p0)]
        for i in range(1, len(P)):
            p = P[i]
            prev = P[i - 1]
            model += srun[(c, d, p)] >= y[(c, d, p)] - y[(c, d, prev)]
            model += srun[(c, d, p)] <= y[(c, d, p)]

    # Подсчёт yday и связь с y
    for c, d in itertools.product(C, D):
        model += yday[(c, d)] == pulp.lpSum(y[(c, d, p)] for p in P), f"YdayDef_{c}_{d}"

    # Баланс по дням: |yday - avg_c| = dev_pos - dev_neg, dev_pos,dev_neg >= 0
    # avg_c = total_hours_c / |D| — константа (может быть дробной)
    total_hours_c: Dict[str, int] = {c: 0 for c in C}
    for (c, s), h in data.plan_hours.items():
        total_hours_c[c] += h
    avg_c: Dict[str, float] = {c: (total_hours_c[c] / float(len(D))) for c in C}

    for c, d in itertools.product(C, D):
        # yday - avg = dev_pos - dev_neg
        # Это две линейные неравенства:
        # yday - avg <= dev_pos
        # -(yday - avg) <= dev_neg  => avg - yday <= dev_neg
        model += yday[(c, d)] - avg_c[c] <= dev_pos[(c, d)], f"BalPos_{c}_{d}"
        model += avg_c[c] - yday[(c, d)] <= dev_neg[(c, d)], f"BalNeg_{c}_{d}"

    # ------------------------------
    # Целевая функция (составная)
    # ------------------------------
    # 1) Анти-окна: минимизировать число блоков у классов
    obj_runs = pulp.lpSum(srun[(c, d, p)] for c, d, p in itertools.product(C, D, P))

    # 2) Ранние слоты
    obj_early = pulp.lpSum(p * y[(c, d, p)] for c, d, p in itertools.product(C, D, P))

    # 3) Баланс по дням (L1-норма отклонений)
    obj_balance = pulp.lpSum(dev_pos[(c, d)] + dev_neg[(c, d)] for c, d in itertools.product(C, D))

    # 4) «Хвосты» после 6-го урока (штраф за поздние слоты)
    late_periods = [p for p in P if p > last_ok_period]
    obj_tail = pulp.lpSum(y[(c, d, p)] for c in C for d in D for p in late_periods)

    # 5) Пользовательские предпочтения
    #    a) по слотам класса
    # Это     кусок     мягких     предпочтений    в    целевой    функции.Он     добавляет
    # штрафы / бонусы     за    то, что    у    конкретного    класса    в    конкретный    день    и
    # на    конкретной    паре    стоит    урок.
    obj_pref_class = pulp.lpSum(
        data.class_slot_weight.get((c, d, p), 0.0) * y[(c, d, p)]
        for c in C for d in D for p in P
    )
    #    b) по слотам учителя (применяем к сумме x у всех его классов/предметов)
    # Она    штрафует / поощряет    занятия    учителя    в    конкретные    день + пара.
    # data.teacher_slot_weight = {
    #     ("Petrov", "Fri", 7): 10.0,  # не хотим позднюю пятницу для Петрова
    #     ("Ivanov", "Mon", 1): -2.0,  # Иванову удобно ранним утром в понедельник
    # }

    obj_pref_teacher = pulp.lpSum(
        data.teacher_slot_weight.get((t, d, p), 0.0) * pulp.lpSum(x[(c, s, d, p)] for (c, s) in by_teacher.get(t, []))
        for t in data.teachers for d in D for p in P
    )
    #    c) по дню для конкретного предмета у класса
    # data.class_subject_day_weight = {
    #     ("5A", "math", "Mon"): 5.0,  # не хотим математику по понедельникам
    #     ("5B", "eng", "Fri"): -3.0  # хорошо, если у 5B английский в пятницу
    # }

    obj_pref_csd = pulp.lpSum(
        data.class_subject_day_weight.get((c, s, d), 0.0) * pulp.lpSum(x[(c, s, d, p)] for p in P)
        for c in C for s in S for d in D
    )

    model += (
        alpha_runs * obj_runs
        + beta_early * obj_early
        + gamma_balance * obj_balance
        + delta_tail * obj_tail
        + pref_scale * (obj_pref_class + obj_pref_teacher + obj_pref_csd)
    ), "CompositeObjective"

    # ------------------------------
    # Решение CBC
    # ------------------------------
    model.writeLP(lp_path)
    if log:
        print(f"LP-модель сохранена в: {lp_path}")

    solver = pulp.PULP_CBC_CMD(msg=log)
    model.solve(solver)

    if log:
        print("Статус решения:", pulp.LpStatus[model.status])

    if pulp.LpStatus[model.status] not in ("Optimal", "Feasible"):
        if log:
            print("Решение не найдено (несовместная модель или иная проблема).")
        return None

    # ------------------------------
    # Вывод расписания по классам
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
            print(f"{d} | "+", ".join(row))

    # ------------------------------
    # Вывод расписания по учителям + недельная нагрузка
    # ------------------------------
    print("\n================ РАСПИСАНИЕ ПО УЧИТЕЛЯМ ================")
    for t in data.teachers:
        cs_pairs = by_teacher.get(t, [])
        if not cs_pairs:
            print(f"\n=== Учитель {t} ===\n(нет закреплённых предметов/классов)")
            continue
        print(f"\n=== Учитель {t} ===")
        total = 0
        for d in D:
            row = []
            for p in P:
                slot = None
                for (c, s) in cs_pairs:
                    if pulp.value(x[(c, s, d, p)]) > 0.5:
                        slot = f"{p}: {c} — {s}"
                        total += 1
                        break
                row.append(slot if slot else f"{p}: —")
            print(f"{d} | "+", ".join(row))
        print(f"Итого уроков за неделю: {total} (лимит {data.teacher_weekly_cap})")

    return model  # при необходимости можно вернуть и переменные


# ------------------------------
# Пример запуска
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
        "Petrov": {"Mon"},
        "Ivanov": set(),
        "Sidorov": set(),
    }

    # Пример предпочтений:
    #  - Штрафуем поздние слоты у 5A по пятницам
    class_slot_weight = {
        ("5A", "Fri", 7): 10.0,
        ("5A", "Fri", 6): 5.0,
    }
    #  - Учитель Петров не любит 1-й урок во вторник
    teacher_slot_weight = {
        ("Petrov", "Tue", 1): 8.0,
    }
    #  - Классу 5B лучше не ставить math по понедельникам
    class_subject_day_weight = {
        ("5B", "math", "Mon"): 6.0,
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
        class_slot_weight=class_slot_weight,
        teacher_slot_weight=teacher_slot_weight,
        class_subject_day_weight=class_subject_day_weight,
    )

    build_and_solve_timetable(
        data,
        lp_path="schedule.lp",
        log=True,
        alpha_runs=1000.0,
        beta_early=1.0,
        gamma_balance=10.0,
        delta_tail=50.0,
        pref_scale=1.0,
    )
