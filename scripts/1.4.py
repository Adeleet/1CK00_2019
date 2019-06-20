from random import shuffle

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from gurobipy import *

from helper_functions import *
from models import DifferentGraph, LateAcceptance, NearestNeighbour
from visualizer import plot, plot_tsp

model4 = LateAcceptance(30, lh=50)
model4.optimize()
model4.print_results()

optimality_gap = 100 * (model4.C - 496) / model4.C
print(f"Optimality gap: {round(optimality_gap, 2)}%")

model4_NN = NearestNeighbour(n=30)
model4_NN.optimize(verbose=False)

locations = parse_tsp_txt(30)[0]
plot(locations, [model4.s], "4_LateAcceptance")
plot(locations, [model4_NN.tour], "4_NearestNeighbour")

model4 = LateAcceptance(100, lh=1)
model4.optimize()
print(f"Obj using lh = 1 : {model4.C}")

for i in range(10):
    model4 = LateAcceptance(100, lh=1)
    shuffle(model4.s)
    model4.C = model4.calc_obj_val(model4.s)
    model4.f = [model4.C] * (1)
    model4.optimize()
    print(f"-\t {model4.C}")

print("| L | " + " | ".join([f"ObjVal{i}" for i in range(1, 11)]) + " | ")
print("| ------ " * 10 + " | ")
output = ""
for L in [1, 10, 20, 50, 100, 150]:
    output += f"| {L} |"
    for i in range(10):
        model4 = LateAcceptance(100, lh=L)
        starting_solution = model4.s[1:-1]
        shuffle(starting_solution)
        model4.s = [0] + starting_solution + [0]
        model4.C = model4.calc_obj_val(model4.s)
        model4.f = [model4.C] * L
        model4.optimize()
        output += f" {model4.C} | "
    output += "\n"
print(output)

model4DG = DifferentGraph(100)
r = model4DG.m.relax()
r.optimize()

print("LPrelax:", round(r.objVal, 2))
optimality_gap = 100 * (936 - r.objVal) / 936
print("Optimality gap: {}%".format(round(optimality_gap, 2)))

fig, ax = plt.subplots(figsize=(10, 10))

for L in [1, 10, 20, 50, 100, 150]:
    models = []
    avgs = []
    for i in range(20):
        model4 = LateAcceptance(100, lh=L)
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
    ax.plot(avgs, label="".format(L))

plt.legend(['L=1', 'L=10', 'L=20', 'L=50', 'L=100',
            'L=150']), plt.savefig("../figures/4_ParameterL.png", dpi=600)
