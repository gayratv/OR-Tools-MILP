# pip install ortools
from ortools.sat.python import cp_model

def build_and_solve_timetable(
    classes,                      # список классов: ["5а", "5б", "6а", ...]
    days=5,                       # учебных дней в неделе
    slots_per_day=7,              # максимум уроков в день
    subjects=("math", "cs", "eng", "hist"),
    weekly_hours_per_subject=2,   # одинаково для каждого предмета и класса
    teachers_by_subject=None,     # маппинг предмет -> имя учителя
    time_limit_s=30, workers=8
):
    """
    Формирует и решает расписание:
      - По каждому классу: у каждого предмета ровно weekly_hours_per_subject занятий в неделю
      - В день у класса <= slots_per_day занятий
      - В каждый timeslot у класса не более одного предмета
      - Учитель (по предмету) не может вести одновременно в двух классах

    Возвращает словарь schedule[class][day][slot] = subject | None
    """
    if teachers_by_subject is None:
        teachers_by_subject = {
            "math": "T_math",
            "cs":   "T_cs",
            "eng":  "T_eng",
            "hist": "T_hist",
        }

    model = cp_model.CpModel()

    C = list(classes)
    U = list(subjects)
    D = range(days)
    S = range(slots_per_day)

    # Бинарные переменные: x[c,u,d,s] = 1, если в классе c в день d на слоте s идёт предмет u
    x = {}
    for c in C:
        for u in U:
            for d in D:
                for s in S:
                    x[c, u, d, s] = model.NewBoolVar(f"x[{c},{u},{d},{s}]")

    # 1) Недельный план: для каждого класса и предмета ровно H занятий в неделю
    H = weekly_hours_per_subject
    for c in C:
        for u in U:
            model.Add(
                sum(x[c, u, d, s] for d in D for s in S) == H
            )

    # 2) В каждом классе в каждом слоте не более одного урока
    for c in C:
        for d in D:
            for s in S:
                model.Add(
                    sum(x[c, u, d, s] for u in U) <= 1
                )

    # 3) В каждом классе в каждый день не более slots_per_day уроков
    for c in C:
        for d in D:
            model.Add(
                sum(x[c, u, d, s] for u in U for s in S) <= slots_per_day
            )

    # 4) Ограничение учителя: учитель по предмету u не может вести одновременно в двух классах
    #    => на каждом (day, slot): суммарно по всем классам для предмета u ≤ 1
    for u in U:
        for d in D:
            for s in S:
                model.Add(
                    sum(x[c, u, d, s] for c in C) <= 1
                )

    # (Опционально) 5) Не ставить один и тот же предмет дважды в один день в одном классе
    # Раскомментируйте, если хотите разнести 2 часа по разным дням:
    # for c in C:
    #     for u in U:
    #         for d in D:
    #             model.Add(
    #                 sum(x[c, u, d, s] for s in S) <= 1
    #             )

    # Цель: можно просто feasibility (минимизируем 0),
    # либо добавить мягкие критерии (например, баланс нагрузки).
    model.Minimize(0)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit_s)
    solver.parameters.num_search_workers = int(workers)

    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {"status": str(status), "schedule": None}

    # Формируем читаемое расписание
    schedule = {c: [[None for _ in S] for _ in D] for c in C}
    for c in C:
        for d in D:
            for s in S:
                for u in U:
                    if solver.Value(x[c, u, d, s]) == 1:
                        schedule[c][d][s] = u
                        break

    return {"status": "OK", "schedule": schedule, "subjects": U, "teachers": teachers_by_subject}

# ----------------------
# Пример запуска
if __name__ == "__main__":
    # Классы по умолчанию: по одной "букве" на параллель 5..11
    classes = [f"{g}а" for g in range(5, 12)]
    res = build_and_solve_timetable(classes=classes, time_limit_s=10, workers=8)

    if res["schedule"] is None:
        print("Не удалось найти расписание.")
    else:
        schedule = res["schedule"]
        subjects = res["subjects"]
        print("Предметы:", subjects)
        for c in schedule:
            print(f"\n=== Класс {c} ===")
            for day_idx, day in enumerate(schedule[c], start=1):
                # Печатаем слоты: None = пусто (окно)
                line = ", ".join(sub if sub else "-" for sub in day)
                print(f"День {day_idx}: {line}")
