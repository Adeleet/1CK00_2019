from models import DifferentGraph

tsp7_model = DifferentGraph(7, exclude_constraints=[9])
tsp7_model.optimize(verbose=False)
# tsp7_model.print_results()

tsp7_model = DifferentGraph(7)
tsp7_model.optimize(verbose=False)
# tsp7_model.print_results()

tsp30_model = DifferentGraph(30)
tsp30_model.optimize(verbose=False)
# tsp30_model.print_results()


r = tsp30_model.m.relax()
r.optimize()
print("LPrelax:", r.objVal)
optimality_gap = 100 * (tsp30_model.m.objVal - r.objVal) / tsp30_model.m.objVal
print("Optimality gap: {}%".format(round(optimality_gap, 2)))
