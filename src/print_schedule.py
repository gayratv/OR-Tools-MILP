"""
Pretty-printers for timetables using InputData + solution vars.
Теперь кроме расписаний по классам/учителям есть и сводка нагрузки.
"""
from typing import Dict, Tuple
import pulp
import pandas as pd
import openpyxl
from openpyxl.styles import Font, Alignment

# Импортируем функцию для создания подключения к БД из access_loader
from access_loader import _create_db_engine
from input_data_OptimizationWeights_types import InputData


def _val(var) -> float:
    if var is None:
        return 0.0
    # pulp.value(var) может вернуть None, если значение переменной не определено
    val = pulp.value(var)
    return float(val) if val is not None else 0.0


def print_by_classes(data: InputData,
                     x: Dict[Tuple, pulp.LpVariable],
                     z: Dict[Tuple, pulp.LpVariable],
                     display_maps: Dict[str, Dict[str, str]] = None) -> None:
    """Печать расписания по классам"""
    days, periods, classes, subjects = data.days, data.periods, data.classes, data.subjects
    split_subjects = set(data.split_subjects)
    if display_maps is None:
        display_maps = {}

    # Извлекаем словари для удобства, с пустым словарем по умолчанию
    # class_map = display_maps.get("class_names", {}) # Пока не загружается
    subject_map = display_maps.get("subject_names", {})
    teacher_map = display_maps.get("teacher_names", {})

    print("\n================ РАСПИСАНИЕ ПО КЛАССАМ ================")
    for c in classes:
        # class_name_rus = class_map.get(c, c)
        print(f"\n=== Класс {c} ===") # Используем техническое имя, т.к. карты для классов нет
        total_lessons = 0
        for d in days:
            row = []
            for p in periods:
                cell = None
                # non-split
                for s in subjects:
                    if s in split_subjects:
                        continue
                    if _val(x.get((c, s, d, p))) > 0.5:
                        t_eng = data.assigned_teacher.get((c, s), "БЕЗ_УЧИТЕЛЯ")
                        s_rus = subject_map.get(s, s)
                        t_rus = teacher_map.get(t_eng, t_eng)
                        cell = f"{p}: {s_rus} ({t_rus})"
                        total_lessons += 1
                        break
                # split
                if cell is None:
                    pieces = []
                    for s in subjects:
                        if s not in split_subjects:
                            continue
                        for g in data.subgroup_ids:
                            if _val(z.get((c, s, g, d, p))) > 0.5:
                                t_eng = data.subgroup_assigned_teacher.get((c, s, g), "БЕЗ_УЧИТЕЛЯ")
                                s_rus = subject_map.get(s, s)
                                t_rus = teacher_map.get(t_eng, t_eng)
                                pieces.append(f"{s_rus}[g{g}::{t_rus}]")
                                total_lessons += 1
                    if pieces:
                        cell = f"{p}: " + "+".join(pieces)
                row.append(cell or f"{p}: —")
            print(f"{d} | " + ", ".join(row))
        print(f"Итого уроков за неделю (считая подгруппы): {total_lessons}")


def print_by_teachers(data: InputData,
                      x: Dict[Tuple, pulp.LpVariable],
                      z: Dict[Tuple, pulp.LpVariable],
                      display_maps: Dict[str, Dict[str, str]] = None) -> None:
    """Печать расписания по учителям"""
    days, periods, teachers = data.days, data.periods, data.teachers
    if display_maps is None:
        display_maps = {}
    # class_map = display_maps.get("class_names", {})
    subject_map = display_maps.get("subject_names", {})
    teacher_map = display_maps.get("teacher_names", {})

    print("\n================ РАСПИСАНИЕ ПО УЧИТЕЛЯМ ================")
    for t in teachers:
        # Используем русское имя учителя
        teacher_name_rus = teacher_map.get(t, t)
        print(f"\n=== Учитель {teacher_name_rus} ===")
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
                        # c_rus = class_map.get(c, c)
                        s_rus = subject_map.get(s, s)
                        cell = f"{p}: {c} — {s_rus}"
                        total += 1
                        break
                # split
                if cell is None:
                    pieces = []
                    for (c, s, g), tt in data.subgroup_assigned_teacher.items():
                        if tt != t:
                            continue
                        varz = z.get((c, s, g, d, p))
                        if varz is not None and _val(varz) > 0.5:
                            # c_rus = class_map.get(c, c)
                            s_rus = subject_map.get(s, s)
                            pieces.append(f"{c} — {s_rus}[g{g}]")
                            total += 1
                    if pieces:
                        cell = f"{p}: " + " + ".join(pieces)
                row.append(cell or f"{p}: —")
            print(f"{d} | " + ", ".join(row))
        print(f"Итого уроков за неделю: {total}")


