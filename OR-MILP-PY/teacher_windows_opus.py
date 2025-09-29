# teacher_windows_opus.py

import itertools
from typing import Dict, List, Tuple, Hashable
from ortools.sat.python import cp_model


def add_teacher_window_optimization_span(
    model: cp_model.CpModel,
    teachers: List[str],
    days: List[str],
    periods: List[int],
    teacher_busy: Dict[Tuple[Hashable, Hashable, Hashable], cp_model.IntVar]
) -> cp_model.LinearExpr:
    """
    Добавляет в модель эффективную оптимизацию "окон" учителей через минимизацию "конверта" (span).

    Для каждого дня и учителя вычисляется "конверт" — количество слотов от первого до
    последнего урока включительно. Минимизация суммы этих конвертов стягивает уроки,
    уменьшая окна.

    Этот метод эффективнее, чем `prefix/suffix/inside`, так как требует меньше переменных.

    Аргументы:
        model: Экземпляр `cp_model.CpModel`.
        teachers: Список учителей.
        days: Список дней.
        periods: Список периодов (числа, отсортированы).
        teacher_busy: Словарь `(t, d, p) -> Var`, где Var=1, если учитель t занят в день d в период p.

    Возвращает:
        `cp_model.LinearExpr`, представляющее суммарную длину всех "конвертов" учителей.
        Это выражение нужно добавить в целевую функцию с нужным весом.
    """
    if not periods:
        return model.NewConstant(0)

    min_p, max_p = min(periods), max(periods)
    teacher_spans = []

    for t, d in itertools.product(teachers, days):
        # has_any_lesson_in_day: флаг, есть ли у учителя вообще уроки в этот день.
        has_any_lesson_in_day = model.NewBoolVar(f'has_any_{t}_{d}')
        
        # busy_slots_in_day должна стать равной 1, если у учителя есть хотя бы один урок в этот день, и 0, если день полностью свободен.
        busy_slots_in_day = [teacher_busy[t, d, p] for p in periods]
        model.AddMaxEquality(has_any_lesson_in_day, busy_slots_in_day)

        # first_lesson: номер первого урока учителя в этот день.
        # last_lesson: номер последнего урока учителя в этот день.
        first_lesson = model.NewIntVar(min_p, max_p, f'first_{t}_{d}')
        last_lesson = model.NewIntVar(min_p, max_p, f'last_{t}_{d}')

        # Связываем first/last с переменными занятости teacher_busy.
        # Если учитель занят в слоте p, то first_lesson <= p и last_lesson >= p.
        for p in periods:
            model.Add(first_lesson <= p).OnlyEnforceIf(teacher_busy[t, d, p])
            model.Add(last_lesson >= p).OnlyEnforceIf(teacher_busy[t, d, p])

        # Уточняем домены, чтобы помочь решателю.
        model.Add(last_lesson >= first_lesson).OnlyEnforceIf(has_any_lesson_in_day)

        # Если уроков нет, фиксируем first/last, чтобы уменьшить пространство поиска.
        # Это не обязательно, но помогает решателю.
        model.Add(first_lesson == min_p).OnlyEnforceIf(has_any_lesson_in_day.Not())
        model.Add(last_lesson == min_p).OnlyEnforceIf(has_any_lesson_in_day.Not())

        # span: длина "конверта" (last - first + 1), если есть уроки. Иначе 0.
        # 0 — это нижняя граница (lower bound) для создаваемой переменной span.
        span = model.NewIntVar(0, max_p - min_p + 1, f'span_{t}_{d}')

        # span == last_lesson - first_lesson + 1
        model.Add(span == (last_lesson - first_lesson + 1)).OnlyEnforceIf(has_any_lesson_in_day)
        # Если уроков нет, конверт равен 0.
        model.Add(span == 0).OnlyEnforceIf(has_any_lesson_in_day.Not())

        teacher_spans.append(span)

    # Возвращаем сумму всех "конвертов" для последующей минимизации.
    return cp_model.LinearExpr.Sum(teacher_spans)
