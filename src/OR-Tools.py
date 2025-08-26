# pip install ortools
from ortools.sat.python import cp_model

def ilp_maximize_ge(A, b, c, lb=None, ub=None, time_limit_s=60, workers=8):
    """
    Максимизация c^T x при ограничениях A x >= b, x целочисленные.
    A: список списков (m x n)
    b: список длины m
    c: список длины n (коэффициенты цели)
    lb: нижние границы переменных (список длины n) или None -> 0
    ub: верхние границы переменных (список длины n) или None -> автооценка
    """
    m, n = len(A), len(A[0])
    model = cp_model.CpModel()

    # Границы
    if lb is None:
        lb = [0] * n
    if ub is None:
        # Старайтесь задать реалистичные верхние границы!
        # Здесь грубая страховка от неограниченности: max_b по модулю
        max_b = max(abs(v) for v in b) if b else 1
        ub = [max(1, max_b * 10) for _ in range(n)]

    # Переменные: целые в [lb_j, ub_j]
    x = [model.NewIntVar(int(lb[j]), int(ub[j]), f"x_{j}") for j in range(n)]

    # Ограничения Ax >= b
    for i in range(m):
        model.Add(sum(int(A[i][j]) * x[j] for j in range(n)) >= int(b[i]))

    # Целевая функция: maximize c^T x
    model.Maximize(sum(int(c[j]) * x[j] for j in range(n)))

    # Параметры решателя
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit_s)
    solver.parameters.num_search_workers = int(workers)

    status = solver.Solve(model)

    status_map = {
        cp_model.OPTIMAL: "OPTIMAL",
        cp_model.FEASIBLE: "FEASIBLE",
        cp_model.INFEASIBLE: "INFEASIBLE",
        cp_model.MODEL_INVALID: "MODEL_INVALID",
        cp_model.UNKNOWN: "UNKNOWN",
    }

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        x_val = [solver.Value(var) for var in x]
        obj = solver.ObjectiveValue()
        return {"status": status_map[status], "objective": obj, "x": x_val}
    else:
        return {"status": status_map[status], "objective": None, "x": None}


# --- Пример использования ---
if __name__ == "__main__":
    # maximize 3x1 + 2x2x2 + 4x3
    c = [3, 8, 4]
    # Ax >= b
    A = [
        [2, 1, 0],
        [1, 3, 1],
    ]
    b = [8, 13]

    # Границы переменных (рекомендуется задавать реалистично!)
    lb = [0, 0, 0]
    ub = [100, 100, 100]   # если убрать/занизить, можно получить неограниченность/слабую модель

    res = ilp_maximize_ge(A, b, c, lb=lb, ub=ub, time_limit_s=10, workers=8)
    print(res)