def summary_load(data: InputData,
                 x: Dict[Tuple, pulp.LpVariable],
                 z: Dict[Tuple, pulp.LpVariable],
                 display_maps: Dict[str, Dict[str, str]] = None) -> None:
    """Сводка по нагрузке для классов и учителей (оптимизированная):
       - общее количество
       - распределение по дням
       - подсчет 'окон' у учителей
       - предупреждения о перегрузках и перекосах
    """
    print("\n================ СВОДКА НАГРУЗКИ ================")
    if display_maps is None:
        display_maps = {}
    # class_map = display_maps.get("class_names", {})
    # subject_map = display_maps.get("subject_names", {})
    teacher_map = display_maps.get("teacher_names", {})

    # --- Предварительный расчет --- 
    teacher_load_per_day = {t: {d: 0 for d in data.days} for t in data.teachers}
    class_load_per_day = {c: {d: 0 for d in data.days} for c in data.classes}
    teacher_busy_periods = {t: {d: [] for d in data.days} for t in data.teachers}

    # не-делимые предметы
    for (c, s, d, p), var in x.items():
        if _val(var) > 0.5:
            class_load_per_day[c][d] += 1
            teacher = data.assigned_teacher.get((c, s))
            if teacher:
                teacher_load_per_day[teacher][d] += 1
                teacher_busy_periods[teacher][d].append(p)

    # делимые предметы
    for (c, s, g, d, p), var in z.items():
        if _val(var) > 0.5:
            class_load_per_day[c][d] += 1
            teacher = data.subgroup_assigned_teacher.get((c, s, g))
            if teacher:
                teacher_load_per_day[teacher][d] += 1
                teacher_busy_periods[teacher][d].append(p)

    # --- по классам ---
    print("\n--- Классы ---")
    for c in data.classes:
        per_day = class_load_per_day[c]
        total = sum(per_day.values())
        avg = total / len(data.days) if data.days else 0

        # class_name_rus = class_map.get(c, c)
        print(f"{c}: {total} занятий/подгрупповых слотов за неделю (≈{avg:.1f}/день)") # Используем техническое имя
        warn_days = [d for d, v in per_day.items() if v > 7]
        if warn_days:
            print(f"   ⚠️ Перегрузка {c} в днях {', '.join(warn_days)} (больше 7 уроков)")
        skew = [d for d, v in per_day.items() if abs(v - avg) > 0.3 * avg and avg > 0]
        if skew:
            print(f"   ⚠️ Перекос нагрузки в днях: {', '.join(skew)} (сильно отличается от среднего {avg:.1f})")
        print("   по дням:", ", ".join(f"{d}:{v}" for d, v in per_day.items()))

    # --- по учителям ---
    print("\n--- Учителя ---")
    for t in data.teachers:
        per_day = teacher_load_per_day[t]
        total = sum(per_day.values())
        avg = total / len(data.days) if data.days else 0

        teacher_name_rus = teacher_map.get(t, t)
        print(f"{teacher_name_rus}: {total} занятий за неделю (лимит {data.teacher_weekly_cap}, ≈{avg:.1f}/день)")
        if total > data.teacher_weekly_cap:
            print(f"   ⚠️ {teacher_name_rus} перегружен! Лимит {data.teacher_weekly_cap}, фактически {total}")
        
        # Окна
        total_windows = 0
        windows_details = []
        for d in data.days:
            busy_periods = sorted(teacher_busy_periods[t][d])
            if len(busy_periods) > 1:
                day_windows = 0
                for i in range(len(busy_periods) - 1):
                    day_windows += busy_periods[i+1] - busy_periods[i] - 1
                if day_windows > 0:
                    total_windows += day_windows
                    windows_details.append(f"{d}:{day_windows}")
        
        if total_windows > 0:
            print(f"   Окна за неделю: {total_windows} ({', '.join(windows_details)})")
            if total_windows > 5: # Условный лимит
                print(f"   ⚠️  У {teacher_name_rus} много окон (больше 5)")

        warn_days = [d for d, v in per_day.items() if v > 8]
        if warn_days:
            print(f"   ⚠️ Перегрузка {teacher_name_rus} в днях {', '.join(warn_days)} (больше 8 уроков)")
        skew = [d for d, v in per_day.items() if abs(v - avg) > 0.3 * avg and avg > 0]
        if skew:
            print(f"   ⚠️ Перекос нагрузки в днях: {', '.join(skew)} (сильно отличается от среднего {avg:.1f})")
        print("   по дням:", ", ".join(f"{d}:{v}" for d, v in per_day.items()))


