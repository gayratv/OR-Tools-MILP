# rasp_or_tools.py (v16 - комментарии к переменным)

import itertools
from typing import Dict

from ortools.sat.python import cp_model

from input_data import InputData, OptimizationWeights

# Импорты для разных источников данных
from rasp_data import create_manual_data
from access_loader import load_data_from_access, load_display_maps
from rasp_data_generated import create_timetable_data

# Импорты для вывода и экспорта
from print_schedule import get_solution_maps, export_full_schedule_to_excel

def _calculate_teacher_windows(data: InputData, solver: cp_model.CpSolver, x: dict, z: dict) -> int:
    """
    Подсчитывает общее количество "окон" в расписании всех учителей на основе решенной модели.
    "Окно" - это пустой урок между двумя занятыми уроками в течение одного дня.
    """
    teacher_busy_periods = {(t, d): [] for t, d in itertools.product(data.teachers, data.days)}

    # Собираем все занятые слоты для каждого учителя
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
        busy_periods = sorted(list(set(teacher_busy_periods[t, d]))) # Сортируем и убираем дубли
        if len(busy_periods) > 1:
            # Суммируем разрывы: (следующий_урок - текущий_урок - 1)
            total_windows += sum(busy_periods[i+1] - busy_periods[i] - 1 for i in range(len(busy_periods) - 1))
    return total_windows

