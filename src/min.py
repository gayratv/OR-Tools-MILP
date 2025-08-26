# pip install ortools
from ortools.sat.python import cp_model

def ilp_minimize_ge(A, b, c, lb=None, ub=None, time_limit_s=60, workers=8):
    """
    Минимизировать c^T x при ограничениях A x >= b, x целочисленные (неотрицательные по умолчанию).
    A: m x n, b: длины m, c: длины n
    lb/ub: списки длины n; если None -> lb=0, ub — грубая автооценка (лучше задать реалистично)
    """
    m, n = len(A), len(A[0])
    model = cp_model.CpModel()

    if lb is None:
        lb = [0] * n
    if ub is None:
        # Рекомендуется задать предметно разумные верхние границы!
        max_b = max(abs(v) for v in b) if b else 1
        ub = [max(1, max_b * 10) for _ in range(n)]

    x = [model.NewIntVar(int(lb[j]), int(ub[j]), f"x_{j}") for j in range(n)]

    # Ограничения: Ax >= b
    for i in range(m):
        model.Add(sum(int(A[i][j]) * x[j] for j in range(n)) >= int(b[i]))

    # Цель: minimize c^T x
    model.Minimize(sum(int(c[j]) * x[j] for j in range(n)))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit_s)
    solver.parameters.num_search_workers = int(workers)

    status = solver.Solve(model)
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {
            "status": "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE",
            "objective": solver.ObjectiveValue(),
            "x": [solver.Value(var) for var in x],
        }
    return {"status": "INFEASIBLE/UNKNOWN", "objective": None, "x": None}

# --- пример ---
if __name__ == "__main__":
    # minimize 3x1 + 2x2 + 0x3
    c = [3, 2, 0]
    A = [
        [2, 1, 0],
        [1, 3, 1],
    ]
    b = [8, 13]
    lb = [0, 0, 0]
    ub = [100, 100, 100]  # поставьте реалистичные верхние границы!

    res = ilp_minimize_ge(A, b, c, lb=lb, ub=ub, time_limit_s=10, workers=8)
    print(res)
