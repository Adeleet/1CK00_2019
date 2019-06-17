import numpy as np
import pandas as pd
from gurobipy import GRB, Model, tupledict

from visualizer import plot_tsp

# Import distances (30x30) and locations x,y coordinates (30x2)
dist = np.load("../data/tsp30_distances.npy")
location = np.load("../data/tsp30_locations.npy")

# distance_map = list(zip([i for i in range(n)], [i for i in range(n)]))

# Number of cities n
n = dist.shape[0]
print('Number of cities in TSP model: {}'.format(n))

# 1 INITIALIZE MODEL
m = Model()

# 2 DEFINE X VARIABLES
xvars = tupledict()

# Each depot (30) can travel to all other (29) at 30 steps
# 2a xvars for arcs leaving depot 0 (29 routes from depot 0)
for j in range(1, n):
    xvars[0, j, 0] = m.addVar(obj=dist[0][j],
                              vtype=GRB.BINARY,
                              name='x[%d,%d,%d]' % (0, j, 0))

# 2b xvars for arcs entering depot 0 (29 routes to depot 0)
for i in range(1, n):
    xvars[i, 0, n - 1] = m.addVar(obj=dist[i][0],
                                  vtype=GRB.BINARY,
                                  name='x[%d,%d,%d]' % (i, 0, n - 1))

# xvars[x,y,z]
#     x : source
#     y : destination
#     z : time step

# all remaining xvars
# Since we always start at 0, consider other 29 depots i,j (30 - 1 = 29)
for i in range(1, n):
    for j in range(1, n):
        # Depot cannot travel to 'itself'
        if i != j:
            # Because we start/end at depot 0, the first (0) and last (n) steps can be ignored; 28 steps
            for t in range(1, n - 1):
                # Add xvar: from i to j at step t
                xvars[i, j, t] = m.addVar(obj=dist[i][j],
                                          vtype=GRB.BINARY,
                                          name='x[%d,%d,%d]' % (i, j, t))

# 3 DEFINE CONSTRAINTS

# Must start from depot 0 on first step
m.addConstr((xvars.sum(0, '*', 0) == 1), "leaveDepot")

# Must arrive at depot 0 on last step
m.addConstr((xvars.sum("*", 0, n - 1) == 1), "arriveDepot")

m.update()

# Ingoing at i at time t = Outgoing from i at time t+1
for i in range(n):
    for t in range(n - 1):
        m.addConstr(xvars.sum("*", i, t) == xvars.sum(i, "*", t + 1),
                    name="inOut_i{}_t{}".format(i, t))

# Only visit location once
for i in range(n):
    m.addConstr(xvars.sum("*", i, "*") == 1)

m.update()
# Optional: write model to file
m.write("tsp.lp")

# Optimize and get solution:
m.optimize()
for v in m.getVars():
    if v.x > 0.5:
        print(v.varName, v.x)
print('Obj:', m.objVal)

# Build and visualize the tour here using the x variables...

vals = m.getAttr('X', xvars)
vals_series = pd.Series(dict(vals))
vals_visited = vals_series[vals_series == 1]

visits = list(dict(vals_series[vals_series == 1]).keys())

visits_sorted = sorted(visits, key=lambda x: x[2])
tour = [0] + [v[1] for v in visits_sorted]

plot_tsp(location, tour, name='exact')

r = m.relax()
r.optimize()
print("LPrelax: ", r.objVal)
