import numpy as np
import pandas as pd
from gurobipy import *

from helper_functions import *
from visualizer import plot_tsp


class DifferentGraph:
    def __init__(self, n, exclude_constraints=[], verbose=False):
        tsp_data = parse_tsp_txt(n)
        self.location = tsp_data[0]
        self.dist = tsp_data[1]
        self.m = Model()
        self.n = n
        if verbose:
            print('Different Graph model with {} cities'.format(n))
            if len(exclude_constraints) > 0:
                print("Excluded constraints: {}".format(exclude_constraints))

        # Define x variables: xvars[i,j] := visit selected that travels from i to j
        self.xvars = tupledict()
        for i in range(n):
            for j in range(n):
                if not i == j:
                    self.xvars[i, j] = self.m.addVar(obj=self.dist[i][j],
                                                     vtype=GRB.BINARY,
                                                     name='x[%d,%d]' % (i, j))

        # Define u variables: uvars[i] := position of node i in tour
        self.uvars = [self.m.addVar(lb=1, ub=n, vtype=GRB.INTEGER, name='u[%d]' % i)
                      for i in range(n)]

        if not 7 in exclude_constraints:
            # Constraint (7): for each location i: only 1 outgoing visit chosen
            for i in range(n):
                self.m.addConstr(self.xvars.sum(i, "*") == 1)
        if not 8 in exclude_constraints:
            # Constraint (8): for each location i: #ingoing == #outgoing
            for i in range(n):
                self.m.addConstr(self.xvars.sum("*", i) ==
                                 self.xvars.sum(i, "*"))
        if not 9 in exclude_constraints:
            # Constraint (9): subtour constraints
            M = n - 1
            for i in range(n):
                for j in range(n):
                    if not i == j and not j == 0:
                        self.m.addConstr(
                            self.uvars[j] >= self.uvars[i] + 1 - M + M * self.xvars[i, j])
            # Constraint (10): each location is visited within n steps
                # Already handled in upper bound of uvars, with Ui: [1,n]
        if not 11 in exclude_constraints:
            # Constraint (11): tour starts from node 0 (i = 0 --> Ui = 1)
            self.m.addConstr(self.uvars[0] == 1)
        self.update()

    def update(self):
        self.m.update()

    def optimize(self, verbose=True):
        if not verbose:
            self.m.setParam('OutputFlag', False)
        self.m.optimize()
        self.visits = get_visits(self.xvars)
        self.tours = get_tours(self.visits)

    def print_results(self):
        if self.m.Status == 1:
            print("Model not yet optimized, now optimizing")
            self.optimize(verbose=False)
        print("\nRESULTS")
        print("\nObj:", self.m.objVal)
        # Sort visits Xij's by i, if not already done

        print("\nx[i,j] variables:")
        for visit in self.visits:
            print("-\t x[{},{}]".format(visit[0], visit[1]))

        print("\nu[i] variables:")
        for i in range(len(self.uvars)):
            print("-\t u[{}] = {}".format(i, int(self.uvars[i].X)))

        print("\nTour(s)")
        for tour in self.tours:
            print("-\t {}".format(self.tours))
