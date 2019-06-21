from random import choice

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from gurobipy import *

from helper_functions import *
from visualizer import plot, plot_tsp

# Coordinates (x,y) for each location
location = [(50, 50), (49, 31), (26, 60), (23, 20), (96, 31), (64, 85),
            (60, 63), (71, 46), (30, 55), (4, 78), (74, 47), (94, 63),
            (20, 50)]

# Demand of customer j
demand = [0, 38, 13, 5, 39, 35, 18, 28, 12, 40, 28, 23, 14]

# Distance of node i to node j
dist = [
    [0, 19, 26, 40, 49, 37, 16, 21, 20, 53, 24, 45, 31],
    [19, 0, 37, 28, 47, 56, 33, 26, 30, 65, 29, 55, 35],
    [26, 37, 0, 40, 75, 45, 34, 47, 6, 28, 49, 68, 12],
    [40, 28, 40, 0, 73, 76, 56, 54, 35, 61, 57, 83, 31],
    [49, 47, 75, 73, 0, 62, 48, 29, 70, 103, 27, 32, 79],
    [37, 56, 45, 76, 62, 0, 22, 39, 45, 60, 39, 37, 57],
    [16, 33, 34, 56, 48, 22, 0, 20, 31, 57, 21, 34, 43],
    [21, 26, 47, 54, 29, 39, 20, 0, 41, 74, 3, 28, 52],
    [20, 30, 6, 35, 70, 45, 31, 41, 0, 34, 44, 64, 12],
    [53, 65, 28, 61, 103, 60, 57, 74, 34, 0, 76, 91, 33],
    [24, 29, 49, 57, 27, 39, 21, 3, 44, 76, 0, 25, 55],
    [45, 55, 68, 83, 32, 37, 34, 28, 64, 91, 25, 0, 76],
    [31, 35, 12, 31, 79, 57, 43, 52, 12, 33, 55, 76, 0],
]

# Constants Q (vehicle capacity), r (profit/demand), f (cost/vehicle)
Q = 80
n = len(dist)
r = 4
f = 101

# To hold results, initialize as (list) : list[k] => (ObjValK, xvarsK)
K_optimals = []

# Iterate through loop, initialize model
for K in range(n):
    m = Model()
    m.params.TIME_LIMIT = 300

    # (1) Objective Function:

    # (1) Initialize 3-parameter binary values Xijk: vehicle k from i to j
    xvars = tupledict()
    for i in range(n):
        for j in range(n):
            if not i == j:
                for k in range(K):
                    xvars[i, j, k] = m.addVar(vtype=GRB.BINARY,
                                              name=f"x[{i}][{j}][{k}]")

    # (1) Initialize 2-parameter integer variabes Ujk:
    #position of node i in the tour of vehicle k.
    uvars = tupledict()
    for k in range(K):
        for j in range(n):
            uvars[j, k] = m.addVar(vtype=GRB.INTEGER,
                                   lb=0,
                                   ub=n,
                                   name=f"u[{j}][{k}]")

    m.update()

    # (1) Transportation costs: sum all binary Xij * Dij
    transport_costs = sum([
        dist[i][j] * xvars.sum(i, j, "*") for i in range(n) for j in range(n)
    ])

    # (1) Fixed fee, every vehicle costs f, so f*K is total vehicle cost
    fixed_fee = K * f

    # (1) Revenue of r per demand j for each j visited.
    # Simply sum all variables as we will handle restrictions later on in the constraints
    revenue = sum([demand[j] * r * xvars.sum("*", j, "*") for j in range(n)])

    m.setObjective((revenue - transport_costs - fixed_fee), GRB.MAXIMIZE)

    # (2) Constraint: Only visit each place once
    for j in range(1, n):
        m.addConstr(xvars.sum("*", j, "*") <= 1)

    # (3) Constraint: Only leave each place once
    for i in range(1, n):
        m.addConstr(xvars.sum(i, "*", "*") <= 1)

    for k in range(K):
        # (4) Constraint: each vehicle can visit a place at most once
        for j in range(n):
            m.addConstr(xvars.sum("*", j, k) <= 1)

        # (5) Constraint: each vehicle can leave a place at most once
        for i in range(n):
            m.addConstr(xvars.sum(i, "*", k) <= 1)

    # (6) If vehicle k visits i, it should also leave i
    for k in range(K):
        for j in range(n):
            m.addConstr(xvars.sum("*", j, k) == xvars.sum(j, "*", k))

    # (7) Subtour constraints: each vehicle makes a single tour
    M = n - 1
    for i in range(n):
        for j in range(1, n):
            if not i == j:
                m.addConstr(
                    uvars.sum(j, "*") >= uvars.sum(i, "*") + 1 - M *
                    (1 - xvars.sum(i, j, "*")))

    # (8) Capacity constraints: each vehicle carries at most Q
    for k in range(K):
        m.addConstr(
            sum([xvars.sum("*", j, k) * demand[j] for j in range(n)]) <= Q)

    m.update()

    m.optimize()

    K_optimals.append({"Obj": m.ObjVal, "XVars": xvars})

plt.figure(figsize=(15, 7)), plt.scatter(
    [int(k) for k in K_optimals.keys()], K_optimals.values(),
    s=100), plt.title("Optimal Value of TSP"), plt.xlabel(
        "K number of vehicles"), plt.ylabel(
            "Profit (revenue, transport and fixed costs)")

visits = get_visits(xvars)


def get_vehicle_tour(visits, k):
    vehicle_visits = [(visit[0], visit[1]) for visit in visits
                      if visit[2] == k]
    tour = []
    key = 0
    while len(vehicle_visits) > 0:
        visit = [arc for arc in vehicle_visits if arc[0] == key][0]
        key = visit[1]
        tour.append(visit[1])
        vehicle_visits.remove(visit)
    return [0] + tour


plot(location, [get_vehicle_tour(visits, k) for k in range(K)], "2.a VRP")
