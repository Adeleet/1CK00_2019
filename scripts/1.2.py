import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from gurobipy import *

from visualizer import plot, plot_tsp


def parse_tsp_txt(n):
    """
    Parses txt file and returns [location, dist]

    Parameters:
        n (int): tsp problem size, allowed values are 5, 7, 30, 100

    Returns:
        (location, dist) :
                location:   list of n (x, y) coordinate tuples
                dist:       list of n * n distances, with dist[i][j]
                            as the distance from node i t node j
    """
    if not n == 5 and not n == 7 and not n == 30 and not n == 100:
        raise ValueError("Invalid n, allowed values are: 5, 7, 30, 100")
    with open("../data/tsp{}.txt".format(n)) as file:
        file_content = [l.strip() for l in file.readlines()]
    length = len(file_content)

    loc_index = (1, int(length / 2))
    dist_index = (loc_index[1] + 1, length)

    location = [eval(l) for l in file_content[loc_index[0]:loc_index[1]]]
    dist = [eval(l) for l in file_content[dist_index[0]:dist_index[1]]]
    return (location, dist)


location, dist = parse_tsp_txt(n=7)


# Number of cities n
n = len(dist)
print('Number of cities in TSP model: {}'.format(n))


# Initialize Model
m = Model()

# Define x variables: xvars[i,j] := arc selected that travels from i to j
xvars = tupledict()
for i in range(n):
    for j in range(n):
        if not i == j:
            xvars[i, j] = m.addVar(obj=dist[i][j],
                                   vtype=GRB.BINARY,
                                   name='x[%d,%d]' % (i, j))


# Define u variables: uvars[i] := position of node i in tour
uvars = [m.addVar(lb=1, ub=n, vtype=GRB.INTEGER, name='u[%d]' % i)
         for i in range(n)]

# Constraint (7): for each location i: only 1 outgoing arc chosen
for i in range(n):
    m.addConstr(xvars.sum(i, "*") == 1)

# Constraint (8): for each location i: #ingoing == #outgoing
for i in range(n):
    m.addConstr(xvars.sum("*", i) == xvars.sum(i, "*"))

# Constraint (10): each location is visited within n steps
# Already handled in upper bound of uvars, with Ui: [1,n]

# Constraint (11): tour starts from node 0 (i = 0 --> Ui = 1)
m.addConstr(uvars[0] == 1)


# Update model, run optimization
m.update()
m.optimize()

# Obtain the selected xvars, thus the selected Xij arcs


def get_arcs(xvars):
    """
    Returns xvars as tuples (i,j) where Xij = 1

    Parameters:
        xvars (gurobipy.tupledict) : Selected Xij variables of the optimized model

    Returns
        arcs (list) : List of tuples (i,j) that are selected (Xij = 1)
    """
    arcs = []
    for i in range(n):
        for j in range(n):
            if not i == j and xvars[i, j].X == 1:
                arcs.append((i, j))
    return sorted(arcs, key=lambda arc: arc[0])


def get_tours(xvars, arcs):
    """
    Returns tours[], where each tour is a (sub)tour using the selected arcs
    If there are no subtours, tours is a list containing a single (complete)
    tour

    Parameters:
        xvars (gurobipy.tupledict) : Selected Xij variables of the optimized model
        arcs (list)                : List of tuples (i,j) obtained from get_arcs

    Returns:
        tours (list) : ordered list of locations of (sub)tours

    """
    tours = []
    visited = [False] * n
    for i in range(n):
        if visited[i]:
            continue
        j = i
        new_tour = []
        while not visited[j]:
            visited[j] = True
            new_tour.append(j)
            j = arcs[j][1]
        new_tour.append(new_tour[0])
        tours.append(new_tour)
    return tours


# Sort arcs Xij's by i, if not already done
arcs = get_arcs(xvars)
tours = get_tours(xvars, arcs)


# obtain the tours

for tour in tours:
    plot_tsp(location, tour, name='test'), plt.show()


# Constraint (9): subtour constraints
M = n - 1
for i in range(n):
    for j in range(n):
        if not i == j and not j == 0:
            m.addConstr(uvars[j] >= uvars[i] + 1 - M + M * xvars[i, j])
