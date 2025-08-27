"""
Refactored pretty-printers that consume the single InputData object
plus solution variables (x, z). No more long argument lists.

Usage (after you solve the model):

    from print_schedule_refactored import print_by_classes, print_by_teachers

    prob, x, z, y = build_and_solve_timetable(data, ...)
    print_by_classes(data, x, z)
    print_by_teachers(data, x, z)
"""
from typing import Dict, Tuple
import pulp

from input_data import InputData


def _val(var) -> float:
    return float(pulp.value(var)) if var is not None else 0.0


def print_by_classes(data: InputData, x: Dict[Tuple, pulp.LpVariable], z: Dict[Tuple, pulp.LpVariable]) -> None:
    """Pretty-print timetable by classes using InputData and solution vars.

    Parameters
    ----------
    data : InputData
        Holds days, periods, classes, subjects, split_subjects, subgroup_ids,
        assigned_teacher, subgroup_assigned_teacher, etc.
    x : dict
        MILP vars for non-split lessons, indexed (class, subject, day, period).
    z : dict
        MILP vars for split lessons, indexed (class, subject, subgroup, day, period).
    """
    days = data.days
    periods = data.periods
    classes = data.classes
    subjects = data.subjects
    split_subjects = set(data.split_subjects)

    print("\n================ РАСПИСАНИЕ ПО КЛАССАМ ================")
    for c in classes:
        print(f"\n=== Класс {c} ===")
        for d in days:
            row = []
            for p in periods:
                cell = None
                # Try non-split first
                for s in subjects:
                    if s in split_subjects:
                        continue
                    var = x.get((c, s, d, p))
                    if var is not None and _val(var) > 0.5:
                        t = data.assigned_teacher[(c, s)]
                        cell = f"{p}: {s} ({t})"
                        break
                # Then split-subjects
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
                    if pieces:
                        cell = f"{p}: " + "+".join(pieces)
                row.append(cell or f"{p}: —")
            print(f"{d} | "+", ".join(row))


def print_by_teachers(data: InputData, x: Dict[Tuple, pulp.LpVariable], z: Dict[Tuple, pulp.LpVariable]) -> None:
    """Pretty-print timetable by teachers using InputData and solution vars."""
    days = data.days
    periods = data.periods
    teachers = data.teachers

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
            print(f"{d} | "+", ".join(row))
        print(f"Итого уроков за неделю: {total}")
