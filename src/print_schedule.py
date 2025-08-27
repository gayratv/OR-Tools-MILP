"""
Pretty-printers for timetables using InputData + solution vars.
Теперь кроме расписаний по классам/учителям есть и сводка нагрузки.
"""
from typing import Dict, Tuple
import pulp
import openpyxl
from openpyxl.styles import Font

from input_data import InputData


def _val(var) -> float:
    return float(pulp.value(var)) if var is not None else 0.0


def print_by_classes(data: InputData,
                     x: Dict[Tuple, pulp.LpVariable],
                     z: Dict[Tuple, pulp.LpVariable]) -> None:
    """Печать расписания по классам"""
    days, periods, classes, subjects = data.days, data.periods, data.classes, data.subjects
    split_subjects = set(data.split_subjects)

    print("\n================ РАСПИСАНИЕ ПО КЛАССАМ ================")
    for c in classes:
        print(f"\n=== Класс {c} ===")
        total_lessons = 0
        for d in days:
            row = []
            for p in periods:
                cell = None
                # non-split
                for s in subjects:
                    if s in split_subjects:
                        continue
                    var = x.get((c, s, d, p))
                    if var is not None and _val(var) > 0.5:
                        t = data.assigned_teacher[(c, s)]
                        cell = f"{p}: {s} ({t})"
                        total_lessons += 1
                        break
                # split
                if cell is None:
                    pieces = []
                    for s in subjects:
                        if s not in split_subjects:
                            continue
                        for g in data.subgroup_ids:
                            varz = z.get((c, s, g, d, p))
                            if varz is not None and _val(varz) > 0.5:
                                t = data.subgroup_assigned_teacher[(c, s, g)]
                                pieces.append(f"{s}[g{g}::{t}]")
                                total_lessons += 1
                    if pieces:
                        cell = f"{p}: " + "+".join(pieces)
                row.append(cell or f"{p}: —")
            print(f"{d} | " + ", ".join(row))
        print(f"Итого уроков за неделю (считая подгруппы): {total_lessons}")


def print_by_teachers(data: InputData,
                      x: Dict[Tuple, pulp.LpVariable],
                      z: Dict[Tuple, pulp.LpVariable]) -> None:
    """Печать расписания по учителям"""
    days, periods, teachers = data.days, data.periods, data.teachers

    print("\n================ РАСПИСАНИЕ ПО УЧИТЕЛЯМ ================")
    for t in teachers:
        print(f"\n=== Учитель {t} ===")
        total = 0
        for d in days:
            row = []
            for p in periods:
                cell = None
                # non-split
                for (c, s), tt in data.assigned_teacher.items():
                    if tt != t:
                        continue
                    var = x.get((c, s, d, p))
                    if var is not None and _val(var) > 0.5:
                        cell = f"{p}: {c} — {s}"
                        total += 1
                        break
                if cell is None:
                    # split
                    for (c, s, g), tt in data.subgroup_assigned_teacher.items():
                        if tt != t:
                            continue
                        varz = z.get((c, s, g, d, p))
                        if varz is not None and _val(varz) > 0.5:
                            cell = f"{p}: {c} — {s}[g{g}]"
                            total += 1
                            break
                row.append(cell or f"{p}: —")
            print(f"{d} | " + ", ".join(row))
        print(f"Итого уроков за неделю: {total}")


