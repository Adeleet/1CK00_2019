import itertools
import math
import random
import sys

import numpy as np
from gurobipy import *

from visualizer import plot, plot_tsp

# tsp_30_distances = np.load("../data/tsp30_distances.npy")
# tsp_30_locations = np.load("../data/tsp30_locations.npy")
# distance_map = list(zip([i for i in range(30)], [i for i in range(30)]))
# n = 30


def subtourelim(model, where):
    if where == GRB.Callback.MIPSOL:
        # make a list of edges selected in the solution
        vals = model.cbGetSolution(model._vars)
        selected = tuplelist((i, j)
                             for i, j in model._vars.keys() if vals[i, j] > 0.5)
        # find the shortest cycle in the selected edge list
        tour = subtour(selected)
        if len(tour) < n:
            # add subtour elimination constraint for every pair of cities in tour
            model.cbLazy(quicksum(model._vars[i, j]
                                  for i, j in itertools.combinations(tour, 2))
                         <= len(tour) - 1)


# Given a tuplelist of edges, find the shortest subtour

def subtour(edges):
    unvisited = list(range(n))
    cycle = range(n + 1)  # initial length has 1 more city
    while unvisited:  # true if list is non-empty
        thiscycle = []
        neighbors = unvisited
        while neighbors:
            current = neighbors[0]
            thiscycle.append(current)
            unvisited.remove(current)
            neighbors = [j for i, j in edges.select(
                current, '*') if j in unvisited]
        if len(cycle) > len(thiscycle):
            cycle = thiscycle
    return cycle


# Dictionary of Euclidean distance between each pair of points
dist = {(i, j):
        math.sqrt(
            sum((tsp_30_distances[i][k] - tsp_30_distances[j][k])**2 for k in range(2)))
        for i in range(30) for j in range(i)}


m = Model()

# Create variables

vars = m.addVars(dist.keys(), obj=dist, vtype=GRB.BINARY, name='x')
for i, j in vars.keys():
    vars[j, i] = vars[i, j]  # edge in opposite direction

# You could use Python looping constructs and m.addVar() to create
# these decision variables instead.  The following would be equivalent
# to the preceding m.addVars() call...
#
# vars = tupledict()
# for i,j in dist.keys():
#   vars[i,j] = m.addVar(obj=dist[i,j], vtype=GRB.BINARY,
#                        name='e[%d,%d]'%(i,j))


# Add degree-2 constraint

m.addConstrs(vars.sum(i, '*') == 2 for i in range(n))

#
# m.addConstr(vars.sum(0, "*") == 1)
# vars.sum(j, "*") == 1
# for j in range(30):
#     m.addConstr(vars.sum(j, "*") == 1)
#     m.addConstr(vars.sum("*", j) == 1)
#
#
# m.addConstrs(vars.sum("*", j) == 1 for j in range(30))


# Using Python looping constructs, the preceding would be...
#
# for i in range(n):
#   m.addConstr(sum(vars[i,j] for j in range(n)) == 2)


# Optimize model

m._vars = vars
m.Params.lazyConstraints = 1

m.optimize(subtourelim)
vals = m.getAttr('X', vars)
selected = tuplelist((i, j) for i, j in vals.keys() if vals[i, j] > 0.5)

tour = subtour(selected)
assert len(tour) == n

print('')
print('Optimal tour: %s' % str(tour))
print('Optimal cost: %g' % m.objVal)
print('')


plot_tsp(tsp_30_locations, tour, name='exact')
[tsp_30_locations[i] for i in tour]
tour

m.getConstrs()[0]
