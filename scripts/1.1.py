import matplotlib.pyplot as plt

from models import TimeSpaceNetwork

model1 = TimeSpaceNetwork(30)
model1.optimize(verbose=False)
# model1.print_results()
model1.save('1_TimeSpaceNetwork.lp')

model1.plot("1_TimeSpaceNetwork")

r = model1.m.relax()
r.optimize()
print("LPrelax:", r.objVal)

optimality_gap = 100 * (model1.m.objVal - r.objVal) / model1.m.objVal
print(f"Optimality gap: {round(optimality_gap, 2)}%")