def export_full_schedule_to_excel(filename: str,
                                  data: InputData,
                                  x: Dict[Tuple, pulp.LpVariable],
                                  z: Dict[Tuple, pulp.LpVariable],
                                  display_maps: Dict[str, Dict[str, str]] = None) -> None:
    """Экспорт полного расписания и сводки в Excel-файл"""
    wb = openpyxl.Workbook()
    bold_font = Font(bold=True)
    if display_maps is None:
        display_maps = {}

    # Извлекаем словари для удобства
    # В access_loader.py нет загрузки для class_names, поэтому пока закомментировано
    # class_map = display_maps.get("class_names", {}) 
    subject_map = display_maps.get("subject_names", {})
    teacher_map = display_maps.get("teacher_names", {})

    # --- Лист: расписание по классам ---
    ws_classes = wb.active
    ws_classes.title = "Классы_расписание"
    for c in data.classes:
        # class_rus = class_map.get(c, c)
        ws_classes.append([f"Класс {c}"]) # Используем техническое имя, т.к. карты для классов нет
        header = ["День"] + [f"Урок {p}" for p in data.periods]
        ws_classes.append(header)
        for d in data.days:
            row = [d]
            for p in data.periods:
                cell = None
                # non-split
                for s in data.subjects:
                    if s in data.split_subjects: continue
                    if _val(x.get((c, s, d, p))) > 0.5:
                        t_eng = data.assigned_teacher.get((c, s), "БЕЗ_УЧИТЕЛЯ")
                        s_rus = subject_map.get(s, s)
                        t_rus = teacher_map.get(t_eng, t_eng)
                        cell = f"{s_rus} ({t_rus})"
                        break
                # split
                if cell is None:
                    pieces = []
                    for s in data.subjects:
                        if s not in data.split_subjects: continue
                        for g in data.subgroup_ids:
                            if _val(z.get((c, s, g, d, p))) > 0.5:
                                t_eng = data.subgroup_assigned_teacher.get((c, s, g), "БЕЗ_УЧИТЕЛЯ")
                                s_rus = subject_map.get(s, s)
                                t_rus = teacher_map.get(t_eng, t_eng)
                                pieces.append(f"{s_rus}[g{g}::{t_rus}]")
                    if pieces:
                        cell = "+".join(pieces)
                row.append(cell or "—")
            ws_classes.append(row)
        ws_classes.append([])

    # --- Лист: расписание по учителям ---
    ws_teachers = wb.create_sheet("Учителя_расписание")
    for t in data.teachers:
        teacher_name_rus = teacher_map.get(t, t)
        ws_teachers.append([f"Учитель {teacher_name_rus}"])
        header = ["День"] + [f"Урок {p}" for p in data.periods]
        ws_teachers.append(header)
        for d in data.days:
            row = [d]
            for p in data.periods:
                cell = None
                # non-split
                for (c, s), tt in data.assigned_teacher.items():
                    if tt != t: continue
                    if _val(x.get((c, s, d, p))) > 0.5:
                        s_rus = subject_map.get(s, s)
                        cell = f"{c}-{s_rus}"
                        break
                # split
                if cell is None:
                    pieces = []
                    for (c, s, g), tt in data.subgroup_assigned_teacher.items():
                        if tt != t: continue
                        if _val(z.get((c, s, g, d, p))) > 0.5:
                            s_rus = subject_map.get(s, s)
                            pieces.append(f"{c}-{s_rus}[g{g}]")
                    if pieces:
                        cell = " + ".join(pieces)
                row.append(cell or "—")
            ws_teachers.append(row)
        ws_teachers.append([])

    # --- Лист: Сводка нагрузки ---
    ws_summary = wb.create_sheet("Сводка_нагрузки")
    teacher_load_per_day = {t: {d: 0 for d in data.days} for t in data.teachers}
    class_load_per_day = {c: {d: 0 for d in data.days} for c in data.classes}
    teacher_busy_periods = {t: {d: [] for d in data.days} for t in data.teachers}

    for (c, s, d, p), var in x.items():
        if _val(var) > 0.5:
            class_load_per_day[c][d] += 1
            teacher = data.assigned_teacher.get((c, s))
            if teacher:
                teacher_load_per_day[teacher][d] += 1
                teacher_busy_periods[teacher][d].append(p)

    for (c, s, g, d, p), var in z.items():
        if _val(var) > 0.5:
            class_load_per_day[c][d] += 1
            teacher = data.subgroup_assigned_teacher.get((c, s, g))
            if teacher:
                teacher_load_per_day[teacher][d] += 1
                teacher_busy_periods[teacher][d].append(p)

    ws_summary.append(["Сводка по классам"]) 
    ws_summary.cell(ws_summary.max_row, 1).font = bold_font
    header = ["Класс", "Всего уроков", "Среднее в день"] + data.days + ["Предупреждения"]
    ws_summary.append(header)

    for c in data.classes:
        # class_rus = class_map.get(c, c)
        per_day = class_load_per_day[c]
        total = sum(per_day.values())
        avg = total / len(data.days) if data.days else 0
        warnings = []
        warn_days = [d for d, v in per_day.items() if v > 7]
        if warn_days: warnings.append(f"Перегрузка: {', '.join(warn_days)}")
        skew = [d for d, v in per_day.items() if abs(v - avg) > 0.3 * avg and avg > 0]
        if skew: warnings.append(f"Перекос: {', '.join(skew)}")
        row = [c, total, f"{avg:.1f}"] + [per_day[d] for d in data.days] + [", ".join(warnings)] # Используем техническое имя
        ws_summary.append(row)

    ws_summary.append([])
    ws_summary.append(["Сводка по учителям"]) 
    ws_summary.cell(ws_summary.max_row, 1).font = bold_font
    header = ["Учитель", "Всего уроков", "Лимит", "Среднее в день", "Окна"] + data.days + ["Предупреждения"]
    ws_summary.append(header)

    for t in data.teachers:
        teacher_name_rus = teacher_map.get(t, t)
        per_day = teacher_load_per_day[t]
        total = sum(per_day.values())
        avg = total / len(data.days) if data.days else 0
        
        total_windows = 0
        windows_details = []
        for d in data.days:
            busy_periods = sorted(teacher_busy_periods[t][d])
            if len(busy_periods) > 1:
                day_windows = sum(busy_periods[i+1] - busy_periods[i] - 1 for i in range(len(busy_periods) - 1))
                if day_windows > 0: 
                    total_windows += day_windows
                    windows_details.append(f"{d}:{day_windows}")

        warnings = []
        if total > data.teacher_weekly_cap: warnings.append(f"Перегрузка ({total}/{data.teacher_weekly_cap})")
        if total_windows > 5: warnings.append(f"Много окон ({total_windows})")
        warn_days = [d for d, v in per_day.items() if v > 8]
        if warn_days: warnings.append(f"Перегрузка по дням: {', '.join(warn_days)}")
        skew = [d for d, v in per_day.items() if abs(v - avg) > 0.3 * avg and avg > 0]
        if skew: warnings.append(f"Перекос: {', '.join(skew)}")

        row = [teacher_name_rus, total, data.teacher_weekly_cap, f"{avg:.1f}", f"{total_windows} ({', '.join(windows_details)})"] + [per_day[d] for d in data.days] + [", ".join(warnings)]
        ws_summary.append(row)

    # --- Авто-ширина колонок и стиль ---
    for ws in wb.worksheets:
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except: pass
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column].width = adjusted_width
        for row in ws.iter_rows(min_row=1, max_row=ws.max_row):
            for cell in row:
                if cell.font.bold:
                    cell.alignment = Alignment(horizontal='center', vertical='center')

    wb.save(filename)
    print(f"Полное расписание и сводка сохранены в {filename}")