def summary_load(data: InputData,
                 x: Dict[Tuple, pulp.LpVariable],
                 z: Dict[Tuple, pulp.LpVariable]) -> None:
    """Сводка по нагрузке для классов и учителей:
       - общее количество
       - распределение по дням
       - предупреждения о перегрузках
       - сравнение со средним по дням
    """
    print("\n================ СВОДКА НАГРУЗКИ ================")

    # --- по классам ---
    print("\n--- Классы ---")
    for c in data.classes:
        total = 0
        per_day = {d: 0 for d in data.days}
        # non-split
        for (cc, s), _ in data.assigned_teacher.items():
            if cc == c:
                for d in data.days:
                    for p in data.periods:
                        val = _val(x[(cc, s, d, p)])
                        total += val
                        per_day[d] += val
        # split
        for (cc, s, g), _ in data.subgroup_assigned_teacher.items():
            if cc == c:
                for d in data.days:
                    for p in data.periods:
                        val = _val(z[(cc, s, g, d, p)])
                        total += val
                        per_day[d] += val

        avg = total / len(data.days) if data.days else 0
        print(f"{c}: {int(total)} занятий/подгрупповых слотов за неделю (≈{avg:.1f}/день)")
        warn_days = [d for d,v in per_day.items() if v > 7]
        if warn_days:
            print(f"   ⚠️ Перегрузка {c} в днях {', '.join(warn_days)} (больше 7 уроков)")
        # проверка на перекосы от среднего (>30% отклонение)
        skew = [d for d,v in per_day.items() if abs(v - avg) > 0.3*avg and avg > 0]
        if skew:
            print(f"   ⚠️ Перекос нагрузки в днях: {', '.join(skew)} (сильно отличается от среднего {avg:.1f})")
        print("   по дням:", ", ".join(f"{d}:{int(per_day[d])}" for d in data.days))

    # --- по учителям ---
    print("\n--- Учителя ---")
    for t in data.teachers:
        total = 0
        per_day = {d: 0 for d in data.days}
        # non-split
        for (c, s), tt in data.assigned_teacher.items():
            if tt == t:
                for d in data.days:
                    for p in data.periods:
                        val = _val(x[(c, s, d, p)])
                        total += val
                        per_day[d] += val
        # split
        for (c, s, g), tt in data.subgroup_assigned_teacher.items():
            if tt == t:
                for d in data.days:
                    for p in data.periods:
                        val = _val(z[(c, s, g, d, p)])
                        total += val
                        per_day[d] += val

        avg = total / len(data.days) if data.days else 0
        print(f"{t}: {int(total)} занятий за неделю (лимит {data.teacher_weekly_cap}, ≈{avg:.1f}/день)")
        if total > data.teacher_weekly_cap:
            print(f"   ⚠️ {t} перегружен! Лимит {data.teacher_weekly_cap}, фактически {int(total)}")
        warn_days = [d for d,v in per_day.items() if v > 8]
        if warn_days:
            print(f"   ⚠️ Перегрузка {t} в днях {', '.join(warn_days)} (больше 8 уроков)")
        skew = [d for d,v in per_day.items() if abs(v - avg) > 0.3*avg and avg > 0]
        if skew:
            print(f"   ⚠️ Перекос нагрузки в днях: {', '.join(skew)} (сильно отличается от среднего {avg:.1f})")
        print("   по дням:", ", ".join(f"{d}:{int(per_day[d])}" for d in data.days))

def export_full_schedule_to_excel(filename: str,
                                  data: InputData,
                                  x: Dict[Tuple, pulp.LpVariable],
                                  z: Dict[Tuple, pulp.LpVariable]) -> None:
    """Экспорт полного расписания в Excel: отдельные листы для классов и учителей"""
    wb = openpyxl.Workbook()

    # --- Лист: расписание по классам ---
    ws_classes = wb.active
    ws_classes.title = "Классы_расписание"
    # для каждого класса вставляем блок
    for c in data.classes:
        ws_classes.append([f"Класс {c}"])
        header = ["День"] + [f"Урок {p}" for p in data.periods]
        ws_classes.append(header)
        for d in data.days:
            row = [d]
            for p in data.periods:
                cell = None
                # non-split
                for s in data.subjects:
                    if s in data.split_subjects:
                        continue
                    if _val(x.get((c, s, d, p))) > 0.5:
                        t = data.assigned_teacher[(c, s)]
                        cell = f"{s} ({t})"
                        break
                # split
                if cell is None:
                    pieces = []
                    for s in data.subjects:
                        if s not in data.split_subjects:
                            continue
                        for g in data.subgroup_ids:
                            if _val(z.get((c, s, g, d, p))) > 0.5:
                                t = data.subgroup_assigned_teacher[(c, s, g)]
                                pieces.append(f"{s}[g{g}::{t}]")
                    if pieces:
                        cell = "+".join(pieces)
                row.append(cell or "—")
            ws_classes.append(row)
        ws_classes.append([])  # пустая строка-разделитель

    # --- Лист: расписание по учителям ---
    ws_teachers = wb.create_sheet("Учителя_расписание")
    for t in data.teachers:
        ws_teachers.append([f"Учитель {t}"])
        header = ["День"] + [f"Урок {p}" for p in data.periods]
        ws_teachers.append(header)
        for d in data.days:
            row = [d]
            for p in data.periods:
                cell = None
                # non-split
                for (c, s), tt in data.assigned_teacher.items():
                    if tt != t:
                        continue
                    if _val(x.get((c, s, d, p))) > 0.5:
                        cell = f"{c}-{s}"
                        break
                # split
                if cell is None:
                    for (c, s, g), tt in data.subgroup_assigned_teacher.items():
                        if tt != t:
                            continue
                        if _val(z.get((c, s, g, d, p))) > 0.5:
                            cell = f"{c}-{s}[g{g}]"
                            break
                row.append(cell or "—")
            ws_teachers.append(row)
        ws_teachers.append([])

    # --- стиль заголовков ---
    for ws in [ws_classes, ws_teachers]:
        for row in ws.iter_rows(min_row=2, max_row=2):  # строка заголовков
            for cell in row:
                cell.font = Font(bold=True)

    wb.save(filename)
    print(f"Полное расписание сохранено в {filename}")


