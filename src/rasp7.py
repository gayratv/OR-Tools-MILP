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

import highspy
import pulp

from input_data import InputData, OptimizationWeights
from rasp_data import create_timetable_data


# ------------------------------
# Построение и решение модели
# ------------------------------

def build_and_solve_timetable(
        data: InputData,
        lp_path: str = "schedule.lp",
        log: bool = True,

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
    G = data.subgroup_ids  # определено в типе - номера подгрупп
    splitS = set(data.split_subjects)  # {"eng", "cs", "labor"}' - это уже множество (set).

    weights = OptimizationWeights()
    alpha_runs = weights.alpha_runs
    beta_early = weights.beta_early
    gamma_balance = weights.gamma_balance
    delta_tail = weights.delta_tail
    pref_scale = weights.pref_scale
    last_ok_period = weights.last_ok_period

    model = pulp.LpProblem("School_Timetabling", sense=pulp.LpMinimize)

    # Переменные назначения
    # x[(c, s, d, p)] ∈ {0,1} — у класса c предмет s в день d, урок p.
    x = pulp.LpVariable.dicts(
        "x", ((c, s, d, p) for c, s, d, p in itertools.product(C, S, D, P)),
        lowBound=0, upBound=1, cat=pulp.LpBinary
    )
    # y[c,d,p] = 1 если в слоте день, час есть ЛЮБОЙ урок у класса c
    y = pulp.LpVariable.dicts(
        "y", ((c, d, p) for c, d, p in itertools.product(C, D, P)),
        lowBound=0, upBound=1, cat=pulp.LpBinary
    )

    # 1 если для подгруппы проводится урок
    # z[(c, s, g, d, p)] ∈ {0,1}
    z = pulp.LpVariable.dicts(
        "z", ((c, s, g, d, p) for c, s, g, d, p in itertools.product(C, S, G, D, P) if s in splitS),
        0, 1, cat=pulp.LpBinary)

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

    # is_subj_taught[(c, s, d, p)] = 1, если предмет s преподается ЛЮБОЙ подгруппе класса c в данном слоте
    is_subj_taught = pulp.LpVariable.dicts(
        "is_subj_taught", ((c, s, d, p) for c, s, d, p in itertools.product(C, splitS, D, P)),
        cat=pulp.LpBinary
    )

    # ------------------------------
    # Ограничения
    # ------------------------------

    # Учебный план
    # с- class s - предмет h - часы
    for (c, s), h in data.plan_hours.items():
        model += pulp.lpSum(x[(c, s, d, p)] for d in D for p in P) == h, f"Plan_{c}_{s}"

    # План часов: split по подгруппам
    # z- если есть урок в подгруппе
    for (c, s, g), h in data.subgroup_plan_hours.items():
        model += pulp.lpSum(z[(c, s, g, d, p)] for d in D for p in P) == h

    # Не больше 1 non-split в слот у класса
    for c, d, p in itertools.product(C, D, P):
        model += pulp.lpSum(x[(c, s, d, p)] for s in S if s not in splitS) <= 1  # splitS - set разбиваемых уроков

        # y связываем с x и z
        for s in S:
            if s not in splitS:
                model += y[(c, d, p)] >= x[(c, s, d, p)]
            else:
                for g in G:
                    model += y[(c, d, p)] >= z[(c, s, g, d, p)]

        # это уравнение нужно, чтобы установить y в 0
        # если нет занятий то предыдущее уравнение говорит что y>=0 , те y может быть 0 и 1
        model += y[(c, d, p)] <= (
                pulp.lpSum(x[(c, s, d, p)] for s in S if s not in splitS) +
                pulp.lpSum(z[(c, s, g, d, p)] for s in S if s in splitS for g in G)
        )

    # Каждая подгруппа только на одном занятии в слот, два предмета не могут быть назначены на одно время
    for c, g, d, p in itertools.product(C, G, D, P):
        model += pulp.lpSum(z[(c, s, g, d, p)] for s in S if s in splitS) <= 1

    # Нельзя одновременно ставить урок для всего класса и для его подгруппы в один и тот же слот
    for c, g, d, p in itertools.product(C, G, D, P):
        model += (pulp.lpSum(x[(c, s, d, p)] for s in S if s not in splitS) +
                  pulp.lpSum(z[(c, s, g, d, p)] for s in S if s in splitS)
                  ) <= 1, f"No_Class_Subgroup_Clash_{c}_{g}_{d}_{p}"

    # У класса не более 1 урока в слот; связь y с x
    # Цикл проходит по каждой возможной комбинации класс (c), Дня (d) и Периода (p).

    # Не больше 2 урока предмета в день (могут быть 2 алгебры)

    # Переменные означают следующее:
     # •C: Список всех Классов(например, '9А', '10Б').
     # •S: Список всех предметов(Subjects), например, 'Математика', 'История'.
     # •D: Список всех учебных Дней(например, 'Понедельник', 'Вторник').
     # •P: Список всех уроков - Периодов в течение одного дня(например, 1, 2, 3, 4).
     # •G: Список всех подгрупп(например, 'Группа 1', 'Группа 2').
     # •x и z: Это бинарные переменные решения для модели
     # •x — для уроков всего класса,
     # •z — для уроков в подгруппах.
     # Они равны 1, если урок запланирован на определенное время, и 0 в противном случае.

    for c, s, d in itertools.product(C, S, D):
        if s not in splitS and (c, s) in data.plan_hours:
            model += pulp.lpSum(x[(c, s, d, p)] for p in P) <= 2

    for c, s, g, d in itertools.product(C, S, G, D):
        if s in splitS and (c, s, g) in data.subgroup_plan_hours:
            model += pulp.lpSum(z[(c, s, g, d, p)] for p in P) <= 2

    # --- Совместимость "делящихся" предметов ---

    # Связь z и is_subj_taught: флаг, что предмет s преподается классу c в слоте (d,p)
    for c, s, d, p in itertools.product(C, splitS, D, P):
        # Если хотя бы одна подгруппа g изучает предмет s, is_subj_taught должен стать 1
        for g in G:
            model += is_subj_taught[(c, s, d, p)] >= z[(c, s, g, d, p)], f"Link_is_subj_taught_up_{c}_{s}_{d}_{p}_{g}"
        # Если ни одна подгруппа не изучает предмет s, is_subj_taught должен стать 0
        model += is_subj_taught[(c, s, d, p)] <= pulp.lpSum(z[(c, s, g, d, p)] for g in G), f"Link_is_subj_taught_down_{c}_{s}_{d}_{p}"

    # Ограничение совместимости: в одном слоте у класса могут быть только совместимые "делящиеся" предметы
    split_list = sorted(list(splitS))
    for c, d, p in itertools.product(C, D, P):
        for s1, s2 in itertools.combinations(split_list, 2):
            pair = (s1, s2)
            # Проверяем в обоих направлениях, если compatible_pairs не отсортированы
            if pair not in data.compatible_pairs and (s2, s1) not in data.compatible_pairs:
                # Если предметы s1 и s2 несовместимы, они не могут преподаваться одновременно
                # разным подгруппам одного класса.
                model += is_subj_taught[(c, s1, d, p)] + is_subj_taught[(c, s2, d, p)] <= 1, \
                    f"Incompatible_Pair_{c}_{d}_{p}_{s1}_{s2}"

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

    missed = 0
    for var in model.variables():
        if var.name in values:
            var.varValue = values[var.name]
        else:
            var.varValue = 0.0
            missed += 1
    print("Vars with no value from HiGHS:", missed)

    return model, x, y


# ------------------------------
# Пример запуска
# ------------------------------
if __name__ == "__main__":
    data = create_timetable_data()

    build_and_solve_timetable(
        data,
        lp_path="schedule.lp",
        log=True,
    )