def export_raw_data_to_excel(filename: str, db_path: str) -> None:
    """
    Добавляет в существующий Excel-файл листы с "сырыми" данными из таблиц MS Access.

    Args:
        filename: Путь к существующему Excel-файлу, куда будут добавлены листы.
        db_path: Путь к файлу базы данных MS Access.
    """
    if not db_path:
        print("INFO: Путь к базе данных не указан, экспорт сырых данных пропущен.")
        return

    # Список таблиц/представлений для экспорта.
    # Ключ - имя таблицы/представления в Access, значение - имя листа в Excel.
    tables_to_export = {
        "з_excel_предметы": "предметы",
        "з_excel_учителя": "учителя",
        # "v_subgroup_plan_hours": "Нагрузка_подгрупп",
        # "v_subgroup_assigned_teacher": "Назначения_подгрупп",
        # "v_days_off": "Выходные_учителей",
        # "v_forbidden_slots": "Запреты_слотов",
        # "v_сompatible_pairs": "Совместимые_пары",
    }

    try:
        engine = _create_db_engine(db_path)
        with pd.ExcelWriter(filename, engine='openpyxl', mode='a') as writer:
            for table_name, sheet_name in tables_to_export.items():
                print(f"  - Экспорт '{table_name}' в лист '{sheet_name}'...")
                df = pd.read_sql(f"SELECT * FROM {table_name}", engine)
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        print(f"Сырые данные из Access добавлены в {filename}")
    except Exception as e:
        print(f"ОШИБКА: Не удалось экспортировать сырые данные из Access. Причина: {e}")
