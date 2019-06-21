from models import DifferentGraph

model2 = DifferentGraph(7, exclude_constraints=[9])
model2.optimize(verbose=False)
model2.plot("2_DifferentGraph")
model2.print_results()

model2 = DifferentGraph(7)
model2.optimize(verbose=False)
model2.plot("2_DifferentGraph_without_subtours")
model2.print_results()

model2 = DifferentGraph(30)
model2.optimize(verbose=False)
model2.print_results()

r = model2.m.relax()
r.optimize()

print("LPrelax:", round(r.objVal, 2))
optimality_gap = 100 * (model2.m.objVal - r.objVal) / model2.m.objVal
print("Optimality gap: {}%".format(round(optimality_gap, 2)))
