# rasp_or_tools.py (cleaned: без teacher_weekly_cap/teacher_daily_cap/class_daily_cap)

import itertools
from typing import Dict

from ortools.sat.python import cp_model

from input_data import InputData, OptimizationWeights

# Источники данных
from rasp_data import create_manual_data
from access_loader import load_data_from_access, load_display_maps
from rasp_data_generated import create_timetable_data

# Вывод и экспорт
from print_schedule import get_solution_maps, export_full_schedule_to_excel


def _calculate_teacher_windows(data: InputData, solver: cp_model.CpSolver, x: dict, z: dict) -> int:
    """
    Подсчитывает общее количество "окон" у учителей на основании найденного решения.
    "Окно" — пустой период между двумя уроками в рамках одного дня.
    """
    teacher_busy_periods = {(t, d): [] for t, d in itertools.product(data.teachers, data.days)}

    # Неделимые предметы
    for (c, s, d, p), var in x.items():
        if solver.Value(var) > 0:
            t = data.assigned_teacher.get((c, s))
            if t:
                teacher_busy_periods[t, d].append(p)

    # Делимые предметы
    for (c, s, g, d, p), var in z.items():
        if solver.Value(var) > 0:
            t = data.subgroup_assigned_teacher.get((c, s, g))
            if t:
                teacher_busy_periods[t, d].append(p)

    total_windows = 0
    for t, d in itertools.product(data.teachers, data.days):
        busy = sorted(set(teacher_busy_periods[t, d]))
        if len(busy) > 1:
            # сумма разрывов между соседними занятиями
            total_windows += sum(busy[i + 1] - busy[i] - 1 for i in range(len(busy) - 1))
    return total_windows


