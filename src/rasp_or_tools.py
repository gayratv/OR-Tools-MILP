# rasp_or_tools.py — OR-Tools CP-SAT: составление школьного расписания
# ВЕРСИЯ: улучшенная (включает оптимизацию has_split, inside-подсчёт окон, усиление pairing и набор опций)
# -----------------------------------------------------------------------------
# Структура модуля:
#   1) Импорты и вспомогательные хелперы
#   2) Подсчёт окон преподавателей из готового решения (для отчёта)
#   3) Основная функция build_and_solve_with_or_tools(...)
#      3.1) Переменные модели
#      3.2) Жёсткие ограничения
#      3.3) Доп. опции (по требованию)
#      3.4) Целевая функция: как «взвешенная сумма» либо «лексикографика в 2 фазы»
#      3.5) Решение, сбор статистики, экспорт в Excel
# -----------------------------------------------------------------------------
# ОСНОВНЫЕ УЛУЧШЕНИЯ:
#  - Связь y<->уроки через AddMaxEquality (булев OR)
#  - has_split: замена квадратичного запрета (неделимый vs делимый) на одну булевую переменную-OR
#  - «Окна» как длина «конверта»: prefix/suffix/inside для учителей и (опционально) классов
#  - Линейная эквивалентность для «спаренных» (is_lonely = curr ∧ ¬prev ∧ ¬next)
#  - Набор опций: синхронные сплиты
#  - Опциональная лексикографическая оптимизация (2 solve-а)
# -----------------------------------------------------------------------------

import itertools
from typing import Dict, Iterable, Hashable, Tuple, List, Optional, Union

from ortools.sat.python import cp_model

# Ваша инфраструктура данных/вывода
from input_data import InputData, OptimizationWeights
from rasp_data import create_manual_data
from access_loader import load_data_from_access, load_display_maps
from rasp_data_generated import create_timetable_data
from print_schedule import get_solution_maps, export_full_schedule_to_excel


# ---------------------------- 1) ВСПОМОГАТЕЛЬНЫЕ ХЕЛПЕРЫ ----------------------------

def _as_int(x: Union[int, float]) -> int:
    """Безопасное приведение веса к int. CP-SAT принимает только целочисленные коэффициенты."""
    try:
        return int(x)
    except Exception:
        # На всякий случай «грубая» дискретизация, если прилетело float
        return int(round(float(x)))


def _get_weight(weights: OptimizationWeights, name: str, default: int = 0) -> int:
    """Достаём coefficient из OptimizationWeights; по умолчанию 0 (отключено)."""
    return _as_int(getattr(weights, name, default))


# ----------- 2) ПОДСЧЁТ ОКОН У ПРЕПОДАВАТЕЛЕЙ ИЗ ГОТОВОГО РЕШЕНИЯ (для отчёта) -----------

def _calculate_teacher_windows(data: InputData,
                               solver: cp_model.CpSolver,
                               x: dict,
                               z: dict) -> int:
    """
    Подсчитывает суммарную длину «окон» (пустых слотов между первым и последним уроком)
    у всех учителей за все дни — по готовому решению.

    Это соответствует сумме (inside - busy) по каждому дню: считаем явно по занятым периодам.
    """
    teacher_busy_periods = {(t, d): [] for t, d in itertools.product(data.teachers, data.days)}

    # Не-делимые предметы
    for (c, s, d, p), var in x.items():
        if solver.Value(var) > 0:
            teacher = data.assigned_teacher.get((c, s))
            if teacher:
                teacher_busy_periods[teacher, d].append(p)

    # Делимые предметы
    for (c, s, g, d, p), var in z.items():
        if solver.Value(var) > 0:
            teacher = data.subgroup_assigned_teacher.get((c, s, g))
            if teacher:
                teacher_busy_periods[teacher, d].append(p)

    total_windows = 0
    for t, d in itertools.product(data.teachers, data.days):
        busy = sorted(set(teacher_busy_periods[t, d]))
        if len(busy) >= 2:
            first, last = busy[0], busy[-1]
            inside_len = (last - first + 1)  # длина «конверта»
            total_windows += inside_len - len(busy)  # окна = всё внутри минус занято
    return total_windows


