# pip install ortools
from ortools.sat.python import cp_model

def build_and_solve_timetable(
    classes,                      # список классов: ["5а", "5б", ...]
    days=5,                       # 5 учебных дней
    slots_per_day=7,              # не более 7 уроков в день
    subjects=("math", "computer_science", "eng", "hist"),
    weekly_hours_per_subject=2,   # для простоты одинаково для всех предметов и классов
    teachers_by_subject=None,     # маппинг предмет -> учитель (один учитель на предмет)
    time_limit_s=30, workers=8
):
    """
    Строит расписание:
      - у каждого класса по 2 часа каждого предмета в неделю,
      - не более 7 уроков в день у класса,
      - один учитель по предмету не может вести в двух классах одновременно,
      - цель — просто найти допустимое расписание.

    Возвращает:
      {
        "status": "OK",
        "schedule": schedule_class,        # schedule_class[c][d][s] = subject | None
        "teachers_schedule": schedule_tch, # schedule_tch[teacher][d][s] = (subject, class) | None
        "subjects": subjects,
        "teachers": teachers_by_subject
      }
    """
    if teachers_by_subject is None:
        teachers_by_subject = {
            "math": "T_math",
            "computer_science": "T_compsci",
            "eng":  "T_eng",
            "hist": "T_hist",
        }

    model = cp_model.CpModel()

    C = list(classes)
    U = list(subjects)
    D = range(days)
    S = range(slots_per_day)

    # x[c,u,d,s] = 1 если в классе c в день d слот s идёт предмет u
    x = {}
    for c in C:
        for u in U:
            for d in D:
                for s in S:
                    x[c, u, d, s] = model.NewBoolVar(f"x[{c},{u},{d},{s}]")

    H = weekly_hours_per_subject

    # 1) Недельный план: у каждого класса по H занятий каждого предмета
    for c in C:
        for u in U:
            model.Add(sum(x[c, u, d, s] for d in D for s in S) == H)

    # 2) В каждом классе в каждом слоте не более одного урока
    for c in C:
        for d in D:
            for s in S:
                model.Add(sum(x[c, u, d, s] for u in U) <= 1)

    # 3) У класса за день не более slots_per_day уроков (формально уже ограничено, но оставим)
    for c in C:
        for d in D:
            model.Add(sum(x[c, u, d, s] for u in U for s in S) <= slots_per_day)

    # 4) Один учитель на предмет: не может вести в двух классах одновременно
    #    На каждом (day, slot) по предмету u суммируем по классам ≤ 1
    for u in U:
        for d in D:
            for s in S:
                model.Add(sum(x[c, u, d, s] for c in C) <= 1)

    # (опционально) разнести 2 часа предмета по разным дням:
    # for c in C:
    #     for u in U:
    #         for d in D:
    #             model.Add(sum(x[c, u, d, s] for s in S) <= 1)

    model.Minimize(0)  # feasibility

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit_s)
    solver.parameters.num_search_workers = int(workers)

    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {"status": str(status), "schedule": None, "teachers_schedule": None}

    # ----- Собираем расписание классов
    schedule_class = {c: [[None for _ in S] for _ in D] for c in C}
    for c in C:
        for d in D:
            for s in S:
                for u in U:
                    if solver.Value(x[c, u, d, s]) == 1:
                        schedule_class[c][d][s] = u
                        break

    # ----- Формируем расписание учителей (по предмету — один учитель)
    teachers = teachers_by_subject
    teacher_names = sorted(set(teachers[u] for u in U))
    schedule_tch = {t: [[None for _ in S] for _ in D] for t in teacher_names}

    for d in D:
        for s in S:
            for c in C:
                u = schedule_class[c][d][s]
                if u:
                    t = teachers[u]
                    schedule_tch[t][d][s] = (u, c)  # предмет и класс

    return {
        "status": "OK",
        "schedule": schedule_class,
        "teachers_schedule": schedule_tch,
        "subjects": U,
        "teachers": teachers_by_subject,
    }


# --------- пример запуска и печати ----------
if __name__ == "__main__":
    classes = [f"{g}а" for g in range(5, 12)]  # 5а..11а
    res = build_and_solve_timetable(classes=classes, time_limit_s=10, workers=8)

    if res["schedule"] is None:
        print("Не удалось найти расписание.")
    else:
        schedule = res["schedule"]
        tch_sched = res["teachers_schedule"]

        print("=== РАСПИСАНИЕ КЛАССОВ ===")
        for c in schedule:
            print(f"\nКласс {c}")
            for day_idx, day in enumerate(schedule[c], start=1):
                print(f"  День {day_idx}: " + ", ".join(sub if sub else "-" for sub in day))

        print("\n=== РАСПИСАНИЕ УЧИТЕЛЕЙ ===")
        for t in tch_sched:
            print(f"\nУчитель {t}")
            for day_idx, day in enumerate(tch_sched[t], start=1):
                # слоты: (subject, class) или "-"
                cells = []
                for cell in day:
                    if cell is None:
                        cells.append("-")
                    else:
                        subj, cl = cell
                        cells.append(f"{subj}@{cl}")
                print(f"  День {day_idx}: " + ", ".join(cells))