def build_and_solve_with_or_tools(
    data: InputData,
    log: bool = True,
    PRINT_TIMETABLE_TO_CONSOLE=None,
    display_maps: Dict[str, Dict[str, str]] = None,
    optimize_teacher_windows: bool = True
):
    """
    Основная функция: строит и решает CP-SAT модель расписания.
    Внимание: ограничения/поля teacher_weekly_cap, teacher_daily_cap, class_daily_cap — УДАЛЕНЫ.
    """
    model = cp_model.CpModel()
    C, S, D, P = data.classes, data.subjects, data.days, data.periods
    G, splitS = data.subgroup_ids, data.split_subjects
    weights = OptimizationWeights()

    # ---------------- Переменные ----------------
    # Неделимые
    x = {(c, s, d, p): model.NewBoolVar(f'x_{c}_{s}_{d}_{p}')
         for c, s, d, p in itertools.product(C, S, D, P) if s not in splitS}

    # Делимые (по подгруппам)
    z = {(c, s, g, d, p): model.NewBoolVar(f'z_{c}_{s}_{g}_{d}_{p}')
         for c, s, g, d, p in itertools.product(C, S, G, D, P) if s in splitS}

    # Занятость класса в слоте
    y = {(c, d, p): model.NewBoolVar(f'y_{c}_{d}_{p}')
         for c, d, p in itertools.product(C, D, P)}

    # Флаг «сплит-предмет s преподаётся хотя бы одной подгруппе»
    is_subj_taught = {(c, s, d, p): model.NewBoolVar(f'ist_{c}_{s}_{d}_{p}')
                      for c, s, d, p in itertools.product(C, splitS, D, P)}

    false_var = model.NewBoolVar('false_var')
    model.Add(false_var == 0)

    # ---------------- Жёсткие ограничения ----------------

    # 1) Связь y с уроками: y == OR(x, z) в слоте
    for c, d, p in itertools.product(C, D, P):
        lessons = [x.get((c, s, d, p)) for s in S if s not in splitS] + \
                  [z.get((c, s, g, d, p)) for s in splitS for g in G]
        lessons = [v for v in lessons if v is not None]
        model.AddBoolOr(lessons).OnlyEnforceIf(y[c, d, p])
        model.AddBoolAnd([v.Not() for v in lessons]).OnlyEnforceIf(y[c, d, p].Not())

    # 2) Выполнение учебного плана
    for (c, s), h in data.plan_hours.items():
        model.Add(sum(x[c, s, d, p] for d in D for p in P) == h)
    for (c, s, g), h in data.subgroup_plan_hours.items():
        model.Add(sum(z[c, s, g, d, p] for d in D for p in P) == h)

    # 3) Учителя: структура слотов / отсутствие накладок / недоступные дни
    teacher_lessons_in_slot = {(t, d, p): [] for t, d, p in itertools.product(data.teachers, D, P)}
    # неделимые
    for (c, s), t in data.assigned_teacher.items():
        if s in splitS:
            continue
        for d, p in itertools.product(D, P):
            teacher_lessons_in_slot[t, d, p].append(x[c, s, d, p])
    # делимые
    for (c, s, g), t in data.subgroup_assigned_teacher.items():
        for d, p in itertools.product(D, P):
            teacher_lessons_in_slot[t, d, p].append(z[c, s, g, d, p])

    for t in data.teachers:
        # 3b) Не более одного урока в одном слоте
        for d, p in itertools.product(D, P):
            lessons = teacher_lessons_in_slot[t, d, p]
            if lessons:
                model.AddAtMostOne(lessons)
            # 3c) Недоступные дни (days_off)
            if d in data.days_off.get(t, set()):
                for v in lessons:
                    model.Add(v == 0)

    # 4) Ограничения внутри класса
    for c, d, p in itertools.product(C, D, P):
        # 4a) Не более одного неделимого в слоте
        non_split_vars = [x[c, s, d, p] for s in S if s not in splitS]
        if non_split_vars:
            model.AddAtMostOne(non_split_vars)

        # 4b) У каждой подгруппы — не более одного сплит-урока в слоте
        for g in G:
            split_by_g = [z[c, s, g, d, p] for s in splitS]
            if split_by_g:
                model.AddAtMostOne(split_by_g)

        # 4c) Неделимый одновременно со сплитом — запрещено (попарные OR)
        all_split = [z[c, s, g, d, p] for s in splitS for g in G]
        for nsv in non_split_vars:
            for sv in all_split:
                model.AddBoolOr([nsv.Not(), sv.Not()])

    # 5) Совместимость сплитов
    for c, s, d, p in itertools.product(C, splitS, D, P):
        subgroup_lessons = [z[c, s, g, d, p] for g in G]
        model.AddBoolOr(subgroup_lessons).OnlyEnforceIf(is_subj_taught[c, s, d, p])
        model.AddBoolAnd([v.Not() for v in subgroup_lessons]).OnlyEnforceIf(is_subj_taught[c, s, d, p].Not())

    split_list = sorted(list(splitS))
    for c, d, p in itertools.product(C, D, P):
        for s1, s2 in itertools.combinations(split_list, 2):
            pair = tuple(sorted((s1, s2)))
            if pair not in data.compatible_pairs:
                model.AddBoolOr([is_subj_taught[c, s1, d, p].Not(),
                                 is_subj_taught[c, s2, d, p].Not()])

    # --- Политика: максимум повторов предмета в день (по КЛАССУ и ПРЕДМЕТУ) ---
    # Ожидаемый формат:
    # data.max_repeats_per_day = {
    #       "5A": {"math": 1, "eng": 2},
    #       "5B": {"math": 2, "eng": 1, "cs": 2} }
    # Для split-предметов считаем "повтор" по флагу is_subj_taught (идёт ли предмет у ЛЮБОЙ подгруппы в слоте).
    if getattr(data, "max_repeats_per_day", None):
        for c, subj_caps in data.max_repeats_per_day.items():
            if c not in C:
                continue
            for s, cap in subj_caps.items():
                if s not in S:
                    continue
                cap_int = int(cap)
                for d in D:
                    if s in splitS:
                        # суммируем по слотам флаг "этот split-предмет идёт у какой-либо подгруппы"
                        model.Add(sum(is_subj_taught[c, s, d, p] for p in P) <= cap_int)
                    else:
                        # для неделимых — суммируем x по слотам дня
                        model.Add(sum(x[c, s, d, p] for p in P if (c, s, d, p) in x) <= cap_int)


    # ---------------- Целевая функция (мягкие цели) ----------------
    objective_terms = []

    # 1) Анти-окна для классов: через начало блоков (srun)
    srun = {(c, d, p): model.NewBoolVar(f'srun_{c}_{d}_{p}')
            for c, d, p in itertools.product(C, D, P)}
    for c, d in itertools.product(C, D):
        model.Add(srun[c, d, P[0]] == y[c, d, P[0]])
        for p_idx in range(1, len(P)):
            p, prev_p = P[p_idx], P[p_idx - 1]
            sr, yp, yprev = srun[c, d, p], y[c, d, p], y[c, d, prev_p]
            model.Add(sr == 1).OnlyEnforceIf([yp, yprev.Not()])
            model.Add(sr == 0).OnlyEnforceIf(yp.Not())
            model.Add(sr == 0).OnlyEnforceIf(yprev)
    objective_terms.append(weights.alpha_runs * sum(srun.values()))

    # 1.1) Анти-окна для учителей: аналогичная конструкция (tsrun)
    if optimize_teacher_windows:
        teacher_busy = {(t, d, p): model.NewBoolVar(f'tbusy_{t}_{d}_{p}')
                        for t, d, p in itertools.product(data.teachers, D, P)}
        for t, d, p in itertools.product(data.teachers, D, P):
            lessons = teacher_lessons_in_slot.get((t, d, p), [])
            if lessons:
                model.AddBoolOr(lessons).OnlyEnforceIf(teacher_busy[t, d, p])
                model.AddBoolAnd([v.Not() for v in lessons]).OnlyEnforceIf(teacher_busy[t, d, p].Not())
            else:
                model.Add(teacher_busy[t, d, p] == 0)

        tsrun = {(t, d, p): model.NewBoolVar(f'tsrun_{t}_{d}_{p}')
                 for t, d, p in itertools.product(data.teachers, D, P)}
        for t, d in itertools.product(data.teachers, D):
            model.Add(tsrun[t, d, P[0]] == teacher_busy[t, d, P[0]])
            for p_idx in range(1, len(P)):
                p, prev_p = P[p_idx], P[p_idx - 1]
                model.Add(tsrun[t, d, p] == 1).OnlyEnforceIf([teacher_busy[t, d, p],
                                                              teacher_busy[t, d, prev_p].Not()])
                model.Add(tsrun[t, d, p] == 0).OnlyEnforceIf(teacher_busy[t, d, p].Not())
                model.Add(tsrun[t, d, p] == 0).OnlyEnforceIf(teacher_busy[t, d, prev_p])

        objective_terms.append(weights.alpha_runs_teacher * sum(tsrun.values()))

    # 2) Ранние слоты
    objective_terms.append(weights.beta_early * sum(p * y[c, d, p] for c, d, p in y))

    # 3) Баланс по дням
    for c in C:
        lessons_per_day = [sum(y[c, d, p] for p in P) for d in D]
        minl = model.NewIntVar(0, len(P), f'minl_{c}')
        maxl = model.NewIntVar(0, len(P), f'maxl_{c}')
        model.AddMinEquality(minl, lessons_per_day)
        model.AddMaxEquality(maxl, lessons_per_day)
        objective_terms.append(weights.gamma_balance * (maxl - minl))

    # 4) «Хвосты» после разрешённого слота
    objective_terms.append(weights.delta_tail * sum(y[c, d, p] for c, d, p in y if p > weights.last_ok_period))

    # 5) «Спаренные» уроки: штраф за одиночные
    if getattr(data, 'paired_subjects', None):
        lonely = []
        for s in data.paired_subjects:
            if s in splitS:
                for c, g, d in itertools.product(C, G, D):
                    for idx, p in enumerate(P):
                        curr = z.get((c, s, g, d, p), false_var)
                        prev_ = z.get((c, s, g, d, P[idx - 1]), false_var) if idx > 0 else false_var
                        next_ = z.get((c, s, g, d, P[idx + 1]), false_var) if idx < len(P) - 1 else false_var
                        u = model.NewBoolVar(f'lonely_{c}_{s}_{g}_{d}_{p}')
                        model.Add(u == 1).OnlyEnforceIf([curr, prev_.Not(), next_.Not()])
                        model.Add(u == 0).OnlyEnforceIf(curr.Not())
                        model.Add(u == 0).OnlyEnforceIf(prev_)
                        model.Add(u == 0).OnlyEnforceIf(next_)
                        lonely.append(u)
            else:
                for c, d in itertools.product(C, D):
                    for idx, p in enumerate(P):
                        curr = x.get((c, s, d, p), false_var)
                        prev_ = x.get((c, s, d, P[idx - 1]), false_var) if idx > 0 else false_var
                        next_ = x.get((c, s, d, P[idx + 1]), false_var) if idx < len(P) - 1 else false_var
                        u = model.NewBoolVar(f'lonely_{c}_{s}_{d}_{p}')
                        model.Add(u == 1).OnlyEnforceIf([curr, prev_.Not(), next_.Not()])
                        model.Add(u == 0).OnlyEnforceIf(curr.Not())
                        model.Add(u == 0).OnlyEnforceIf(prev_)
                        model.Add(u == 0).OnlyEnforceIf(next_)
                        lonely.append(u)
        if lonely:
            objective_terms.append(weights.epsilon_pairing * sum(lonely))

    # Итоговая цель
    model.Minimize(sum(objective_terms))

    # ---------------- Решение ----------------
    solver = cp_model.CpSolver()
    solver.parameters.log_search_progress = log
    solver.parameters.num_search_workers = 20
    solver.parameters.relative_gap_limit = 0.05

    print("Начинаем решение...")
    status = solver.Solve(model)
    print("\nРешение завершено.")

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        solution_stats = {
            "status": solver.StatusName(status),
            "objective_value": solver.ObjectiveValue(),
            "wall_time_s": solver.WallTime(),
            "total_lonely_lessons": -1,
            "total_teacher_windows": -1
        }

        # Считаем одиночные (если были добавлены)
        if 'lonely' in locals() and lonely:
            solution_stats["total_lonely_lessons"] = int(sum(solver.Value(v) for v in lonely))

        # Считаем окна учителей
        total_teacher_windows = _calculate_teacher_windows(data, solver, x, z)
        solution_stats["total_teacher_windows"] = int(total_teacher_windows)

        print(f'Финальный статус: {solution_stats["status"]}')
        print(f'Целевая функция: {solution_stats["objective_value"]}')
        print(f'Время решения: {solution_stats["wall_time_s"]:.2f}s')
        if solution_stats["total_lonely_lessons"] != -1:
            print(f'Одинокие уроки (штраф): {solution_stats["total_lonely_lessons"]}')
        print(f'Окна у учителей (сумма разрывов): {solution_stats["total_teacher_windows"]}')

        # Экспорт в Excel
        output_filename = "timetable_or_tools_solution.xlsx"
        final_maps = {"solver": solver, "x": x, "z": z}
        solution_maps = get_solution_maps(data, final_maps, is_pulp=False)
        export_full_schedule_to_excel(output_filename, data, solution_maps, display_maps, solution_stats, weights)
    else:
        print(f'Решение не найдено. Статус: {solver.StatusName(status)}')


if __name__ == '__main__':
    data_source = 'generated'
    data = None

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
        exit()

    display_maps = load_display_maps(db_path_str)
    build_and_solve_with_or_tools(
        data,
        PRINT_TIMETABLE_TO_CONSOLE=False,
        display_maps=display_maps,
        optimize_teacher_windows=True
    )