# ---------------------- 3) ОСНОВНАЯ ФУНКЦИЯ ПОСТРОЕНИЯ/РЕШЕНИЯ ----------------------

def build_and_solve_with_or_tools(
    data: InputData,
    log: bool = True,
    PRINT_TIMETABLE_TO_CONSOLE: Optional[bool] = None,
    display_maps: Optional[Dict[str, Dict[str, str]]] = None,

) -> None:
    """
    Строит CP-SAT модель расписания и решает её.
    Модель учитывает делимые/неделимые предметы, занятость преподавателей/классов,
    совместимость сплитов, дневные/недельные планы, а также мягкие цели.

    Важные флаги/опции читаются из OptimizationWeights и полей InputData,
    но все опциональны — код корректно работает, если они отсутствуют.
    """

    model = cp_model.CpModel()
    C, S, D, P = data.classes, data.subjects, data.days, data.periods
    G, splitS = data.subgroup_ids, data.split_subjects
    weights = OptimizationWeights()

    # -------------------------- 3.1) ПЕРЕМЕННЫЕ МОДЕЛИ --------------------------

    # x[c,s,d,p] — неделимый предмет
    x = {(c, s, d, p): model.NewBoolVar(f'x_{c}_{s}_{d}_{p}')
         for c, s, d, p in itertools.product(C, S, D, P) if s not in splitS}

    # z[c,s,g,d,p] — делимый предмет по подгруппе g
    z = {(c, s, g, d, p): model.NewBoolVar(f'z_{c}_{s}_{g}_{d}_{p}')
         for c, s, g, d, p in itertools.product(C, S, G, D, P) if s in splitS}

    # y[c,d,p] — в слоте у класса есть ЛЮБОЙ урок
    y = {(c, d, p): model.NewBoolVar(f'y_{c}_{d}_{p}')
         for c, d, p in itertools.product(C, D, P)}

    # is_subj_taught[c,s,d,p] — флаг, что сплит‑предмет s преподаётся (какой‑то подгруппе) в слоте
    is_subj_taught = {(c, s, d, p): model.NewBoolVar(f'ist_{c}_{s}_{d}_{p}')
                      for c, s, d, p in itertools.product(C, splitS, D, P)}

    # has_split[c,d,p] — в слоте есть ХОТЯ БЫ ОДИН сплит‑урок (любой предмет, любая подгруппа)
    has_split = {(c, d, p): model.NewBoolVar(f'has_split_{c}_{d}_{p}')
                 for c, d, p in itertools.product(C, D, P)}

    # Общая «ложная» булева (удобно для .get(..., false_var))
    false_var = model.NewBoolVar('false_var')
    model.Add(false_var == 0)

    # Предварительно соберём «уроки класса в слоте» для удобного OR
    def _class_lessons_in_slot(c, d, p) -> List[cp_model.IntVar]:
        non_split = [x[(c, s, d, p)] for s in S if s not in splitS if (c, s, d, p) in x]
        split = [z[(c, s, g, d, p)] for s in splitS for g in G if (c, s, g, d, p) in z]
        return non_split + split

    # teacher_lessons_in_slot[(t,d,p)] — список булевых уроков данного учителя в слоте
    teacher_lessons_in_slot: Dict[Tuple[Hashable, Hashable, Hashable], List[cp_model.IntVar]] = {
        (t, d, p): [] for t, d, p in itertools.product(data.teachers, D, P)
    }
    for (c, s), t in data.assigned_teacher.items():
        if s not in splitS:
            for d, p in itertools.product(D, P):
                teacher_lessons_in_slot[t, d, p].append(x[c, s, d, p])
    for (c, s, g), t in data.subgroup_assigned_teacher.items():
        for d, p in itertools.product(D, P):
            teacher_lessons_in_slot[t, d, p].append(z[c, s, g, d, p])

    # teacher_busy[t,d,p] — у учителя есть хотя бы 1 урок в слоте
    teacher_busy = {(t, d, p): model.NewBoolVar(f'tbusy_{t}_{d}_{p}')
                    for t, d, p in itertools.product(data.teachers, D, P)}
    for t, d, p in itertools.product(data.teachers, D, P):
        lessons = teacher_lessons_in_slot.get((t, d, p), [])
        if lessons:
            # teacher_busy == OR(lessons)
            model.AddMaxEquality(teacher_busy[t, d, p], lessons)
        else:
            model.Add(teacher_busy[t, d, p] == 0)

    # --------------------------- 3.2) ЖЁСТКИЕ ОГРАНИЧЕНИЯ ---------------------------

    # (1) Связь y с уроками: y == OR(x, z) в слоте
    for c, d, p in itertools.product(C, D, P):
        lessons = _class_lessons_in_slot(c, d, p)
        if lessons:
            model.AddMaxEquality(y[c, d, p], lessons)
        else:
            model.Add(y[c, d, p] == 0)

    # (2) Выполнение недельных планов (для неделимых и делимых)
    for (c, s), h in data.plan_hours.items():
        model.Add(sum(x[c, s, d, p] for d in D for p in P) == h)
    for (c, s, g), h in data.subgroup_plan_hours.items():
        model.Add(sum(z[c, s, g, d, p] for d in D for p in P) == h)

    # (3) Ограничения для учителей
    for t in data.teachers:
        # (3a) Не более одного урока в слоте
        for d, p in itertools.product(D, P):
            lessons = teacher_lessons_in_slot[t, d, p]
            if lessons:
                model.AddAtMostOne(list(lessons))  # список, не генератор

            # (3b) Индивидуальные выходные/недоступные дни
            if d in getattr(data, 'days_off', {}).get(t, set()):
                for v in lessons:
                    model.Add(v == 0)

            # (3c) Явно запрещённые слоты учителя (если есть)
            for (td, tp) in getattr(data, 'teacher_forbidden_slots', {}).get(t, []):
                if td == d and tp == p:
                    for v in lessons:
                        model.Add(v == 0)

    # (4) Ограничения внутри класса/слота
    for c, d, p in itertools.product(C, D, P):
        # (4a) Не более одного НЕДЕЛИМОГО предмета
        non_split_vars = [x[(c, s, d, p)] for s in S if s not in splitS if (c, s, d, p) in x]
        if non_split_vars:
            model.AddAtMostOne(list(non_split_vars))

        # (4b) По каждой подгруппе — не более одного СПЛИТ‑урока в слоте
        for g in G:
            split_by_group = [z[(c, s, g, d, p)] for s in splitS if (c, s, g, d, p) in z]
            if split_by_group:
                model.AddAtMostOne(list(split_by_group))

        # (4c) Неделимый и какой‑либо сплит одновременно — запрещено.
        # Вводим has_split[c,d,p] = OR всех z в слоте и «конкурируем» его с неделимыми:
        all_split_vars_in_slot = [z[(c, s, g, d, p)] for s in splitS for g in G if (c, s, g, d, p) in z]
        if all_split_vars_in_slot:
            model.AddMaxEquality(has_split[c, d, p], all_split_vars_in_slot)
        else:
            model.Add(has_split[c, d, p] == 0)

        # либо один неделимый, либо «какие‑то» сплиты (с учётом 4b и совместимости ниже)
        if non_split_vars:
            model.AddAtMostOne(list(non_split_vars) + [has_split[c, d, p]])
        else:
            # Если неделимых нет, ограничение сводится к «has_split ≤ 1», но это уже булева.
            pass

    # (5) Совместимость сплитов: is_subj_taught[c,s,d,p] == OR_g z[c,s,g,d,p]
    for c, s, d, p in itertools.product(C, splitS, D, P):
        subgroup_vars = [z[(c, s, g, d, p)] for g in G if (c, s, g, d, p) in z]
        if subgroup_vars:
            model.AddMaxEquality(is_subj_taught[c, s, d, p], subgroup_vars)
        else:
            model.Add(is_subj_taught[c, s, d, p] == 0)

    # Несовместимые пары сплит‑предметов: не могут идти одновременно у класса
    split_list = sorted(list(splitS))
    for c, d, p in itertools.product(C, D, P):
        for s1, s2 in itertools.combinations(split_list, 2):
            pair = tuple(sorted((s1, s2)))
            if pair not in getattr(data, 'compatible_pairs', set()):
                model.AddBoolOr([
                    is_subj_taught[c, s1, d, p].Not(),
                    is_subj_taught[c, s2, d, p].Not(),
                ])

    # ------------------------- 3.3) ДОПОЛНИТЕЛЬНЫЕ ОПЦИИ (НЕОБЯЗ.) -------------------------

    # (A) Синхронность подгрупп для некоторых сплит‑предметов
    must_sync = set(getattr(data, 'must_sync_split_subjects', [])) & set(splitS)
    if must_sync:
        for s in must_sync:
            for c, d, p in itertools.product(C, D, P):
                # Все z для разных g в этом слоте должны быть равны (0/1 одновременно)
                for g1, g2 in itertools.combinations(G, 2):
                    if (c, s, g1, d, p) in z and (c, s, g2, d, p) in z:
                        model.Add(z[c, s, g1, d, p] == z[c, s, g2, d, p])

    # ------------------------- 3.4) ЦЕЛЕВАЯ ФУНКЦИЯ / МЯГКИЕ ЦЕЛИ -------------------------

    # (A) «Окна» у классов и учителей через префикс/суффикс/inside
    #
    # Идея метода: для каждой комбинации "класс–день" и "учитель–день"
    # построим оболочку, охватывающую все занятые уроки. Длина этой
    # оболочки (от первого до последнего урока включительно) равна
    # сумме переменных inside. Минимизируя её, мы сокращаем количество
    # пустых слотов внутри дня, то есть «окон».

    # --- Классы -------------------------------------------------------
    # prefix_class[c,d,p]  — хотя бы один урок у класса c в день d в слотах
    #                         до и включая период p.
    # suffix_class[c,d,p]  — хотя бы один урок у класса c в день d в слотах
    #                         начиная с p и далее.
    # inside_class[c,d,p]  — слот находится между первым и последним
    #                         уроком (внутри оболочки). Все значения 1
    #                         образуют «конверт», который далее
    #                         минимизируется.
    prefix_class: Dict[Tuple[Hashable, Hashable, Hashable], cp_model.IntVar] = {}
    suffix_class: Dict[Tuple[Hashable, Hashable, Hashable], cp_model.IntVar] = {}
    inside_class: Dict[Tuple[Hashable, Hashable, Hashable], cp_model.IntVar] = {}

    for c, d in itertools.product(C, D):
        # prefix: накапливаем OR слева направо, чтобы определить, был ли
        # хотя бы один урок до текущего периода включительно.
        for idx, p in enumerate(P):
            v = model.NewBoolVar(f'pref_c_{c}_{d}_{p}')
            prefix_class[c, d, p] = v
            if idx == 0:
                model.Add(v == y[c, d, p])  # первая позиция совпадает с y
            else:
                # v = prefix_class[p-1] OR y[p]
                model.AddMaxEquality(v, [prefix_class[c, d, P[idx - 1]], y[c, d, p]])
        # suffix: аналогичная логика, но идём справа налево, чтобы знать,
        # есть ли уроки после текущего периода.
        for idx in reversed(range(len(P))):
            p = P[idx]
            v = model.NewBoolVar(f'suff_c_{c}_{d}_{p}')
            suffix_class[c, d, p] = v
            if idx == len(P) - 1:
                model.Add(v == y[c, d, p])  # последняя позиция совпадает с y
            else:
                # v = suffix_class[p+1] OR y[p]
                model.AddMaxEquality(v, [suffix_class[c, d, P[idx + 1]], y[c, d, p]])

    for c, d, p in itertools.product(C, D, P):
        # inside = prefix AND suffix, т.е. единица только для слотов
        # между первым и последним уроком (включая их).
        u = model.NewBoolVar(f'inside_c_{c}_{d}_{p}')
        inside_class[c, d, p] = u
        model.Add(u <= prefix_class[c, d, p])
        model.Add(u <= suffix_class[c, d, p])
        model.Add(u >= prefix_class[c, d, p] + suffix_class[c, d, p] - 1)

    # Сумма inside_class — это длина оболочки для всех классов.
    # Минимизируя её, непрямо наказываем за «окна» внутри дня.
    sum_inside_class = sum(inside_class.values())

    # --- Учителя -----------------------------------------------------
    # Аналогичные переменные для каждого учителя. Здесь вместо y мы
    # используем подготовленный флаг teacher_busy[t,d,p].
    prefix_teacher: Dict[Tuple[Hashable, Hashable, Hashable], cp_model.IntVar] = {}
    suffix_teacher: Dict[Tuple[Hashable, Hashable, Hashable], cp_model.IntVar] = {}
    inside_teacher: Dict[Tuple[Hashable, Hashable, Hashable], cp_model.IntVar] = {}

    for t, d in itertools.product(data.teachers, D):
        # prefix: «есть ли уже урок у учителя до текущего периода?»
        for idx, p in enumerate(P):
            v = model.NewBoolVar(f'pref_t_{t}_{d}_{p}')
            prefix_teacher[t, d, p] = v
            if idx == 0:
                model.Add(v == teacher_busy[t, d, p])
            else:
                model.AddMaxEquality(v, [prefix_teacher[t, d, P[idx - 1]], teacher_busy[t, d, p]])
        # suffix: «будет ли ещё урок после текущего периода?»
        for idx in reversed(range(len(P))):
            p = P[idx]
            v = model.NewBoolVar(f'suff_t_{t}_{d}_{p}')
            suffix_teacher[t, d, p] = v
            if idx == len(P) - 1:
                model.Add(v == teacher_busy[t, d, p])
            else:
                model.AddMaxEquality(v, [suffix_teacher[t, d, P[idx + 1]], teacher_busy[t, d, p]])

    for t, d, p in itertools.product(data.teachers, D, P):
        # Слот внутри оболочки преподавателя, если до него и после него
        # есть занятие (или он сам занят).
        u = model.NewBoolVar(f'inside_t_{t}_{d}_{p}')
        inside_teacher[t, d, p] = u
        model.Add(u <= prefix_teacher[t, d, p])
        model.Add(u <= suffix_teacher[t, d, p])
        model.Add(u >= prefix_teacher[t, d, p] + suffix_teacher[t, d, p] - 1)

    # Ключевая метрика «окон» преподавателей: чем меньше оболочка,
    # тем более компактно распределены уроки в течение дня.
    sum_inside_teacher = sum(inside_teacher.values())

    # (B) Предпочтение ранних слотов (минимизируем номер периода)
    beta_early = _get_weight(weights, 'beta_early', 0)
    early_term = beta_early * sum(p * y[c, d, p] for c, d, p in y)

    # (C) Баланс по дням: минимизировать разброс нагрузки в днях
    gamma_balance = _get_weight(weights, 'gamma_balance', 0)
    balance_terms = []
    if gamma_balance:
        for c in C:
            lessons_per_day = [sum(y[c, d, p] for p in P) for d in D]
            min_lessons = model.NewIntVar(0, len(P), f'minl_{c}')
            max_lessons = model.NewIntVar(0, len(P), f'maxl_{c}')
            model.AddMinEquality(min_lessons, lessons_per_day)
            model.AddMaxEquality(max_lessons, lessons_per_day)
            balance_terms.append(max_lessons - min_lessons)
    balance_term = gamma_balance * sum(balance_terms) if balance_terms else 0

    # (D) «Хвосты»: штраф за уроки после last_ok_period
    last_ok = getattr(weights, 'last_ok_period', max(P) if P else 0)
    delta_tail = _get_weight(weights, 'delta_tail', 0)
    tail_term = delta_tail * sum(y[c, d, p] for c, d, p in y if p > last_ok)

    # (E) «Спаренные» уроки: штраф за одиночные (линейная эквивалентность)
    epsilon_pairing = _get_weight(weights, 'epsilon_pairing', 0)
    lonely_vars: List[cp_model.IntVar] = []

    if epsilon_pairing and getattr(data, 'paired_subjects', None):
        for s in data.paired_subjects:
            if s in splitS:
                # Для каждого класса/подгруппы/дня, проверяем «соседей» по периоду
                for c, g, d in itertools.product(C, G, D):
                    for idx, p in enumerate(P):
                        curr = z.get((c, s, g, d, p), false_var)
                        prev_ = z.get((c, s, g, d, P[idx - 1]), false_var) if idx > 0 else false_var
                        next_ = z.get((c, s, g, d, P[idx + 1]), false_var) if idx < len(P) - 1 else false_var
                        u = model.NewBoolVar(f'lonely_{c}_{s}_{g}_{d}_{p}')
                        # u = curr ∧ ¬prev ∧ ¬next
                        model.Add(u <= curr)
                        model.Add(u <= 1 - prev_)
                        model.Add(u <= 1 - next_)
                        model.Add(u >= curr - prev_ - next_)
                        lonely_vars.append(u)
            else:
                for c, d in itertools.product(C, D):
                    for idx, p in enumerate(P):
                        curr = x.get((c, s, d, p), false_var)
                        prev_ = x.get((c, s, d, P[idx - 1]), false_var) if idx > 0 else false_var
                        next_ = x.get((c, s, d, P[idx + 1]), false_var) if idx < len(P) - 1 else false_var
                        u = model.NewBoolVar(f'lonely_{c}_{s}_{d}_{p}')
                        model.Add(u <= curr)
                        model.Add(u <= 1 - prev_)
                        model.Add(u <= 1 - next_)
                        model.Add(u >= curr - prev_ - next_)
                        lonely_vars.append(u)
    pairing_term = epsilon_pairing * sum(lonely_vars) if lonely_vars else 0

    # (F) Основные «окна/конверты» как цели
    alpha_runs = _get_weight(weights, 'alpha_runs', 0)  # для классов
    alpha_runs_teacher = _get_weight(weights, 'alpha_runs_teacher', 0)  # для учителей

    # Для лексикографики удобно иметь чистые выражения без весов:
    primary_expr = sum_inside_teacher  # по умолчанию: основная цель — окна учителей
    secondary_expr = (
        alpha_runs * sum_inside_class +
        early_term +
        balance_term +
        tail_term +
        pairing_term
    )

    use_lexico = bool(getattr(weights, 'use_lexico', False))
    lexico_primary = getattr(weights, 'lexico_primary', 'teacher_windows')  # 'teacher_windows' | 'class_windows'

    if lexico_primary == 'class_windows':
        primary_expr, secondary_expr = sum_inside_class, (
            alpha_runs_teacher * sum_inside_teacher +
            early_term + balance_term + tail_term + pairing_term
        )

    # Если лексикографика выключена — минимизируем взвешенную сумму
    if not use_lexico:
        objective = (
            alpha_runs_teacher * sum_inside_teacher +
            alpha_runs * sum_inside_class +
            early_term + balance_term + tail_term + pairing_term
        )
        model.Minimize(objective)

    # --------------------------- 3.5) ЗАПУСК РЕШАТЕЛЯ ---------------------------

    solver = cp_model.CpSolver()
    solver.parameters.log_search_progress = log
    solver.parameters.num_search_workers = getattr(weights, 'num_search_workers', 20)
    # Опциональные параметры для воспроизводимости/тайм‑лимита
    if getattr(weights, 'random_seed', None) is not None:
        solver.parameters.random_seed = int(weights.random_seed)
    if getattr(weights, 'time_limit_s', None):
        solver.parameters.max_time_in_seconds = float(weights.time_limit_s)
    # Чуть отпускаем разрыв по умолчанию — ускоряет черновики
    solver.parameters.relative_gap_limit = getattr(weights, 'relative_gap_limit', 0.05)

    print("Начинаем решение...")

    if use_lexico:
        # Фаза A: минимизируем primary_expr
        model.Minimize(primary_expr)
        status_A = solver.Solve(model)
        print("Фаза A (лексикографика): завершена.")
        if status_A not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            print(f'Решение не найдено (фаза A). Статус: {solver.StatusName(status_A)}')
            return

        primary_value = int(round(solver.ObjectiveValue()))
        print(f'Оптимум фазы A (primary) = {primary_value}')

        # Фиксируем ограничение «primary ≤ найденный уровень»
        model.Add(primary_expr <= primary_value)

        # Фаза B: минимизируем secondary_expr
        model.Minimize(secondary_expr)
        status = solver.Solve(model)
        print("Фаза B (лексикографика): завершена.")
    else:
        status = solver.Solve(model)

    print("\nРешение завершено.")

    # ---------------------- 3.6) СБОР СТАТИСТИКИ И ЭКСПОРТ ----------------------

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        # Сводка
        solution_stats = {
            "status": solver.StatusName(status),
            "objective_value": solver.ObjectiveValue(),
            "wall_time_s": solver.WallTime(),
            "total_lonely_lessons": -1,
            "total_teacher_windows": -1
        }

        if lonely_vars:
            solution_stats["total_lonely_lessons"] = int(sum(solver.Value(v) for v in lonely_vars))

        # Подсчёт окон преподавателей по готовому расписанию (для отчёта/Excel)
        total_teacher_windows = _calculate_teacher_windows(data, solver, x, z)
        solution_stats["total_teacher_windows"] = int(total_teacher_windows)

        # Печать краткой сводки
        print(f'Финальный статус: {solution_stats["status"]}')
        print(f'Целевая функция: {solution_stats["objective_value"]}')
        print(f'Время решения: {solution_stats["wall_time_s"]:.2f}s')
        if solution_stats["total_lonely_lessons"] != -1:
            print(f'Одинокие уроки (штраф): {solution_stats["total_lonely_lessons"]}')
        print(f'Окна у преподавателей (суммарная длина): {solution_stats["total_teacher_windows"]}')

        # Экспорт в Excel
        output_filename = "timetable_or_tools_solution.xlsx"
        final_maps = {"solver": solver, "x": x, "z": z}
        solution_maps = get_solution_maps(data, final_maps, is_pulp=False)
        export_full_schedule_to_excel(output_filename, data, solution_maps, display_maps, solution_stats, weights)

    else:
        print(f'Решение не найдено. Статус: {solver.StatusName(status)}')


# ------------------------------ 4) ТОЧКА ВХОДА ------------------------------

if __name__ == '__main__':
    # Источник данных: 'db' | 'generated' | 'manual'
    data_source = 'manual'
    data = None

    # Путь к вашей MS Access БД (используется при data_source == 'db')
    db_path_str = r"F:/_prg/python/OR-Tools-MILP/src/db/rasp3-new-calculation.accdb"

    if data_source == 'db':
        print("--- Источник данных: MS Access DB ---")
        data = load_data_from_access(db_path_str)
    elif data_source == 'generated':
        print("--- Источник данных: сгенерированный файл (rasp_data_generated.py) ---")
        data = create_timetable_data()
    elif data_source == 'manual':
        print("--- Источник данных: ручной файл (rasp_data.py) ---")
        data = create_manual_data()

    if data is None:
        print(f"Ошибка: не удалось загрузить данные из источника '{data_source}'. Проверьте настройки.")
        raise SystemExit(1)

    # Карты для красивого отображения в Excel (если есть)
    display_maps = load_display_maps(db_path_str)

    # Запуск
    build_and_solve_with_or_tools(
        data,
        PRINT_TIMETABLE_TO_CONSOLE=False,
        display_maps=display_maps

    )
