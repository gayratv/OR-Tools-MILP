# rasp_or_tools.py (v15 - добавлен relative_gap_limit)

import itertools
from ortools.sat.python import cp_model

from input_data import InputData, OptimizationWeights

# Импорты для разных источников данных
from rasp_data import create_manual_data
from access_loader import load_data_from_access
from rasp_data_generated import create_timetable_data

# Импорты для вывода и экспорта
from print_schedule import get_solution_maps, export_full_schedule_to_excel


def build_and_solve_with_or_tools(data: InputData, log: bool = True):
    """Основная функция для построения и решения модели расписания с помощью OR-Tools."""
    model = cp_model.CpModel()
    C, S, D, P = data.classes, data.subjects, data.days, data.periods
    G, splitS = data.subgroup_ids, data.split_subjects
    weights = OptimizationWeights()

    # --- Переменные ---
    x = { (c, s, d, p): model.NewBoolVar(f'x_{c}_{s}_{d}_{p}')
          for c, s, d, p in itertools.product(C, S, D, P) if s not in splitS }
    z = { (c, s, g, d, p): model.NewBoolVar(f'z_{c}_{s}_{g}_{d}_{p}')
          for c, s, g, d, p in itertools.product(C, S, G, D, P) if s in splitS }
    y = { (c, d, p): model.NewBoolVar(f'y_{c}_{d}_{p}')
          for c, d, p in itertools.product(C, D, P) }
    is_subj_taught = { (c, s, d, p): model.NewBoolVar(f'ist_{c}_{s}_{d}_{p}')
                       for c, s, d, p in itertools.product(C, splitS, D, P) }

    # --- Жесткие ограничения ---
    for c, d, p in itertools.product(C, D, P):
        lessons_in_slot = [x.get((c, s, d, p)) for s in S if s not in splitS] + \
                          [z.get((c, s, g, d, p)) for s in splitS for g in G]
        lessons_in_slot = [v for v in lessons_in_slot if v is not None]
        model.AddBoolOr(lessons_in_slot).OnlyEnforceIf(y[c, d, p])
        model.AddBoolAnd([v.Not() for v in lessons_in_slot]).OnlyEnforceIf(y[c, d, p].Not())
    for (c, s), h in data.plan_hours.items(): model.Add(sum(x[c, s, d, p] for d in D for p in P) == h)
    for (c, s, g), h in data.subgroup_plan_hours.items(): model.Add(sum(z[c, s, g, d, p] for d in D for p in P) == h)
    teacher_lessons_in_slot = { (t,d,p): [] for t,d,p in itertools.product(data.teachers, D, P) }
    for (c, s), t in data.assigned_teacher.items():
        if s not in splitS: 
            for d, p in itertools.product(D, P): teacher_lessons_in_slot[t, d, p].append(x[c, s, d, p])
    for (c, s, g), t in data.subgroup_assigned_teacher.items():
        for d, p in itertools.product(D, P): teacher_lessons_in_slot[t, d, p].append(z[c, s, g, d, p])
    for t in data.teachers:
        all_lessons_for_teacher = []
        for d,p in itertools.product(D,P):
            all_lessons_for_teacher.extend(teacher_lessons_in_slot[t,d,p])
        if all_lessons_for_teacher:
             model.Add(sum(all_lessons_for_teacher) <= data.teacher_weekly_cap)
        for d, p in itertools.product(D, P):
            lessons = teacher_lessons_in_slot[t, d, p]
            if not lessons: continue
            model.AddAtMostOne(lessons)
            if d in data.days_off.get(t, set()):
                for lesson_var in lessons: model.Add(lesson_var == 0)
    for c, d, p in itertools.product(C, D, P):
        non_split_vars = [x[c, s, d, p] for s in S if s not in splitS]
        model.AddAtMostOne(non_split_vars)
        for g in G:
            model.AddAtMostOne(z[c, s, g, d, p] for s in splitS)
        all_split_vars_in_slot = [z[c, s, g, d, p] for s in splitS for g in G]
        for nsv in non_split_vars:
            for sv in all_split_vars_in_slot:
                model.AddBoolOr([nsv.Not(), sv.Not()])
    for c, s, d, p in itertools.product(C, splitS, D, P):
        subgroup_lessons = [z[c, s, g, d, p] for g in G]
        model.AddBoolOr(subgroup_lessons).OnlyEnforceIf(is_subj_taught[c, s, d, p])
        model.AddBoolAnd([v.Not() for v in subgroup_lessons]).OnlyEnforceIf(is_subj_taught[c, s, d, p].Not())
    split_list = sorted(list(splitS))
    for c, d, p in itertools.product(C, D, P):
        for s1, s2 in itertools.combinations(split_list, 2):
            pair = tuple(sorted((s1, s2)))
            if pair not in data.compatible_pairs:
                model.AddBoolOr([is_subj_taught[c, s1, d, p].Not(), is_subj_taught[c, s2, d, p].Not()])

    # --- Целевая функция ---
    objective_terms = []
    srun = { (c, d, p): model.NewBoolVar(f'srun_{c}_{d}_{p}') for c, d, p in itertools.product(C, D, P) }
    for c, d in itertools.product(C, D):
        model.Add(srun[c, d, P[0]] == y[c, d, P[0]])
        for p_idx in range(1, len(P)):
            p, prev_p = P[p_idx], P[p_idx-1]
            sr, yp, yprev = srun[c,d,p], y[c,d,p], y[c,d,prev_p]
            model.Add(sr == 1).OnlyEnforceIf([yp, yprev.Not()])
            model.Add(sr == 0).OnlyEnforceIf(yp.Not())
            model.Add(sr == 0).OnlyEnforceIf(yprev)
    objective_terms.append(weights.alpha_runs * sum(srun.values()))
    objective_terms.append(weights.beta_early * sum(p * y[c, d, p] for c,d,p in y))
    for c in C:
        lessons_per_day = [sum(y[c, d, p] for p in P) for d in D]
        min_lessons, max_lessons = model.NewIntVar(0, len(P), f'minl_{c}'), model.NewIntVar(0, len(P), f'maxl_{c}')
        model.AddMinEquality(min_lessons, lessons_per_day)
        model.AddMaxEquality(max_lessons, lessons_per_day)
        objective_terms.append(weights.gamma_balance * (max_lessons - min_lessons))
    objective_terms.append(weights.delta_tail * sum(y[c,d,p] for c,d,p in y if p > weights.last_ok_period))

    model.Minimize(sum(objective_terms))

    # --- Решение ---
    solver = cp_model.CpSolver()
    solver.parameters.log_search_progress = log
    solver.parameters.num_search_workers = 16
    # Устанавливаем относительный разрыв в 5% для ранней остановки
    solver.parameters.relative_gap_limit = 0.05
    
    print("Начинаем решение...")
    status = solver.Solve(model)
    print("\nРешение завершено.")

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print(f'Финальный статус: {solver.StatusName(status)}')
        print(f'Целевая функция: {solver.ObjectiveValue()}')
        print(f'Затрачено времени: {solver.WallTime()}s')

        # Вывод и экспорт
        print("\n--- ФИНАЛЬНОЕ РАСПИСАНИЕ ---")
        for c in data.classes:
            print(f"\n=== Класс {c} ===")
            for d in data.days:
                row = []
                for p in data.periods:
                    cell = None
                    for s in data.subjects:
                        if s not in data.split_subjects and solver.Value(x.get((c, s, d, p), 0)):
                            t = data.assigned_teacher.get((c, s), '?')
                            cell = f"{p}: {s} ({t})"
                            break
                    if cell is None:
                        pieces = []
                        for s in data.split_subjects:
                            for g in data.subgroup_ids:
                                if solver.Value(z.get((c, s, g, d, p), 0)):
                                    t = data.subgroup_assigned_teacher.get((c, s, g), '?')
                                    pieces.append(f"{s}[g{g}::{t}]")
                        if pieces:
                            cell = f"{p}: " + "+".join(pieces)
                    row.append(cell or f"{p}: —")
                print(f"{d} | " + ", ".join(row))

        output_filename = "timetable_or_tools_solution.xlsx"
        final_maps = {"solver": solver, "x": x, "z": z}
        solution_maps = get_solution_maps(data, final_maps, is_pulp=False)
        export_full_schedule_to_excel(output_filename, data, solution_maps)

    else:
        print(f'Решение не найдено. Статус: {solver.StatusName(status)}')

if __name__ == '__main__':
    data_source = 'generated'
    data = None

    if data_source == 'db':
        print("--- Источник данных: MS Access DB ---")
        db_path_str = r"F:/_prg/python/OR-Tools-MILP/src/db/rasp3-new-calculation.accdb"
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

    build_and_solve_with_or_tools(data)
