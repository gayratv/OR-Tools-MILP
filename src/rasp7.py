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

from input_data_OptimizationWeights_types import InputData, OptimizationWeights
from access_loader import load_data_from_access
from rasp_data import create_timetable_data as create_manual_data
from rasp_data_generated import create_timetable_data as create_generated_data
from print_schedule import print_by_classes, print_by_teachers, summary_load, export_full_schedule_to_excel, export_raw_data_to_excel


# ------------------------------
# Построение и решение модели
# ------------------------------

def build_and_solve_timetable(
        data: InputData,
        lp_path: str = "schedule.lp",
        db_path: str = None, # Добавляем db_path как необязательный аргумент
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

    # --- Учебный план ---
    # Проходим по всем возможным урокам и накладываем ограничения

    # Для обычных (неделимых) предметов
    for c, s in itertools.product(C, S):
        if s not in splitS:
            required_hours = data.plan_hours.get((c, s), 0)
            model += pulp.lpSum(x[(c, s, d, p)] for d in D for p in P) == required_hours, f"Plan_{c}_{s}"

    # Для делимых предметов
    for c, s, g in itertools.product(C, S, G):
        if s in splitS:
            # Получаем требуемые часы из плана. Если урока нет в плане, требуемые часы = 0.
            # Это ключевое исправление: мы явно запрещаем назначать уроки, которых нет в плане.
            required_hours = data.subgroup_plan_hours.get((c, s, g), 0)
            model += pulp.lpSum(z[(c, s, g, d, p)] for d in D for p in P) == required_hours, f"Subgroup_Plan_{c}_{s}_{g}"


    # Жесткие запреты на слоты для классов
    for c, d, p in data.forbidden_slots:
        if c in C and d in D and p in P:
            model += y[(c, d, p)] == 0, f"Forbidden_Slot_{c}_{d}_{p}"

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

    for c, s, d in itertools.product(C, S, D):
        if s not in splitS and (c, s) in data.plan_hours:
            model += pulp.lpSum(x[(c, s, d, p)] for p in P) <= 2

    for c, s, g, d in itertools.product(C, S, G, D):
        if s in splitS and (c, s, g) in data.subgroup_plan_hours:
            model += pulp.lpSum(z[(c, s, g, d, p)] for p in P) <= 2

    # --- Ограничения для учителей ---
    # Сначала создадим удобную структуру {учитель -> список его уроков}
    by_teacher = {t: [] for t in data.teachers}
    # Назначения для целых классов
    for (c, s), t in data.assigned_teacher.items():
        if s not in splitS:
            by_teacher[t].append(('x', c, s))
    # Назначения для подгрупп
    if hasattr(data, 'subgroup_assigned_teacher'):
        for (c, s, g), t in data.subgroup_assigned_teacher.items():
            by_teacher[t].append(('z', c, s, g))

    # Теперь проходим по каждому учителю и слоту
    for t, assignments in by_teacher.items():
        # Ограничение на недельную нагрузку (если задано)
        if hasattr(data, 'teacher_weekly_cap') and data.teacher_weekly_cap > 0:
            weekly_lessons = []
            for assign in assignments:
                if assign[0] == 'x':
                    _, c, s = assign
                    weekly_lessons.extend(x[(c, s, d, p)] for d in D for p in P)
                else:
                    _, c, s, g = assign
                    weekly_lessons.extend(z[(c, s, g, d, p)] for d in D for p in P)
            if weekly_lessons:
                model += pulp.lpSum(weekly_lessons) <= data.teacher_weekly_cap, f"Teacher_Weekly_Cap_{t}"

        for d, p in itertools.product(D, P):
            lessons_in_slot = []
            for assign in assignments:
                if assign[0] == 'x':
                    _, c, s = assign
                    lessons_in_slot.append(x[(c, s, d, p)])
                else:  # 'z'
                    _, c, s, g = assign
                    lessons_in_slot.append(z[(c, s, g, d, p)])

            # Ограничение 1: Не более 1 урока в слот
            if lessons_in_slot:
                model += pulp.lpSum(lessons_in_slot) <= 1, f"Teacher_Slot_Clash_{t}_{d}_{p}"

            # Ограничение 2: Учет дней отдыха
            if d in data.days_off.get(t, set()) and lessons_in_slot:
                model += pulp.lpSum(lessons_in_slot) == 0, f"Teacher_Day_Off_{t}_{d}_{p}"

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

    # --- Логика для "анти-окон" (подсчет начала блоков занятий) ---
    for c, d in itertools.product(C, D):
        # Для первого урока дня, начало блока - это просто наличие урока.
        # Если y(p0)=1, то srun(p0)=1. Если y(p0)=0, то srun(p0)=0.
        p0 = P[0]
        model += srun[(c, d, p0)] == y[(c, d, p0)], f"SRun_First_Period_{c}_{d}"

        # Для остальных уроков, начало блока - это когда урок есть, а на предыдущем не было.
        for prev_p, p in zip(P, P[1:]):
            # srun >= y(p) - y(p-1)
            # Это неравенство заставляет srun стать 1, если y(p)=1 и y(prev_p)=0.
            model += srun[(c, d, p)] >= y[(c, d, p)] - y[(c, d, prev_p)], f"SRun_Lower_Bound_{c}_{d}_{p}"
            # srun <= y(p)
            # Это неравенство не дает srun стать 1, если в текущем слоте урока нет (y(p)=0).
            # Если же y(p)=1 и y(prev_p)=1, то srun >= 0. Минимизация в целевой функции сделает srun=0.
            model += srun[(c, d, p)] <= y[(c, d, p)], f"SRun_Upper_Bound_{c}_{d}_{p}"

    # --- Логика для балансировки нагрузки по дням ---
    for c, d in itertools.product(C, D):
        # Суммарное число уроков у класса в день
        model += yday[(c, d)] == pulp.lpSum(y[(c, d, p)] for p in P), f"YDay_Def_{c}_{d}"

    for c in C:
        # Среднее число уроков в день для класса.
        # PuLP и решатели корректно работают с такими линейными выражениями.
        total_lessons_for_class = pulp.lpSum(y[(c, d, p)] for d in D for p in P)
        avg_lessons = total_lessons_for_class / len(D)
        for d in D:
            # Отклонение от среднего (L1-норма). Выражение y_day - avg = dev_pos - dev_neg
            model += yday[(c, d)] - avg_lessons == dev_pos[(c, d)] - dev_neg[(c, d)], f"Dev_Def_{c}_{d}"

    # ------------------------------
    # Целевая функция (составная)
    # ------------------------------
    # 1) Анти-окна: минимизировать число пустых окон у классов между уроками
    obj_runs = pulp.lpSum(srun[(c, d, p)] for c, d, p in itertools.product(C, D, P))

    # 2) Ранние слоты: легкое предпочтение ранних уроков
    obj_early = pulp.lpSum(p * y[(c, d, p)] for c, d, p in itertools.product(C, D, P))

    # 3) Баланс по дням (L1-норма отклонений) - более менее равномерное распределение уроков по дням
    obj_balance = pulp.lpSum(dev_pos[(c, d)] + dev_neg[(c, d)] for c, d in itertools.product(C, D))

    # 4) «Хвосты» после 6-го урока (штраф за поздние слоты) если есть возможность то не назначать уроки после 6 урока
    obj_tail = pulp.lpSum(y[(c, d, p)] for c, d, p in itertools.product(C, D, P) if p > last_ok_period)

    # 5) Пользовательские предпочтения
    #    a) по слотам класса (class_slot_weight)
    #       Штраф или бонус за назначение урока классу 'c' в конкретный день 'd' и период 'p'.
    obj_pref_class_slot = pulp.lpSum(
        y[(c, d, p)] * w
        for (c, d, p), w in data.class_slot_weight.items()
        if c in C and d in D and p in P
    )

    #    b) по слотам учителя (teacher_slot_weight)
    #       Штраф или бонус за назначение урока учителю 't' в конкретный день 'd' и период 'p'.
    teacher_slot_lessons = []
    for (t, d, p), w in data.teacher_slot_weight.items():
        if t in by_teacher and d in D and p in P:
            for assign in by_teacher[t]:
                if assign[0] == 'x':
                    _, c, s = assign
                    teacher_slot_lessons.append(x[(c, s, d, p)] * w)
                else:  # 'z'
                    _, c, s, g = assign
                    teacher_slot_lessons.append(z[(c, s, g, d, p)] * w)
    obj_pref_teacher_slot = pulp.lpSum(teacher_slot_lessons)

    #    c) по дню для конкретного предмета у класса (class_subject_day_weight)
    class_subj_day_lessons = []
    for (c, s, d), w in data.class_subject_day_weight.items():
        if c in C and s in S and d in D:
            if s not in splitS:
                # Суммируем все часы этого предмета в этот день и умножаем на вес
                total_hours_on_day = pulp.lpSum(x[(c, s, d, p)] for p in P)
                class_subj_day_lessons.append(total_hours_on_day * w)
            else:
                # Для делящихся предметов суммируем слоты, в которые они преподаются,
                # чтобы избежать двойного штрафа за параллельные подгруппы.
                total_slots_on_day = pulp.lpSum(is_subj_taught[(c, s, d, p)] for p in P)
                class_subj_day_lessons.append(total_slots_on_day * w)
    obj_pref_class_subj_day = pulp.lpSum(class_subj_day_lessons)


    model += (alpha_runs * obj_runs +
              beta_early * obj_early +
              gamma_balance * obj_balance +
              delta_tail * obj_tail +
              pref_scale * (obj_pref_class_slot + obj_pref_teacher_slot + obj_pref_class_subj_day)
              ), "CompositeObjective"

    # ------------------------------
    # Решение CBC
    # ------------------------------
    # Просто сохраняем LP-файл. Так как используются только английские символы,
    # проблем с кодировкой быть не должно.
    model.writeLP(lp_path) 
    if log:
        print(f"LP-модель сохранена в: {lp_path}")

    # Используем решатель HiGHS через его API 'highspy',
    # так как pulp.pulpTestAll() показал, что 'HiGHS' доступен,
    # в отличие от 'HiGHS_CMD' или 'OR_TOOLS'.
    solver = pulp.HiGHS(msg=log, gapRel=0.05)
    model.solve(solver)

    if log:
        print("Статус решения:", pulp.LpStatus[model.status])

    if model.status == pulp.LpStatusOptimal:
        # --- Вывод результатов ---
        # Так как PuLP сам получил решение от HiGHS, переменные уже заполнены.
        print_by_classes(data, x, z)
        # print_by_teachers(data, x, z)
        # summary_load(data, x, z)
        
        output_filename = "timetable_solution.xlsx"
        export_full_schedule_to_excel(output_filename, data, x, z)

        # Добавляем листы с сырыми данными в тот же файл, если источник - БД
        if db_path: # Теперь проверка стала проще и надежнее
            export_raw_data_to_excel(output_filename, db_path)
    return model, x, y, z


# ------------------------------
# Пример запуска
# ------------------------------
if __name__ == "__main__":
    # --- ВЫБЕРИТЕ ИСТОЧНИК ДАННЫХ ---
    # 'db'        - загрузка "вживую" из базы данных MS Access
    # 'manual'    - использование данных из файла rasp_data.py (ручные, для тестов)
    # 'generated' - использование данных из файла rasp_data_generated.py (снимок базы)
    data_source = 'generated'  # <--- ИЗМЕНИТЕ ЗДЕСЬ

    data = None
    db_path = None # Инициализируем переменную
    if data_source == 'db':
        print("--- Источник данных: MS Access DB ---")
        db_path = r"F:/_prg/python/OR-Tools-MILP/src/db/rasp3.accdb"
        data = load_data_from_access(db_path)
    elif data_source == 'generated':
        print("--- Источник данных: сгенерированный файл (rasp_data_generated.py) ---")
        db_path = r"F:/_prg/python/OR-Tools-MILP/src/db/rasp3-new-calculation.accdb"
        data = create_generated_data()
    elif data_source == 'manual':
        print("--- Источник данных: ручной файл (rasp_data.py) ---")
        data = create_manual_data()

    if data is None:
        print(f"Ошибка: не удалось загрузить данные из источника '{data_source}'. Проверьте настройки.")
        exit()

    build_and_solve_timetable(
        data,
        lp_path="schedule.lp",
        db_path=db_path, # Явно передаем db_path в функцию
        log=True,
    )