def build_and_solve_with_or_tools(data: InputData, log: bool = True, PRINT_TIMETABLE_TO_CONSOLE=None, display_maps: Dict[str, Dict[str, str]]=None, optimize_teacher_windows: bool = True):
    """Основная функция для построения и решения модели расписания с помощью OR-Tools."""
    model = cp_model.CpModel()
    C, S, D, P = data.classes, data.subjects, data.days, data.periods
    G, splitS = data.subgroup_ids, data.split_subjects
    weights = OptimizationWeights()

    # --- Переменные ---
    # x[(c, s, d, p)] = 1, если у класса c не-делимый предмет s в день d, урок p
    x = {(c, s, d, p): model.NewBoolVar(f'x_{c}_{s}_{d}_{p}')
         for c, s, d, p in itertools.product(C, S, D, P) if s not in splitS}

    # z[(c, s, g, d, p)] = 1, если у класса c делимый предмет s для подгруппы g в день d, урок p
    z = {(c, s, g, d, p): model.NewBoolVar(f'z_{c}_{s}_{g}_{d}_{p}')
         for c, s, g, d, p in itertools.product(C, S, G, D, P) if s in splitS}

    # y[c, d, p] = 1, если у класса c есть любое занятие в день d, период p (вспомогательная переменная)
    y = {(c, d, p): model.NewBoolVar(f'y_{c}_{d}_{p}')
         for c, d, p in itertools.product(C, D, P)}

    # is_subj_taught[(c, s, d, p)] = 1, если делимый предмет s преподается ЛЮБОЙ подгруппе класса c в данном слоте
    # (нужна для проверки совместимости)
    # Это ограничение говорит:•
    # is_subj_taught[('10A', 'Eng', 'Mon', 1)] будет 1, потому что z[('10A', 'Eng', 1, 'Mon', 1)] равен 1.•
    # is_subj_taught[('10A', 'CS', 'Mon', 1)] будет 1, потому что z[('10A', 'CS', 2, 'Mon', 1)] равен 1.•
    # is_subj_taught[('10A', 'Trud', 'Mon', 1)] будет 0, потому что ни одна подгруппа не изучает труд в это время.

    is_subj_taught = {(c, s, d, p): model.NewBoolVar(f'ist_{c}_{s}_{d}_{p}')
                      for c, s, d, p in itertools.product(C, splitS, D, P)}

    false_var = model.NewBoolVar('false_var')
    model.Add(false_var == 0)

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
    teacher_lessons_in_slot = {(t, d, p): [] for t, d, p in itertools.product(data.teachers, D, P)}
    for (c, s), t in data.assigned_teacher.items():
        if s not in splitS:
            for d, p in itertools.product(D, P): teacher_lessons_in_slot[t, d, p].append(x[c, s, d, p])
    for (c, s, g), t in data.subgroup_assigned_teacher.items():
        for d, p in itertools.product(D, P): teacher_lessons_in_slot[t, d, p].append(z[c, s, g, d, p])

    for t in data.teachers:
        # a) Недельная нагрузка не более лимита
        all_lessons_for_teacher = []
        for d, p in itertools.product(D, P):
            all_lessons_for_teacher.extend(teacher_lessons_in_slot[t, d, p])
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
    srun = {(c, d, p): model.NewBoolVar(f'srun_{c}_{d}_{p}') for c, d, p in itertools.product(C, D, P)}
    for c, d in itertools.product(C, D):
        # Для первого урока дня, начало блока = это просто наличие урока.
        model.Add(srun[c, d, P[0]] == y[c, d, P[0]])
        # Для остальных: начало блока = (есть урок СЕЙЧАС) И (не было урока РАНЬШЕ)
        for p_idx in range(1, len(P)):
            p, prev_p = P[p_idx], P[p_idx - 1]
            sr, yp, yprev = srun[c, d, p], y[c, d, p], y[c, d, prev_p]
            model.Add(sr == 1).OnlyEnforceIf([yp, yprev.Not()])  # Если y[p] и not y[p-1], то sr=1
            model.Add(sr == 0).OnlyEnforceIf(yp.Not())  # Если not y[p], то sr=0
            model.Add(sr == 0).OnlyEnforceIf(yprev)  # Если y[p-1], то sr=0
    objective_terms.append(weights.alpha_runs * sum(srun.values()))

    if optimize_teacher_windows:
        # 1.1. Анти-окна для учителей: минимизация числа "окон" между уроками у учителей.
        # --- НОВЫЙ ПОДХОД: Прямая минимизация "окон" ---

        # teacher_busy[t,d,p] = 1 <=> есть хотя бы один урок у учителя в этом слоте
        teacher_busy = {(t, d, p): model.NewBoolVar(f'tbusy_{t}_{d}_{p}')
                        for t, d, p in itertools.product(data.teachers, D, P)}

        for t, d, p in itertools.product(data.teachers, D, P):
            lessons = teacher_lessons_in_slot.get((t, d, p), [])
            if lessons:
                model.AddBoolOr(lessons).OnlyEnforceIf(teacher_busy[t, d, p])
                model.AddBoolAnd([v.Not() for v in lessons]).OnlyEnforceIf(teacher_busy[t, d, p].Not())
            else:
                model.Add(teacher_busy[t, d, p] == 0)

        # teacher_window[t,d,p] = 1 <=> у учителя t в день d в период p есть "окно"
        teacher_window = {(t, d, p): model.NewBoolVar(f'twin_{t}_{d}_{p}')
                          for t, d, p in itertools.product(data.teachers, D, P)}

        for t, d in itertools.product(data.teachers, D):
            # Вспомогательные переменные для определения "окна"
            has_lesson_before = {p: model.NewBoolVar(f't_before_{t}_{d}_{p}') for p in P}
            has_lesson_after = {p: model.NewBoolVar(f't_after_{t}_{d}_{p}') for p in P}

            # Заполняем has_lesson_before (был ли урок до этого периода)
            model.Add(has_lesson_before[P[0]] == 0) # Перед первым уроком ничего не было
            for i in range(1, len(P)):
                # Урок был до p, если он был до p-1 ИЛИ был в p-1
                model.AddBoolOr([has_lesson_before[P[i-1]], teacher_busy[t, d, P[i-1]]]).OnlyEnforceIf(has_lesson_before[P[i]])
                model.AddImplication(has_lesson_before[P[i]].Not(), has_lesson_before[P[i-1]].Not())
                model.AddImplication(has_lesson_before[P[i]].Not(), teacher_busy[t, d, P[i-1]].Not())

            # Заполняем has_lesson_after (будет ли урок после этого периода)
            model.Add(has_lesson_after[P[-1]] == 0) # После последнего урока ничего не будет
            for i in range(len(P) - 2, -1, -1):
                # Урок будет после p, если он будет после p+1 ИЛИ будет в p+1
                model.AddBoolOr([has_lesson_after[P[i+1]], teacher_busy[t, d, P[i+1]]]).OnlyEnforceIf(has_lesson_after[P[i]])
                model.AddImplication(has_lesson_after[P[i]].Not(), has_lesson_after[P[i+1]].Not())
                model.AddImplication(has_lesson_after[P[i]].Not(), teacher_busy[t, d, P[i+1]].Not())

            # Определяем "окно"
            for p in P:
                # Окно = (был урок до) И (будет урок после) И (нет урока сейчас)
                model.AddBoolAnd([has_lesson_before[p], has_lesson_after[p], teacher_busy[t, d, p].Not()]).OnlyEnforceIf(teacher_window[t, d, p])
                model.AddImplication(teacher_window[t, d, p], has_lesson_before[p])
                model.AddImplication(teacher_window[t, d, p], has_lesson_after[p])
                model.AddImplication(teacher_window[t, d, p], teacher_busy[t, d, p].Not())

        objective_terms.append(weights.alpha_runs_teacher * sum(teacher_window.values()))

