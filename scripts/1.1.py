import itertools
import math
import random
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from gurobipy import *

from visualizer import plot, plot_tsp

tsp_30_distances = np.load("../data/tsp30_distances.npy")
tsp_30_locations = np.load("../data/tsp30_locations.npy")
distance_map = list(zip([i for i in range(30)], [i for i in range(30)]))
n = 30


# distance matrix

dist = tsp_30_distances
# number of cities n
n = len(dist)
print('The number of cities in my model: {}'.format(n))

# build model
m = Model()
xvars = tupledict()

# 1. Define the variables:
# xvars for arcs leaving depot 0
for j in range(1, n):
    xvars[0, j, 0] = m.addVar(
        obj=dist[0][j], vtype=GRB.BINARY, name='x[%d,%d,%d]' % (0, j, 0))

# xvars for arcs entering depot 0
for i in range(1, n):
    xvars[i, 0, n - 1] = m.addVar(obj=dist[i][0],
                                  vtype=GRB.BINARY, name='x[%d,%d,%d]' % (i, 0, n - 1))

# xvars[x,y,z]
#     x : source
#     y : destination
#     z : time step

# all remaining xvars
for i in range(1, n):
    for j in range(1, n):
        if i != j:
            for t in range(1, n - 1):
                xvars[i, j, t] = m.addVar(
                    obj=dist[i][j], vtype=GRB.BINARY, name='x[%d,%d,%d]' % (i, j, t))


# 2. Define the constraints:

# leave depot
m.addConstr((xvars.sum(0, '*', 0) == 1), "leaveDepot")

# Arrive at leaveDepot
m.addConstr((xvars.sum("*", 0, 29) == 1), "arriveDepot")

# 3 constraints are still missing here....
m.update()
for i in range(30):
    for t in range(29):
        m.addConstr(xvars.sum("*", i, t) == xvars.sum(i,
                                                      "*", t + 1), name="incomingToutgoingT+1")


for i in range(30):
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
tour
plot_tsp(tsp_30_locations, tour, name='exact')
[tsp_30_locations[i] for i in tour]
tour
# done :)
