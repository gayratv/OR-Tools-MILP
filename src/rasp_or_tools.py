# rasp_or_tools.py (v16 - комментарии к переменным)

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
    # x[(c, s, d, p)] = 1, если у класса c не-делимый предмет s в день d, урок p
    x = { (c, s, d, p): model.NewBoolVar(f'x_{c}_{s}_{d}_{p}')
          for c, s, d, p in itertools.product(C, S, D, P) if s not in splitS }

    # z[(c, s, g, d, p)] = 1, если у класса c делимый предмет s для подгруппы g в день d, урок p
    z = { (c, s, g, d, p): model.NewBoolVar(f'z_{c}_{s}_{g}_{d}_{p}')
          for c, s, g, d, p in itertools.product(C, S, G, D, P) if s in splitS }

    # y[c, d, p] = 1, если у класса c есть любое занятие в день d, период p (вспомогательная переменная)
    y = { (c, d, p): model.NewBoolVar(f'y_{c}_{d}_{p}')
          for c, d, p in itertools.product(C, D, P) }
          
    # is_subj_taught[(c, s, d, p)] = 1, если делимый предмет s преподается ЛЮБОЙ подгруппе класса c в данном слоте
    # (нужна для проверки совместимости)
    # Это ограничение говорит:•
    # is_subj_taught[('10A', 'Eng', 'Mon', 1)] будет 1, потому что z[('10A', 'Eng', 1, 'Mon', 1)] равен 1.•
    # is_subj_taught[('10A', 'CS', 'Mon', 1)] будет 1, потому что z[('10A', 'CS', 2, 'Mon', 1)] равен 1.•
    # is_subj_taught[('10A', 'Trud', 'Mon', 1)] будет 0, потому что ни одна подгруппа не изучает труд в это время.

    is_subj_taught = { (c, s, d, p): model.NewBoolVar(f'ist_{c}_{s}_{d}_{p}')
                       for c, s, d, p in itertools.product(C, splitS, D, P) }


    # --- Жесткие ограничения (Hard Constraints) ---
    # Эти правила должны выполняться неукоснительно.

    # 1. Связь y (слот занят) с x и z (конкретными уроками)
    # Для каждого слота (класс, день, период), переменная y должна быть 1, если в этом слоте есть хотя бы один урок (x или z).
    for c, d, p in itertools.product(C, D, P):
        lessons_in_slot = [x.get((c, s, d, p)) for s in S if s not in splitS] + \
                          [z.get((c, s, g, d, p)) for s in splitS for g in G]
        lessons_in_slot = [v for v in lessons_in_slot if v is not None]
        # y=1 эквивалентно тому, что хотя бы один из уроков в этом слоте активен.
        model.AddBoolOr(lessons_in_slot).OnlyEnforceIf(y[c, d, p])
        model.AddBoolAnd([v.Not() for v in lessons_in_slot]).OnlyEnforceIf(y[c, d, p].Not())

    # 2. Выполнение учебного плана
    # Сумма всех уроков по предмету за неделю должна быть равна часам в плане.
    for (c, s), h in data.plan_hours.items(): model.Add(sum(x[c, s, d, p] for d in D for p in P) == h)
    for (c, s, g), h in data.subgroup_plan_hours.items(): model.Add(sum(z[c, s, g, d, p] for d in D for p in P) == h)

    # 3. Ограничения для учителей
    # Создаем удобную структуру для быстрого доступа к урокам каждого учителя
    teacher_lessons_in_slot = { (t,d,p): [] for t,d,p in itertools.product(data.teachers, D, P) }
    for (c, s), t in data.assigned_teacher.items():
        if s not in splitS: 
            for d, p in itertools.product(D, P): teacher_lessons_in_slot[t, d, p].append(x[c, s, d, p])
    for (c, s, g), t in data.subgroup_assigned_teacher.items():
        for d, p in itertools.product(D, P): teacher_lessons_in_slot[t, d, p].append(z[c, s, g, d, p])

    for t in data.teachers:
        # a) Недельная нагрузка не более лимита
        all_lessons_for_teacher = []
        for d,p in itertools.product(D,P):
            all_lessons_for_teacher.extend(teacher_lessons_in_slot[t,d,p])
        if all_lessons_for_teacher:
             model.Add(sum(all_lessons_for_teacher) <= data.teacher_weekly_cap)
        # b) Не более одного урока в одном слоте (нет "накладок")
        for d, p in itertools.product(D, P):
            lessons = teacher_lessons_in_slot[t, d, p]
            if not lessons: continue
            model.AddAtMostOne(lessons)
            # c) Запрет работы в выходные дни учителя
            # days_off = {'Osi_EM': {'Mon', 'Tue'}}
            if d in data.days_off.get(t, set()):
                for lesson_var in lessons: model.Add(lesson_var == 0)

    # 4. Ограничения на одновременные уроки в классе
    for c, d, p in itertools.product(C, D, P):
        # a) Не более одного не-делимого урока в слоте
        non_split_vars = [x[c, s, d, p] for s in S if s not in splitS]
        model.AddAtMostOne(non_split_vars)
        
        # b) У каждой подгруппы не более одного урока в слоте
        for g in G:
            model.AddAtMostOne(z[c, s, g, d, p] for s in splitS)
        
        # c) Нельзя проводить не-делимый и делимый урок одновременно
        all_split_vars_in_slot = [z[c, s, g, d, p] for s in splitS for g in G]
        for nsv in non_split_vars:
            for sv in all_split_vars_in_slot:
                model.AddBoolOr([nsv.Not(), sv.Not()])

    # 5. Совместимость "делящихся" предметов
    # Связь z и is_subj_taught: флаг, что предмет s преподается классу c в слоте (d,p)
    for c, s, d, p in itertools.product(C, splitS, D, P):
        subgroup_lessons = [z[c, s, g, d, p] for g in G]
        model.AddBoolOr(subgroup_lessons).OnlyEnforceIf(is_subj_taught[c, s, d, p])
        model.AddBoolAnd([v.Not() for v in subgroup_lessons]).OnlyEnforceIf(is_subj_taught[c, s, d, p].Not())

    # Ограничение на несовместимые пары: в одном слоте у класса могут быть только совместимые "делящиеся" предметы
    split_list = sorted(list(splitS))
    for c, d, p in itertools.product(C, D, P):
        for s1, s2 in itertools.combinations(split_list, 2):
            pair = tuple(sorted((s1, s2)))
            if pair not in data.compatible_pairs:
                # Если предметы несовместимы, они не могут идти одновременно
                model.AddBoolOr([is_subj_taught[c, s1, d, p].Not(), is_subj_taught[c, s2, d, p].Not()])


    # --- Целевая функция (мягкие ограничения) ---
    # Это цели, которые решатель будет стараться выполнить, но может нарушить, если это необходимо для выполнения жестких ограничений.
    objective_terms = []

    # 1. Анти-окна: минимизация числа "окон" между уроками.
    # Реализуется через минимизацию количества "начал блоков занятий".
    srun = { (c, d, p): model.NewBoolVar(f'srun_{c}_{d}_{p}') for c, d, p in itertools.product(C, D, P) }
    for c, d in itertools.product(C, D):
        # Для первого урока дня, начало блока = это просто наличие урока.
        model.Add(srun[c, d, P[0]] == y[c, d, P[0]])
        # Для остальных: начало блока = (есть урок СЕЙЧАС) И (не было урока РАНЬШЕ)
        for p_idx in range(1, len(P)):
            p, prev_p = P[p_idx], P[p_idx-1]
            sr, yp, yprev = srun[c,d,p], y[c,d,p], y[c,d,prev_p]
            model.Add(sr == 1).OnlyEnforceIf([yp, yprev.Not()]) # Если y[p] и not y[p-1], то sr=1
            model.Add(sr == 0).OnlyEnforceIf(yp.Not())          # Если not y[p], то sr=0
            model.Add(sr == 0).OnlyEnforceIf(yprev)             # Если y[p-1], то sr=0
    objective_terms.append(weights.alpha_runs * sum(srun.values()))

    # 2. Ранние слоты: легкое предпочтение ранних уроков (минимизация номера периода).
    objective_terms.append(weights.beta_early * sum(p * y[c, d, p] for c,d,p in y))

    # 3. Баланс по дням: минимизация разницы между самым загруженным и самым свободным днем.
    for c in C:
        lessons_per_day = [sum(y[c, d, p] for p in P) for d in D]
        min_lessons, max_lessons = model.NewIntVar(0, len(P), f'minl_{c}'), model.NewIntVar(0, len(P), f'maxl_{c}')
        model.AddMinEquality(min_lessons, lessons_per_day)
        model.AddMaxEquality(max_lessons, lessons_per_day)
        objective_terms.append(weights.gamma_balance * (max_lessons - min_lessons))

    # 4. Хвосты: штраф за уроки после определенного часа (например, после 6-го).
    objective_terms.append(weights.delta_tail * sum(y[c,d,p] for c,d,p in y if p > weights.last_ok_period))

    # 5. Спаренные уроки: штраф за "одиночные" уроки для предметов, которые должны идти парами.

    # Мы минимизируем количество уроков, у которых нет "соседа" ни до, ни после.
    # минимизировать количество "одиноких" уроков.
    # 1. Итерация по предметам: Мы проходим по всем предметам из data.paired_subjects.
    # 2. Разделение логики: Код отдельно обрабатывает делимые(splitS) и неделимые предметы.
    # 3. Поиск "одиночек": Для каждого урока из списка paired_subjects мы проверяем, есть ли у него "сосед"
    # (такой же урок того же класса / подгруппы) на предыдущем или следующем временном слоте.
    # 4. Переменная is_lonely: Если у урока нет ни предыдущего, ни последующего соседа,
    # мы помечаем его как "одинокий" с помощью вспомогательной булевой переменной is_lonely.
    # 5. Минимизация: В целевую функцию добавляется сумма всех переменных is_lonely, умноженная на весовой коэффициент epsilon_pairing.
    # Таким образом, решатель получает штраф за каждый урок, который он не смог спарить,
    # что напрямую мотивирует его создавать пары, где это возможно, для минимизации целевой функции.

    if hasattr(data, 'paired_subjects') and data.paired_subjects:
        lonely_lessons = []
        for s in data.paired_subjects:
            if s in splitS:
                # --- Для ДЕЛИМЫХ предметов (по каждой подгруппе отдельно) ---
                for c, g, d in itertools.product(C, G, D):
                    for p_idx, p in enumerate(P):
                        current_lesson = z.get((c, s, g, d, p))
                        if not current_lesson: continue

                        # Проверяем соседей
                        has_prev = p_idx > 0 and z.get((c, s, g, d, P[p_idx - 1]))
                        has_next = p_idx < len(P) - 1 and z.get((c, s, g, d, P[p_idx + 1]))

                        # Урок "одинок", если у него нет соседей
                        is_lonely = model.NewBoolVar(f'lonely_{c}_{s}_{g}_{d}_{p}')
                        # is_lonely = current_lesson AND (NOT has_prev) AND (NOT has_next)
                        # Это сложно для линейной формы, поэтому используем индикатор.
                        # Если урок есть, а соседей нет, то is_lonely = 1
                        model.Add(is_lonely == 1).OnlyEnforceIf([current_lesson, has_prev.Not(), has_next.Not()])
                        # В остальных случаях is_lonely = 0
                        model.Add(is_lonely == 0).OnlyEnforceIf(current_lesson.Not())
                        model.Add(is_lonely == 0).OnlyEnforceIf(has_prev)
                        model.Add(is_lonely == 0).OnlyEnforceIf(has_next)
                        lonely_lessons.append(is_lonely)
            else:
                # --- Для НЕ-ДЕЛИМЫХ предметов ---
                for c, d in itertools.product(C, D):
                    for p_idx, p in enumerate(P):
                        current_lesson = x.get((c, s, d, p))
                        if not current_lesson: continue

                        has_prev = p_idx > 0 and x.get((c, s, d, P[p_idx - 1]))
                        has_next = p_idx < len(P) - 1 and x.get((c, s, d, P[p_idx + 1]))

                        is_lonely = model.NewBoolVar(f'lonely_{c}_{s}_{d}_{p}')
                        model.Add(is_lonely == 1).OnlyEnforceIf([current_lesson, has_prev.Not(), has_next.Not()])
                        model.Add(is_lonely == 0).OnlyEnforceIf(current_lesson.Not())
                        model.Add(is_lonely == 0).OnlyEnforceIf(has_prev)
                        model.Add(is_lonely == 0).OnlyEnforceIf(has_next)
                        lonely_lessons.append(is_lonely)

        if lonely_lessons and hasattr(weights, 'epsilon_pairing'):
            objective_terms.append(weights.epsilon_pairing * sum(lonely_lessons))

    model.Minimize(sum(objective_terms))

    # --- Решение ---
    solver = cp_model.CpSolver()
    solver.parameters.log_search_progress = log
    solver.parameters.num_search_workers = 16
    solver.parameters.relative_gap_limit = 0.05
    
    print("Начинаем решение...")
    status = solver.Solve(model)
    print("\nРешение завершено.")

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print(f'Финальный статус: {solver.StatusName(status)}')
        print(f'Целевая функция: {solver.ObjectiveValue()}')
        print(f'Затрачено времени: {solver.WallTime()}s')

        # Вывод финального расписания в консоль
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

        # Экспорт в Excel
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
