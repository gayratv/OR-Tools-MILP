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
from input_data import InputData, OptimizationWeights, OptimizationGoals
from rasp_data import create_manual_data
from access_loader import load_data_from_access, load_display_maps
from rasp_data_generated import create_timetable_data
from print_schedule import get_solution_maps, export_full_schedule_to_excel, print_schedule_to_console


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

    # x[c,s,d,p] — неделимый предмет

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


def _validate_input_data(data: InputData) -> None:
    """
    Полная валидация входных данных. Проверяет:
      - базовые множества и уникальность (days, periods, classes, subjects, teachers);
      - целостность планов часов и закреплений (plan_hours / subgroup_plan_hours / assigned_teacher / subgroup_assigned_teacher);
      - согласованность split‑логики (split_subjects, subgroup_ids, compatible_pairs, must_sync_split_subjects);
      - валидность ограничений/предпочтений (days_off, teacher_forbidden_slots, forbidden_slots,
        grade_max_lessons_per_day, subjects_not_last_lesson, elementary_english_periods,
        grade_subject_max_consecutive_days, class_*_weight, teacher_*_weight);
      - грубые необходимые условия выполнимости по «вместимости» классов/учителей и по английскому в начальной школе.
    При наличии проблем собирает все сообщения и выбрасывает ValueError с агрегированным отчётом.
    """
    from collections import defaultdict

    errors: list[str] = []

    # ---------- Локальные помощники ----------
    def add_err(msg: str) -> None:
        errors.append(str(msg))

    def dups(seq):
        seen, rep = set(), set()
        for x in seq:
            if x in seen:
                rep.add(x)
            else:
                seen.add(x)
        return sorted(rep)

    # Базовые множества
    days = list(data.days)
    periods = list(data.periods)
    classes = list(data.classes)
    subjects = list(data.subjects)
    teachers = list(data.teachers)
    splitS = set(getattr(data, 'split_subjects', set()))
    G = list(getattr(data, 'subgroup_ids', []))

    # ---------- 1) БАЗОВАЯ СТРУКТУРА / УНИКАЛЬНОСТЬ ----------
    if not days:
        add_err("Пустой список days.")
    elif len(dups(days)) > 0:
        add_err(f"Дубли дней в days: {dups(days)}")

    if not periods:
        add_err("Пустой список periods.")
    else:
        if any(not isinstance(p, int) for p in periods):
            add_err("Все элементы periods должны быть целыми числами.")
        if sorted(periods) != periods:
            add_err("Periods должны быть строго возрастающими (отсортированы по возрастанию без повторов).")
        if len(dups(periods)) > 0:
            add_err(f"Дубли периодов в periods: {dups(periods)}")
        if min(periods) < 1:
            add_err("Минимальный номер периода должен быть >= 1.")

    if not classes:
        add_err("Пустой список classes.")
    else:
        class_names = [c.name for c in classes]
        if any(not isinstance(c.name, str) or not c.name for c in classes):
            add_err("У всех классов должно быть непустое строковое имя (ClassInfo.name).")
        if len(dups(class_names)) > 0:
            add_err(f"Дубли имён классов: {dups(class_names)}")
        if any(not isinstance(c.grade, int) or c.grade < 1 for c in classes):
            add_err("У всех классов grade должен быть целым числом >= 1.")
        class_set = set(class_names)
        class_grade = {c.name: c.grade for c in classes}

    if not subjects:
        add_err("Пустой список subjects.")
    elif len(dups(subjects)) > 0:
        add_err(f"Дубли предметов в subjects: {dups(subjects)}")
    subject_set = set(subjects)

    if not teachers:
        add_err("Пустой список teachers.")
    elif len(dups(teachers)) > 0:
        add_err(f"Дубли преподавателей в teachers: {dups(teachers)}")
    teacher_set = set(teachers)

    # English subject name
    eng_name = getattr(data, 'english_subject_name', '')
    if eng_name and eng_name not in subject_set:
        add_err(f"english_subject_name='{eng_name}' отсутствует в subjects.")

    # Split subjects / subgroups
    if not set(splitS).issubset(subject_set):
        bad = sorted(set(splitS) - subject_set)
        add_err(f"split_subjects содержит неизвестные предметы: {bad}")
    if not G:
        add_err("subgroup_ids пуст. Для split‑логики нужны хотя бы один ID подгруппы.")
    else:
        if any(not isinstance(g, int) for g in G):
            add_err("Все subgroup_ids должны быть целыми числами.")
        if len(dups(G)) > 0:
            add_err(f"Дубли значений в subgroup_ids: {dups(G)}")

    # ---------- 2) ПЛАНЫ И ЗАКРЕПЛЕНИЯ ----------
    # plan_hours: только НЕ split‑предметы; subgroup_plan_hours: только split‑предметы
    for (c, s), h in getattr(data, 'plan_hours', {}).items():
        if c not in class_set:
            add_err(f"plan_hours: неизвестный класс '{c}'.")
        if s not in subject_set:
            add_err(f"plan_hours: неизвестный предмет '{s}'.")
        if s in splitS:
            add_err(f"plan_hours: предмет '{s}' помечен как split, ему нельзя задавать часы в plan_hours, используйте subgroup_plan_hours.")
        if not isinstance(h, int) or h < 0:
            add_err(f"plan_hours[{(c, s)}] должно быть целым >= 0.")

    for (c, s, g), h in getattr(data, 'subgroup_plan_hours', {}).items():
        if c not in class_set:
            add_err(f"subgroup_plan_hours: неизвестный класс '{c}'.")
        if s not in subject_set:
            add_err(f"subgroup_plan_hours: неизвестный предмет '{s}'.")
        if s not in splitS:
            add_err(f"subgroup_plan_hours: предмет '{s}' не является split, ему нельзя задавать часы по подгруппам.")
        if g not in G:
            add_err(f"subgroup_plan_hours: неизвестный ID подгруппы '{g}' для {(c, s)}.")
        if not isinstance(h, int) or h < 0:
            add_err(f"subgroup_plan_hours[{(c, s, g)}] должно быть целым >= 0.")

    # assigned_teacher: только для НЕ split‑пар
    for (c, s), t in getattr(data, 'assigned_teacher', {}).items():
        if c not in class_set or s not in subject_set:
            add_err(f"assigned_teacher: неизвестная пара {(c, s)}.")
        if s in splitS:
            add_err(f"assigned_teacher: предмет '{s}' является split, используйте subgroup_assigned_teacher.")
        if t not in teacher_set:
            add_err(f"assigned_teacher: неизвестный учитель '{t}' для {(c, s)}.")
        # Если есть положительные часы — обязан быть учитель
        h = getattr(data, 'plan_hours', {}).get((c, s), 0)
        if h > 0 and (c, s) not in getattr(data, 'plan_hours', {}):
            add_err(f"assigned_teacher: есть закрепление {(c, s)}, но отсутствуют часы в plan_hours.")

    # subgroup_assigned_teacher: только для split‑трёхкортежей
    for (c, s, g), t in getattr(data, 'subgroup_assigned_teacher', {}).items():
        if c not in class_set or s not in subject_set or g not in G:
            add_err(f"subgroup_assigned_teacher: неизвестный ключ {(c, s, g)}.")
        if s not in splitS:
            add_err(f"subgroup_assigned_teacher: предмет '{s}' не является split.")
        if t not in teacher_set:
            add_err(f"subgroup_assigned_teacher: неизвестный учитель '{t}' для {(c, s, g)}.")
        h = getattr(data, 'subgroup_plan_hours', {}).get((c, s, g), 0)
        if h > 0 and (c, s, g) not in getattr(data, 'subgroup_plan_hours', {}):
            add_err(f"subgroup_assigned_teacher: есть закрепление {(c, s, g)}, но отсутствуют часы в subgroup_plan_hours.")

    # Наличие учителя при положительных часах
    for (c, s), h in getattr(data, 'plan_hours', {}).items():
        if h > 0 and (c, s) not in getattr(data, 'assigned_teacher', {}):
            add_err(f"Для {(c, s)} заданы часы ({h}), но не указан assigned_teacher.")
    for (c, s, g), h in getattr(data, 'subgroup_plan_hours', {}).items():
        if h > 0 and (c, s, g) not in getattr(data, 'subgroup_assigned_teacher', {}):
            add_err(f"Для {(c, s, g)} заданы часы ({h}), но не указан subgroup_assigned_teacher.")

    # ---------- 3) ОГРАНИЧЕНИЯ/ПОЛИТИКИ ----------
    # days_off / teacher_forbidden_slots / forbidden_slots
    day_set = set(days)
    period_set = set(periods)

    for t, offs in getattr(data, 'days_off', {}).items():
        if t not in teacher_set:
            add_err(f"days_off: неизвестный учитель '{t}'.")
        for d in offs:
            if d not in day_set:
                add_err(f"days_off[{t}]: неизвестный день '{d}'.")

    for t, slots in getattr(data, 'teacher_forbidden_slots', {}).items():
        if t not in teacher_set:
            add_err(f"teacher_forbidden_slots: неизвестный учитель '{t}'.")
        seen_tp = set()
        for d, p in slots or []:
            if d not in day_set:
                add_err(f"teacher_forbidden_slots[{t}]: неизвестный день '{d}'.")
            if p not in period_set:
                add_err(f"teacher_forbidden_slots[{t}]: неизвестный период '{p}'.")
            if (d, p) in seen_tp:
                add_err(f"teacher_forbidden_slots[{t}]: дублируется слот {(d, p)}.")
            seen_tp.add((d, p))

    for (c, d, p) in getattr(data, 'forbidden_slots', set()):
        if c not in class_set:
            add_err(f"forbidden_slots: неизвестный класс '{c}'.")
        if d not in day_set:
            add_err(f"forbidden_slots[{c}]: неизвестный день '{d}'.")
        if p not in period_set:
            add_err(f"forbidden_slots[{c}]: неизвестный период '{p}'.")

    # grade_max_lessons_per_day
    for g, lim in getattr(data, 'grade_max_lessons_per_day', {}).items():
        if not isinstance(g, int) or g < 1:
            add_err(f"grade_max_lessons_per_day: недопустимый ключ grade={g}.")
        if not isinstance(lim, int) or lim < 0:
            add_err(f"grade_max_lessons_per_day[{g}] должно быть целым >= 0.")
        if periods and lim > len(periods):
            # не ошибка, но предупреждение можно было бы сделать мягким; считаем корректным
            pass

    # subjects_not_last_lesson
    for g, subs in getattr(data, 'subjects_not_last_lesson', {}).items():
        if not isinstance(g, int) or g < 1:
            add_err(f"subjects_not_last_lesson: недопустимый ключ grade={g}.")
        for s in subs:
            if s not in subject_set:
                add_err(f"subjects_not_last_lesson[{g}]: неизвестный предмет '{s}'.")

    # elementary_english_periods
    english_periods = set(getattr(data, 'elementary_english_periods', set()))
    if english_periods and not english_periods.issubset(period_set):
        add_err(f"elementary_english_periods содержит номера не из periods: {sorted(english_periods - period_set)}")

    # grade_subject_max_consecutive_days
    for g, mp in getattr(data, 'grade_subject_max_consecutive_days', {}).items():
        if not isinstance(g, int) or g < 1:
            add_err(f"grade_subject_max_consecutive_days: недопустимый ключ grade={g}.")
        for s, lim in mp.items():
            if s not in subject_set:
                add_err(f"grade_subject_max_consecutive_days[{g}]: неизвестный предмет '{s}'.")
            if not isinstance(lim, int) or lim < 1:
                add_err(f"grade_subject_max_consecutive_days[{g}]['{s}'] должно быть целым >= 1.")
            if days and lim > len(days):
                # технически допустимо, просто правило становится неактивным
                pass

    # class_slot_weight / teacher_slot_weight / class_subject_day_weight
    for (c, d, p), w in getattr(data, 'class_slot_weight', {}).items():
        if c not in class_set or d not in day_set or p not in period_set:
            add_err(f"class_slot_weight: неверный ключ {(c, d, p)}.")
        if not isinstance(w, (int, float)):
            add_err(f"class_slot_weight[{(c, d, p)}] должно быть числом.")

    for (t, d, p), w in getattr(data, 'teacher_slot_weight', {}).items():
        if t not in teacher_set or d not in day_set or p not in period_set:
            add_err(f"teacher_slot_weight: неверный ключ {(t, d, p)}.")
        if not isinstance(w, (int, float)):
            add_err(f"teacher_slot_weight[{(t, d, p)}] должно быть числом.")

    for (c, s, d), w in getattr(data, 'class_subject_day_weight', {}).items():
        if c not in class_set or s not in subject_set or d not in day_set:
            add_err(f"class_subject_day_weight: неверный ключ {(c, s, d)}.")
        if not isinstance(w, (int, float)):
            add_err(f"class_subject_day_weight[{(c, s, d)}] должно быть числом.")

    # paired_subjects
    for s in getattr(data, 'paired_subjects', set()):
        if s not in subject_set:
            add_err(f"paired_subjects: неизвестный предмет '{s}'.")

    # compatible_pairs
    for pair in getattr(data, 'compatible_pairs', set()):
        if not isinstance(pair, tuple) or len(pair) != 2:
            add_err(f"compatible_pairs: ожидалась пара предметов, получено {pair}.")
            continue
        s1, s2 = pair
        if s1 not in splitS or s2 not in splitS:
            add_err(f"compatible_pairs: предметы {pair} должны принадлежать split_subjects.")
        if tuple(sorted(pair)) != pair:
            add_err(f"compatible_pairs: пары должны храниться в отсортированном виде, у вас {pair}.")

    # ---------- 4) MUST_SYNC ДЛЯ SPLIT‑ПРЕДМЕТОВ ----------
    must_sync = set(getattr(data, 'must_sync_split_subjects', set()))
    # все из splitS
    if not must_sync.issubset(splitS):
        add_err(f"must_sync_split_subjects содержит не‑split предметы: {sorted(must_sync - splitS)}")

    # (4a) равенство часов по подгруппам и разные преподаватели
    for s in must_sync:
        for c in class_set:
            # часы по всем подгруппам
            hours = [getattr(data, 'subgroup_plan_hours', {}).get((c, s, g), 0) for g in G]
            if any(h > 0 for h in hours):
                if len(set(hours)) != 1:
                    add_err(f"Невыполнимо (must_sync): в классе {c} для предмета '{s}' часы по подгруппам не равны: {hours}.")
                # преподы по подгруппам (только там, где часы > 0)
                t_by_g = [getattr(data, 'subgroup_assigned_teacher', {}).get((c, s, g)) for g in G]
                # проверяем дубликаты учителей среди активных групп
                active = [(g, t) for g, t, h in zip(G, t_by_g, hours) if h > 0]
                ts = [t for _, t in active if t is not None]
                if len(ts) != len(set(ts)):
                    add_err(f"Невыполнимо (must_sync): в классе {c} предмет '{s}' ведут одинаковые преподаватели на разных подгруппах ({ts}). "
                            f"Синхронно вести уроки одним и тем же учителем невозможно.")
                # предыдущая «узкая» проверка (для совместимости со старым поведением)
                uniq_teachers = {getattr(data, 'subgroup_assigned_teacher', {}).get((c, s, g)) for g, h in zip(G, hours) if h > 0}
                uniq_teachers.discard(None)
                if len(uniq_teachers) == 1 and sum(hours) > 0:
                    add_err(
                        f"Невыполнимо: предмет '{s}' указан в must_sync, но в классе {c} обе/неск. подгруппы ведёт один учитель ({next(iter(uniq_teachers))}). "
                        f"Назначьте разных учителей или уберите '{s}' из must_sync_split_subjects."
                    )

    # ---------- 5) НЕОБХОДИМЫЕ УСЛОВИЯ ВЫПОЛНИМОСТИ (грубые capacity‑проверки) ----------
    # (5a) вместимость учителей по неделе
    periods_per_day = len(periods)
    # суммарные назначенные часы на учителя
    teacher_load = defaultdict(int)
    for (c, s), h in getattr(data, 'plan_hours', {}).items():
        if h > 0:
            t = getattr(data, 'assigned_teacher', {}).get((c, s))
            if t in teacher_set:
                teacher_load[t] += h
    for (c, s, g), h in getattr(data, 'subgroup_plan_hours', {}).items():
        if h > 0:
            t = getattr(data, 'subgroup_assigned_teacher', {}).get((c, s, g))
            if t in teacher_set:
                teacher_load[t] += h

    # доступные слоты для каждого учителя
    t_forb = defaultdict(set)  # teacher -> {(d,p), ...}
    for t, slots in getattr(data, 'teacher_forbidden_slots', {}).items():
        for d, p in slots or []:
            t_forb[t].add((d, p))
    t_days_off = {t: set(v) for t, v in getattr(data, 'days_off', {}).items()}

    for t in teacher_set:
        weekly_capacity = 0
        for d in days:
            if d in t_days_off.get(t, set()):
                continue
            forb_count = sum(1 for p in periods if (d, p) in t_forb.get(t, set()))
            day_cap = max(0, periods_per_day - forb_count)
            weekly_capacity += day_cap
        if teacher_load.get(t, 0) > weekly_capacity:
            add_err(f"Невыполнимо: учитель '{t}' имеет назначенных часов {teacher_load[t]}, "
                    f"но доступная недельная вместимость с учётом days_off/forbidden_slots равна {weekly_capacity}.")

    # (5b) вместимость классов по неделе
    # нижняя оценка требуемых слот‑занятий у класса:
    #   non_split_hours + max_{g}(sum_{s∈split} hours[c,s,g])
    # (неделимые не могут идти параллельно со split; в одной подгруппе в слот может идти только один split‑урок)
    grade_day_limit = getattr(data, 'grade_max_lessons_per_day', {})
    forb = getattr(data, 'forbidden_slots', set())
    forb_by_cd = defaultdict(int)
    for (c, d, p) in forb:
        forb_by_cd[(c, d)] += 1

    for c in class_set:
        non_split_hours = sum(h for (cc, s), h in getattr(data, 'plan_hours', {}).items() if cc == c)
        by_group = defaultdict(int)
        for (cc, s, g), h in getattr(data, 'subgroup_plan_hours', {}).items():
            if cc == c:
                by_group[g] += h
        split_lb = max(by_group.values(), default=0)
        required_slots_min = non_split_hours + split_lb

        # недельная ёмкость: по каждому дню min(лимит_по_дню, доступные_слоты_в_дне_после_forbidden)
        g = class_grade.get(c)
        per_day_limit = grade_day_limit.get(g, len(periods))
        weekly_capacity = 0
        for d in days:
            day_free = max(0, len(periods) - forb_by_cd.get((c, d), 0))
            weekly_capacity += min(per_day_limit, day_free)

        if required_slots_min > weekly_capacity:
            add_err(f"Невыполнимо: классу {c} требуется минимум {required_slots_min} слот‑уроков "
                    f"(несплит={non_split_hours}, сплит (нижняя оценка)={split_lb}), "
                    f"а недельная ёмкость равна {weekly_capacity} с учётом forbidden_slots и дневных лимитов.")

    # (5c) английский в начальной школе: достаточно ли разрешённых слотов
    if eng_name and eng_name in subject_set and english_periods:
        for c in class_set:
            g = class_grade.get(c)
            if g in {2, 3, 4}:
                # требуемое число «слот‑уроков» англ. за неделю
                if eng_name in splitS:
                    req_eng = max(
                        (getattr(data, 'subgroup_plan_hours', {}).get((c, eng_name, g_id), 0) for g_id in G),
                        default=0
                    )
                else:
                    req_eng = getattr(data, 'plan_hours', {}).get((c, eng_name), 0)

                # доступные англ. слоты с учётом запрещённых слотов класса
                eng_cap = 0
                for d in days:
                    forb_p = {p for p in periods if (c, d, p) in forb}
                    allowed_today = [p for p in english_periods if p in period_set and p not in forb_p]
                    eng_cap += len(allowed_today)

                if req_eng > eng_cap:
                    add_err(f"Невыполнимо: в классе {c} (grade={g}) требуется английский {req_eng} ч/нед, "
                            f"но доступных слотов на разрешённых периодах всего {eng_cap} "
                            f"(разрешённые: {sorted(english_periods)}; учитываются forbidden_slots класса).")

    # ---------- Финал ----------
    if errors:
        raise ValueError("Обнаружены проблемы во входных данных:\n  - " + "\n  - ".join(errors))