# 2. Ранние слоты: легкое предпочтение ранних уроков (минимизация номера периода).
    objective_terms.append(weights.beta_early * sum(p * y[c, d, p] for c, d, p in y))

    # 3. Баланс по дням: минимизация разницы между самым загруженным и самым свободным днем.
    for c in C:
        lessons_per_day = [sum(y[c, d, p] for p in P) for d in D]
        min_lessons, max_lessons = model.NewIntVar(0, len(P), f'minl_{c}'), model.NewIntVar(0, len(P), f'maxl_{c}')
        model.AddMinEquality(min_lessons, lessons_per_day)
        model.AddMaxEquality(max_lessons, lessons_per_day)
        objective_terms.append(weights.gamma_balance * (max_lessons - min_lessons))

    # 4. Хвосты: штраф за уроки после определенного часа (например, после 6-го).
    objective_terms.append(weights.delta_tail * sum(y[c, d, p] for c, d, p in y if p > weights.last_ok_period))

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
                for c, g, d in itertools.product(C, G, D):  # Исправлена опечатка d -> D
                    for p_idx, p in enumerate(P):
                        # Получаем переменные для текущего, предыдущего и следующего уроков.
                        # Если переменной нет, используем целочисленный 0, который решатель понимает как False.
                        current_lesson = z.get((c, s, g, d, p), false_var)
                        prev_lesson = z.get((c, s, g, d, P[p_idx - 1]), false_var) if p_idx > 0 else false_var
                        next_lesson = z.get((c, s, g, d, P[p_idx + 1]), false_var) if p_idx < len(P) - 1 else false_var

                        # Урок может быть "одиноким" только если он существует.
                        # Если current_lesson это 0, то и is_lonely будет 0.
                        is_lonely = model.NewBoolVar(f'lonely_{c}_{s}_{g}_{d}_{p}')

                        # Устанавливаем эквивалентность: is_lonely = 1 ТОГДА И ТОЛЬКО ТОГДА, КОГДА (урок есть И соседей нет)
                        # Это ключевое исправление. Мы добавляем обратную импликацию.
                        # ЕСЛИ (урок есть И соседей нет), ТО is_lonely ДОЛЖЕН быть 1.
                        model.Add(is_lonely == 1).OnlyEnforceIf([current_lesson, prev_lesson.Not(), next_lesson.Not()])
                        model.Add(is_lonely == 0).OnlyEnforceIf(
                            current_lesson.Not())  # Если урока нет, он не может быть одиноким
                        model.Add(is_lonely == 0).OnlyEnforceIf(prev_lesson)  # Если есть сосед слева, он не одинокий
                        model.Add(is_lonely == 0).OnlyEnforceIf(next_lesson)  # Если есть сосед справа, он не одинокий

                        lonely_lessons.append(is_lonely)
            else:
                # --- Для НЕ-ДЕЛИМЫХ предметов ---
                for c, d in itertools.product(C, D):
                    for p_idx, p in enumerate(P):
                        current_lesson = x.get((c, s, d, p), false_var)
                        prev_lesson = x.get((c, s, d, P[p_idx - 1]), false_var) if p_idx > 0 else false_var
                        next_lesson = x.get((c, s, d, P[p_idx + 1]), false_var) if p_idx < len(P) - 1 else false_var

                        is_lonely = model.NewBoolVar(f'lonely_{c}_{s}_{d}_{p}')
                        # Та же логика эквивалентности для не-делимых предметов
                        model.Add(is_lonely == 1).OnlyEnforceIf([current_lesson, prev_lesson.Not(), next_lesson.Not()])
                        model.Add(is_lonely == 0).OnlyEnforceIf(current_lesson.Not())
                        model.Add(is_lonely == 0).OnlyEnforceIf(prev_lesson)
                        model.Add(is_lonely == 0).OnlyEnforceIf(next_lesson)
                        lonely_lessons.append(is_lonely)

        if lonely_lessons and hasattr(weights, 'epsilon_pairing'):
            objective_terms.append(weights.epsilon_pairing * sum(lonely_lessons))

    model.Minimize(sum(objective_terms))

    # --- Решение ---
    solver = cp_model.CpSolver()
    solver.parameters.log_search_progress = log
    solver.parameters.num_search_workers = 20
    solver.parameters.relative_gap_limit = 0.05

    print("Начинаем решение...")
    status = solver.Solve(model)
    print("\nРешение завершено.")

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        # Собираем всю статистику по решению в один словарь
        solution_stats = {
            "status": solver.StatusName(status),
            "objective_value": solver.ObjectiveValue(),
            "wall_time_s": solver.WallTime(),
            "total_lonely_lessons": -1, # Значение по умолчанию
            "total_teacher_windows": -1 # Значение по умолчанию
        }

        # Выводим итоговое количество "одиноких" уроков
        if 'lonely_lessons' in locals() and lonely_lessons:
            total_lonely = sum(solver.Value(v) for v in lonely_lessons)
            solution_stats["total_lonely_lessons"] = total_lonely

        # Подсчет и вывод общего количества "окон" у учителей
        total_teacher_windows = _calculate_teacher_windows(data, solver, x, z)
        solution_stats["total_teacher_windows"] = total_teacher_windows

        # Вывод основной информации в консоль
        print(f'Финальный статус: {solution_stats["status"]}')
        print(f'Целевая функция: {solution_stats["objective_value"]}')
        print(f'Затрачено времени: {solution_stats["wall_time_s"]:.2f}s')
        if solution_stats["total_lonely_lessons"] != -1:
            print(f'Итоговое количество "одиноких" уроков (штраф): {solution_stats["total_lonely_lessons"]}')
        print(f'Итоговое количество "окон" у учителей: {solution_stats["total_teacher_windows"]}')

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
    build_and_solve_with_or_tools(data, PRINT_TIMETABLE_TO_CONSOLE=False, display_maps=display_maps, optimize_teacher_windows=False)
