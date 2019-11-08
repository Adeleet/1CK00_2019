import sys
sys.path.append("..")
sys.path.append("../lib")

from random import shuffle

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from gurobipy import *
from helper_functions import *
from models import DifferentGraph, LateAcceptance, NearestNeighbour
from visualizer import plot, plot_tsp




model4_LA = LateAcceptance(30, L=50)
model4_NN = NearestNeighbour(n=30)

model4_LA.optimize()
model4_NN.optimize()

OPTIMAL_VALUE = 496

optimality_gap = 100 * (model4_LA.C - OPTIMAL_VALUE) / model4_LA.C

locations = parse_tsp_txt(30)[0]
# plot(locations, [model4.s], "4_LateAcceptance")
# plot(locations, [model4_NN.tour], "4_NearestNeighbour")

# Initialize empty list to hold random results

# Start with random starting solution, add results to random_starts
random_starts = model4_LA.random_start_results(10, 1)

# Start each L with random starting solution, add results to random_starts_L
random_starts_L = []

for i, L in enumerate([1, 10, 20, 50, 100, 150]):
    model4 = LateAcceptance(30, lh=L)
    rand_results = model4_LA.random_start_results(10)
    random_starts_L.append(np.array(rand_results))

# Lowest value found for 10 random starts for each L value
MIN_RAND_START_L_VALUE = np.array(start_pos_L).min()

# Initialize a different graph G(V,A)
model4DG = DifferentGraph(100)

# Relation of G(V,A): no integer constraints
r = model4DG.m.relax()
r.optimize()

# Initialize figures
fig, ax = plt.subplots(figsize=(10, 10))

for L in enumerate([1, 10, 20, 50, 100, 300]):
    models = []
    avgs = []
    for i in range(20):
        starting_solution = model4.s[1:-1]
        shuffle(starting_solution)
        model4.s = [0] + starting_solution + [0]
        model4.C = model4.calc_obj_val(model4.s)
        model4.f = [model4.C] * L
        models.append(model4)
    for t in range(10000):
        for model in models:
            model.step()
        avgs.append(sum([model.C for model in models]) / 20)
    ax.plot(avgs, label="{}".format(L))

plt.legend(['L=1', 'L=10', 'L=20', 'L=50', 'L=100', 'L=300']), plt.savefig(
    "output/figures/4_ParameterL.png",
    dpi=300), plt.xlabel("iteration"), plt.ylabel("Mean Obj. Value")
