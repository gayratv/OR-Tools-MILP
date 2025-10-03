import itertools
# from typing import Dict, List, Union
from ortools.sat.python import cp_model
from ..data_types.input_data import InputData


def calculate_teacher_windows(data: InputData,
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


def validate_input_data(data: InputData) -> None:
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

    # (5d) учительская вместимость на «узких» периодах для английского в начальной школе
    # Проверяем: часы английского у учителя в 2–4 классах <= кол-ва доступных слотов на english_periods
    if eng_name and english_periods:
        allowed_p = {p for p in english_periods if p in period_set}
        if allowed_p:
            from collections import defaultdict
            # Требование по часам английского в начальной школе на каждого учителя
            teacher_elem_eng_hours = defaultdict(int)

            # НЕДЕЛИМЫЕ (на случай, если английский не сплит)
            for (c, s), h in getattr(data, 'plan_hours', {}).items():
                if h > 0 and s == eng_name and class_grade.get(c) in {2, 3, 4}:
                    t = getattr(data, 'assigned_teacher', {}).get((c, s))
                    if t in teacher_set:
                        teacher_elem_eng_hours[t] += h

            # СПЛИТ-ПРЕДМЕТ (обычный случай: английский сплит у 2–4 классов)
            for (c, s, g_id), h in getattr(data, 'subgroup_plan_hours', {}).items():
                if h > 0 and s == eng_name and class_grade.get(c) in {2, 3, 4}:
                    t = getattr(data, 'subgroup_assigned_teacher', {}).get((c, s, g_id))
                    if t in teacher_set:
                        teacher_elem_eng_hours[t] += h

            # Ёмкость учителя по разрешённым периодам: суммируем по дням, исключая days_off и запрещённые слоты учителя
            from collections import defaultdict as _dd
            t_forb = _dd(set)  # teacher -> {(day, period)}
            for t, slots in getattr(data, 'teacher_forbidden_slots', {}).items():
                for d, p in slots or []:
                    t_forb[t].add((d, p))
            t_days_off = {t: set(v) for t, v in getattr(data, 'days_off', {}).items()}

            for t, req in teacher_elem_eng_hours.items():
                cap = 0
                for d in days:
                    if d in t_days_off.get(t, set()):
                        continue
                    forb_count = sum(1 for p in allowed_p if (d, p) in t_forb.get(t, set()))
                    cap += max(0, len(allowed_p) - forb_count)
                if req > cap:
                    add_err(
                        f"Невыполнимо: учитель '{t}' имеет {req} ч/нед английского в начальной школе (2–4 кл.), "
                        f"но доступная недельная вместимость по разрешённым периодам {sorted(allowed_p)} равна {cap} "
                        f"(учтены days_off и teacher_forbidden_slots учителя). "
                        f"Уменьшите нагрузку, перераспределите подгруппы или расширьте elementary_english_periods."
                    )


    # ---------- Финал ----------
    if errors:
        raise ValueError("Обнаружены проблемы во входных данных:\n  - " + "\n  - ".join(errors))