# ---------------------- 3) ОСНОВНАЯ ФУНКЦИЯ ПОСТРОЕНИЯ/РЕШЕНИЯ ----------------------

def build_and_solve_with_or_tools(
    data: InputData,
    log: bool = True,
    PRINT_TIMETABLE_TO_CONSOLE: bool = False,
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
    class_names = [c.name for c in data.classes]
    class_grades = {c.name: c.grade for c in data.classes}

    # grade_subject_max_consecutive_days = {5: {"PE": 2}}
    grade_subject_max_consecutive_days = getattr(data, 'grade_subject_max_consecutive_days', {})
    C, S, D, P = class_names, data.subjects, data.days, data.periods

    # split_subjects = {"eng", "cs", "labor"}
    G, splitS = data.subgroup_ids, data.split_subjects
    weights = OptimizationWeights()
    optimizationGoals = OptimizationGoals()

    _validate_input_data(data)

    # -------------------------- 3.1) ПЕРЕМЕННЫЕ МОДЕЛИ --------------------------

    # x[c,s,d,p] — неделимый предмет
    # Переменная x[класс, предмет, день, период] принимает значение 1, если неделимый предмет назначен в данный слот, иначе 0.
    x = {(c, s, d, p): model.NewBoolVar(f'x_{c}_{s}_{d}_{p}')
         for c, s, d, p in itertools.product(C, S, D, P)
         if s not in splitS and (c, s) in data.plan_hours}

    # z[c,s,g,d,p] — делимый предмет по подгруппе g
    z = {(c, s, g, d, p): model.NewBoolVar(f'z_{c}_{s}_{g}_{d}_{p}')
         for c, s, g, d, p in itertools.product(C, S, G, D, P)
         if s in splitS and (c, s, g) in data.subgroup_plan_hours}

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

    zero_var = model.NewConstant(0)

    # Предварительно соберём «уроки класса в слоте» для удобного OR
    # Эта вспомогательная функция собирает все переменные CP-SAT,
    # которые представляют уроки для данного класса (c) в определённый
    # день (d) и период (p). Она объединяет как неделимые предметы (x),
    # так и делимые предметы (z) для всех подгрупп.
    # Используется для построения ограничения (1) и расчёта "y".
    def _class_lessons_in_slot(c, d, p) -> List[cp_model.IntVar]:
        non_split = [x[(c, s, d, p)] for s in S if s not in splitS if (c, s, d, p) in x]
        split = [z[(c, s, g, d, p)] for s in splitS for g in G if (c, s, g, d, p) in z]
        return non_split + split

    # teacher_lessons_in_slot[(t,d,p)] — список булевых уроков данного учителя в слоте
    teacher_lessons_in_slot: Dict[Tuple[Hashable, Hashable, Hashable], List[cp_model.IntVar]] = {
        (t, d, p): [] for t, d, p in itertools.product(data.teachers, D, P)
    }
    for c, s, d, p in itertools.product(C, S, D, P):
        if s not in splitS and (c, s) in data.assigned_teacher:
            teacher_lessons_in_slot[data.assigned_teacher[c, s], d, p].append(x[c, s, d, p])
    for c, s, g, d, p in itertools.product(C, splitS, G, D, P):
        if (c, s, g) in data.subgroup_assigned_teacher:
            teacher_lessons_in_slot[data.subgroup_assigned_teacher[c, s, g], d, p].append(z[c, s, g, d, p])

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
    # y[c,d,p] — в слоте у класса есть ЛЮБОЙ урок
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

    # (2a) Предметы по 2 часа в неделю (не из paired_subjects) не ставим дважды в один день
    paired = getattr(data, 'paired_subjects', set())
    # plan_hours = { ("5A", "math"): 2,
    for (c, s), h in data.plan_hours.items():
        if h == 2 and s not in paired:
            for d in D:
                model.Add(sum(x[c, s, d, p] for p in P) <= 1)
    for (c, s, g), h in data.subgroup_plan_hours.items():
        if h == 2 and s not in paired:
            for d in D:
                model.Add(sum(z[c, s, g, d, p] for p in P) <= 1)

    # (3) Ограничения для учителей
    for t in data.teachers:
        # (3a) Не более одного урока в слоте
        for d, p in itertools.product(D, P):
            lessons = teacher_lessons_in_slot[t, d, p]
            if lessons:
                model.AddAtMostOne(list(lessons))  # список, не генератор

            # (3b) Индивидуальные выходные/недоступные дни - выходные дни учителя
            # days_off = {"Petrov": {"Mon"}}
            if d in getattr(data, 'days_off', {}).get(t, set()):
                for v in lessons:
                    model.Add(v == 0)

            # (3c) Явно запрещённые слоты учителя (если есть)
            #  teacher_forbidden_slots = {
            #         "Petrov": [("Tue", 1)],
            #         "Nikolaev": [("Thu", 7)],
            #     }
            # учитель не может вести уроки в определенные слоты
            for (td, tp) in getattr(data, 'teacher_forbidden_slots', {}).get(t, []):
                if td == d and tp == p:
                    for v in lessons:
                        model.Add(v == 0)

    # (4) Ограничения внутри класса/слота
    for c, d, p in itertools.product(C, D, P):
        # (4a) Не более одного НЕДЕЛИМОГО предмета
        # в одном классе в один и тот же момент времени может идти не более одного "цельного" (неделимого на подгруппы) урока.
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
        # all_split_vars_in_slot[c,d,p]
        # собирает в один список все возможные уроки, делимые на подгруппы, которые могут проходить у класса c в слоте (d, p).
        all_split_vars_in_slot = [z[(c, s, g, d, p)] for s in splitS for g in G if (c, s, g, d, p) in z]
        if all_split_vars_in_slot:
            # has_split[c,d,p] — в слоте есть ХОТЯ БЫ ОДИН сплит‑урок (любой предмет, любая подгруппа)
            # устанавливает эквивалентность между переменной has_split и логической операцией ИЛИ(OR) над всеми переменными в списке all_split_vars_in_slot.
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
    # is_subj_taught[c,s,d,p] — флаг, что сплит‑предмет s преподаётся (какой‑то подгруппе) в слоте
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

    # (6) Дополнительные ограничения для начальной школы и общие правила
    # subjects_not_last_lesson = {2: {"math", "eng"}, 5: {"math"}}
    subjects_not_last_lesson = getattr(data, 'subjects_not_last_lesson', {})
    # elementary_english_periods = {2, 3, 4}
    english_periods = getattr(data, 'elementary_english_periods', {2, 3, 4})

    # Максимальное число уроков в день по параллели, например {2: 4, 3: 5, 4: 5}
    # grade_max_lessons_per_day = {5: 7, 2: 4}
    grade_max_lessons_per_day = getattr(data, 'grade_max_lessons_per_day', {})

    # Дополняем grade_max_lessons_per_day для всех уникальных классов
    unique_grades = {class_grades.get(c) for c in C if class_grades.get(c) is not None}
    for g in unique_grades:
        if g not in grade_max_lessons_per_day:
            grade_max_lessons_per_day[g] = max(P)


    # (6a) Ограничение по числу уроков в день
    for c in C:
        g = class_grades.get(c)  # class_grades - год обучения
        if g is not None:
            for d in D:
                day_load = sum(y[c, d, p] for p in P) # y[c,d,p] — в слоте у класса есть ЛЮБОЙ урок
                if g in grade_max_lessons_per_day:
                    model.Add(day_load <= grade_max_lessons_per_day[g])

    # (6b) Предметы, запрещённые последними уроками по параллелям
    # версия после рефакторинга
    # Идея: если запрещённый предмет стоит в периоде p, то ПОСЛЕ него в этот день должен быть хотя бы один любой урок. Иначе — запрещаем.
    # (6b) Предметы, запрещённые последними уроками по параллелям
    # Если урок запрещённого предмета s стоит в периоде p, то после него в этот день должен быть хотя бы ещё один урок (любой).
    if optimizationGoals.subjects_not_last_lesson_optimization:
        for c in C:
            g = class_grades.get(c)

            # NEW: полностью отключаем правило для начальной школы (1–4 классы)
            if g is None or g in {1, 2, 3, 4}:
                continue

            # Если для этой параллели нет запрещённых предметов — ничего не делаем и не плодим переменные
            banned_subjects = subjects_not_last_lesson.get(g, set())
            if not banned_subjects:
                continue

            # Служебные флаги "этот слот является последним уроком дня" — только для нужных параллелей
            day_is_last_lesson = {
                (d, p): model.NewBoolVar(f'is_last_{c}_{d}_{p}')
                for d, p in itertools.product(D, P)
            }
            for d in D:
                lessons_on_day = [y[c, d, p] for p in P]
                for p_idx, p in enumerate(P):
                    # p — последний, если в p есть урок и ПОСЛЕ него уроков нет
                    no_lessons_after = model.NewBoolVar(f'no_lessons_after_{c}_{d}_{p}')
                    lessons_after = [lessons_on_day[i] for i in range(p_idx + 1, len(P))]
                    if lessons_after:
                        # no_lessons_after <=> (OR(lessons_after) == 0)
                        model.AddBoolOr([l.Not() for l in lessons_after]).OnlyEnforceIf(no_lessons_after)
                        model.AddBoolOr(lessons_after).OnlyEnforceIf(no_lessons_after.Not())
                    else:  # последний период дня
                        model.Add(no_lessons_after == 1)

                    # day_is_last_lesson[d, p] <=> (lessons_on_day[p_idx] AND no_lessons_after)
                    model.AddBoolAnd([lessons_on_day[p_idx], no_lessons_after]).OnlyEnforceIf(day_is_last_lesson[d, p])
                    model.AddImplication(day_is_last_lesson[d, p], lessons_on_day[p_idx])
                    model.AddImplication(day_is_last_lesson[d, p], no_lessons_after)

            # Запрещённые предметы не могут стоять в последнем слоте дня
            for s in banned_subjects:
                if s in splitS:
                    for g_id, d, p in itertools.product(G, D, P):
                        var = z.get((c, s, g_id, d, p), false_var)
                        model.AddImplication(var, day_is_last_lesson[d, p].Not())
                else:
                    for d, p in itertools.product(D, P):
                        var = x.get((c, s, d, p), false_var)
                        model.AddImplication(var, day_is_last_lesson[d, p].Not())

    # (6c) Правила для начальной школы (2-4 классы)
    for c in C:
        g = class_grades.get(c)
        if g in {2, 3, 4}:
            # Английский только на разрешённых уроках (если предмет указан в data.english_subject_name)
            if data.english_subject_name:
                subj = data.english_subject_name
                if subj in splitS:
                    for g_id in G:
                        for d, p in itertools.product(D, P):
                            if p not in english_periods and (c, subj, g_id, d, p) in z:
                                model.Add(z[c, subj, g_id, d, p] == 0)
                else:
                    for d, p in itertools.product(D, P):
                        if p not in english_periods and (c, subj, d, p) in x:
                            model.Add(x[c, subj, d, p] == 0)

            # Запрет двух одинаковых предметов подряд
            for s in set(S) - paired: # Исключаем paired_subjects из этого правила
                for d in D:
                    for idx in range(len(P) - 1):
                        p1 = P[idx]
                        p2 = P[idx + 1]
                        if s in splitS:
                            v1 = is_subj_taught.get((c, s, d, p1), false_var)
                            v2 = is_subj_taught.get((c, s, d, p2), false_var)
                        else:
                            v1 = x.get((c, s, d, p1), false_var)
                            v2 = x.get((c, s, d, p2), false_var)
                        model.Add(v1 + v2 <= 1)

    # (6d) Максимум подряд идущих дней с предметом по параллелям
    # grade_subject_max_consecutive_days = {5: {"PE": 2, "eng": 2}}
    for grade, limits in grade_subject_max_consecutive_days.items():
        for c in C:
            if class_grades.get(c) == grade:
                for subj, limit in limits.items():
                    # limits.items = {"PE": 2, "eng": 2}
                    # subj, limit = "PE": 2
                    day_flag = {}
                    for d in D:
                        v = model.NewBoolVar(f'{subj}_day_{c}_{d}')
                        day_flag[d] = v
                        lessons = []
                        if subj in splitS:
                            for g_id in G:
                                for p in P:
                                    if (c, subj, g_id, d, p) in z:
                                        lessons.append(z[c, subj, g_id, d, p])
                        else:
                            for p in P:
                                if (c, subj, d, p) in x:
                                    lessons.append(x[c, subj, d, p])
                        if lessons:
                            model.AddMaxEquality(v, lessons)
                        else:
                            model.Add(v == 0)
                    # Ограничение на максимальное количество подряд идущих дней с предметом
                    # Если limit = 2, то сумма day_flag для 3 подряд идущих дней не должна превышать 2.
                    for i in range(len(D) - limit):
                        model.Add(sum(day_flag[D[j]] for j in range(i, i + limit + 1)) <= limit)

    # ------------------------- 3.3) ДОПОЛНИТЕЛЬНЫЕ ОПЦИИ (НЕОБЯЗ.) -------------------------

    # (A) Синхронность подгрупп для некоторых сплит‑предметов
    # Опциональный параметр `must_sync_split_subjects` в `InputData`
    # позволяет указать предметы, подгруппы которых должны идти синхронно.
    # Например, если `must_sync_split_subjects = {"eng", "cs"}`,
    # то для английского и информатики все подгруппы класса должны
    # либо иметь урок в данном слоте, либо не иметь его.
    # Это полезно, когда, например, все подгруппы по английскому
    # занимаются одновременно, но с разными учителями.
    must_sync = set(getattr(data, 'must_sync_split_subjects', [])) & splitS
    if must_sync:
        for s in must_sync:
            for c, d, p in itertools.product(C, D, P):
                # Устанавливаем равенство переменных `z` для всех подгрупп `g1` и `g2`
                # одного и того же сплит-предмета `s` в одном и том же слоте `(c, d, p)`.
                # Это означает, что если одна подгруппа имеет урок, то и другая должна.
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
    #                         до и включая период p. Например, если у класса
    #                         «7А» в понедельник занятия в слотах [2,3,5], то
    #                         prefix_class[7А,Пн,1] = 0,
    #                         prefix_class[7А,Пн,2] = 1,
    #                         prefix_class[7А,Пн,3] = 1,
    #                         prefix_class[7А,Пн,4] = 1,
    #                         prefix_class[7А,Пн,5] = 1, последующие слоты = 1.
    # suffix_class[c,d,p]  — хотя бы один урок у класса c в день d в слотах
    #                         начиная с p и далее. При тех же занятиях
    #                         suffix_class[7А,Пн,1] = 1,
    #                         suffix_class[7А,Пн,2] = 1,
    #                         suffix_class[7А,Пн,3] = 1,
    #                         suffix_class[7А,Пн,4] = 1,
    #                         suffix_class[7А,Пн,5] = 1, последующие слоты = 0.
    # inside_class[c,d,p]  — слот находится между первым и последним
    #                         уроком класса c в день d (включая сами уроки).
    #                         Например, если у класса «7А» в понедельник
    #                         занятия стоят в слотах [2,3,5], то
    #                         inside_class[7А,Пн,1] = 0,
    #                         inside_class[7А,Пн,2] = 1,
    #                         inside_class[7А,Пн,3] = 1,
    #                         inside_class[7А,Пн,4] = 1,
    #                         inside_class[7А,Пн,5] = 1, остальные = 0.
    #                         Все значения 1 образуют «конверт», который далее
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
    sum_inside_class = sum(
        inside_class[c, d, p]
        for c in C if class_grades.get(c) not in {2, 3, 4}
        for d in D for p in P
    )

    # --- Учителя -----------------------------------------------------
    # Аналогичные переменные для каждого учителя. Здесь вместо y мы
    # используем подготовленный флаг teacher_busy[t,d,p].
    prefix_teacher: Dict[Tuple[Hashable, Hashable, Hashable], cp_model.IntVar] = {}
    suffix_teacher: Dict[Tuple[Hashable, Hashable, Hashable], cp_model.IntVar] = {}
    inside_teacher: Dict[Tuple[Hashable, Hashable, Hashable], cp_model.IntVar] = {}

    sum_inside_teacher = zero_var
    if optimizationGoals.teacher_slot_optimization:
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
    # y[c,d,p] — в слоте у класса есть ЛЮБОЙ урок
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

    # попытка провести спаренные предметы
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

    # Формируем единую целевую функцию как взвешенную сумму всех компонентов.
    # Лексикографическая оптимизация отключена.
    objective = (
        alpha_runs_teacher * sum_inside_teacher +  # Окна у учителей
        alpha_runs * sum_inside_class +            # Окна у классов
        early_term +                               # Предпочтение ранних слотов
        balance_term +                             # Баланс нагрузки по дням
        tail_term +                                # Штраф за уроки после last_ok_period
        pairing_term                               # Штраф за одиночные "спаренные" уроки
    )
    model.Minimize(objective)

    # --------------------------- 3.5) ЗАПУСК РЕШАТЕЛЯ ---------------------------

    solver = cp_model.CpSolver()
    solver.parameters.log_search_progress = log
    solver.parameters.num_search_workers = getattr(weights, 'num_search_workers', 20)
    if getattr(weights, 'random_seed', None) is not None:
        solver.parameters.random_seed = int(weights.random_seed)
    if getattr(weights, 'time_limit_s', None):
        solver.parameters.max_time_in_seconds = float(weights.time_limit_s)
    # Чуть отпускаем разрыв по умолчанию — ускоряет черновики
    solver.parameters.relative_gap_limit = getattr(weights, 'relative_gap_limit', 0.05)

    print("Начинаем решение...")

    # Запускаем решатель с единой целевой функцией
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
        
        if PRINT_TIMETABLE_TO_CONSOLE:
            print("\n--- Расписание в консоли ---")
            print_schedule_to_console(data, solution_maps, display_maps)

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
        PRINT_TIMETABLE_TO_CONSOLE=OptimizationGoals().print_timetable_to_console, # <--- Установите True для вывода в консоль
        display_maps=display_maps

    )
