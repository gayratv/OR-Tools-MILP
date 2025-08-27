# Проверить, видит ли PuLP HiGHS, можно так:
import pulp
from pulp import PULP_HIGHS_CMD
print(pulp.listSolvers(onlyAvailable=True))
# Должен быть 'PULP_HIGHS_CMD' среди доступных

prob = pulp.LpProblem("t", pulp.LpMinimize)
prob += 0
prob.solve(PULP_HIGHS_CMD(msg=1, threads=2, mip_rel_gap=0.05))
print(pulp.LpStatus[prob.status])
