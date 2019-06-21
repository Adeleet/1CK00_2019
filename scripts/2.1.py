from random import choice

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from gurobipy import *

from helper_functions import *
from models import CVRPModel
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

Q = 80
r = 4
f = 101

# To hold results, initialize as (list) : list[k] => (ObjValK, xvarsK)
K_optimals = []

# Iterate through loop, initialize model
for K in range(1, 10):
    model = CVRPModel(Q, r, K, f, dist, demand)
    model.optimize()
    K_optimals.append({
        "K": K,
        "Obj": model.m.ObjVal,
        "Tour": model.get_tours()
    })

max(K_optimals, key=lambda res: res["Obj"])
[result["Obj"] for result in K_optimals]
K_optimals

plt.figure(), plt.scatter(x, y), plt.title(
    "VRP - Vehicle Scaling"), plt.xlabel("K number of vehicles"), plt.ylabel(
        "Profit (revenue, transport and fixed costs)")
