from random import choice

import numpy as np
import pandas as pd
from gurobipy import *

from helper_functions import *
from visualizer import plot, plot_tsp


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
        self.uvars = [
            self.m.addVar(lb=1, ub=n, vtype=GRB.INTEGER, name='u[%d]' % i)
            for i in range(n)
        ]

        if not 7 in exclude_constraints:
            # (7) Constraint (7): for each location i: only 1 outgoing visit chosen
            for i in range(n):
                self.m.addConstr(self.xvars.sum(i, "*") == 1)
        if not 8 in exclude_constraints:
            # Constraint (8): for each location i: #ingoing == #outgoing
            for i in range(n):
                self.m.addConstr(
                    self.xvars.sum("*", i) == self.xvars.sum(i, "*"))
        if not 9 in exclude_constraints:
            # Constraint (9): subtour constraints
            M = n - 1
            for i in range(n):
                for j in range(n):
                    if not i == j and not j == 0:
                        self.m.addConstr(self.uvars[j] >= self.uvars[i] + 1 -
                                         M + M * self.xvars[i, j])
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
        print("\nObj:", self.m.objVal)
        # Sort visits Xij's by i, if not already done
        print("\nx[i,j] = 1 variables:\n\n")
        print("| i | j | dij | ui | ")
        print("| - | - | -- | -- | ")
        for (i, j) in self.visits:
            print(f"| {i} | {j} | {self.dist[i][j]} | {self.uvars[i].X} |")

        print("\nTour(s)")
        for tour in self.tours:
            print("-\t {}".format(tour))

    def plot(self, name):
        """
        Plots results, optimizes model first if not done yet
        """
        if self.m.Status == 1:
            print("Model not yet optimized, now optimizing")
            self.optimize(verbose=False)
        plot(self.location, self.tours, name)


class TimeSpaceNetwork:
    def __init__(self, n, verbose=False):
        """
        Intializes a Time-Space Network (class 4)

        Attributes:
            location (list):   (x,y) coordinates parsed from .txt file
            dist (list):       (i,j) distance from i to j
            n:                  number of locations
            m:                  gurobi model used for optimization
            xvars:              decision variables
        """
        tsp_data = parse_tsp_txt(n)
        self.location = tsp_data[0]
        self.dist = tsp_data[1]
        self.n = n
        self.m = Model()
        self.xvars = tupledict()

        if verbose:
            print('Time Space Network model with {} cities'.format(n))

        # (1) Define X0,j,0 variables: start from node 0
        for j in range(1, n):
            self.xvars[0, j, 0] = self.m.addVar(obj=self.dist[0][j],
                                                vtype=GRB.BINARY,
                                                name='x[%d,%d,%d]' % (0, j, 0))

        # (1) Define Xi,0,n-1 variables: end at node 0
        for i in range(1, n):
            self.xvars[i, 0, n - 1] = self.m.addVar(obj=self.dist[i][0],
                                                    vtype=GRB.BINARY,
                                                    name='x[%d,%d,%d]' %
                                                    (i, 0, n - 1))

        # (1) Define remaining variables
        for i in range(1, n):
            for j in range(1, n):
                # Depot cannot travel to 'itself'
                if i != j:
                    for t in range(1, n - 1):
                        self.xvars[i, j, t] = self.m.addVar(
                            obj=self.dist[i][j],
                            vtype=GRB.BINARY,
                            name='x[%d,%d,%d]' % (i, j, t))

        # (2) Constraint: Start from depot 0 on first step
        self.m.addConstr((self.xvars.sum(0, '*', 0) == 1), "x[0,j]=1")

        # (3) Constraint: Ingoing Xji = Outgoing Xij
        for i in range(n):
            for t in range(n - 1):
                xji = self.xvars.sum("*", i, t)
                xij = self.xvars.sum(i, "*", t + 1)
                self.m.addConstr(xji == xij, name=f"x[j,{i},{t}]=x[{i},j,{t}]")

        # (4) Constraint: Only 1 ingoing arc for node 1 to n-1
        for j in range(1, n - 1):
            self.m.addConstr(self.xvars.sum("*", j, "*") == 1)
        # (5) Constraint: Xij is binary already defined in (1)

        self.update()

    def update(self):
        """
        Calls gurobi's update function
        """
        self.m.update()

    def optimize(self, verbose=True):
        """
        Calls gurobi's optimize function, and calculates visits and tours
        """
        if not verbose:
            self.m.setParam('OutputFlag', False)
        self.m.optimize()
        self.visits = get_visits(self.xvars)
        self.tours = get_tours(self.visits)

    def save(self, filename):
        """
        Saves model as file to /models/{filename}
        """
        self.m.write(filename)

    def print_results(self):
        """
        Prints results, optimizes model first if not done yet

        Results consist of:
            Obj:        Objective Value after optimization
            x[i,j,t] :  selected variables in solution where x[i,j,t] = 1
            Tours(s) :  selected tours in solution
        """
        if self.m.Status == 1:
            print("Model not yet optimized, now optimizing")
            self.optimize(verbose=False)
        print("\nObj:", self.m.objVal)
        # Sort visits Xij's by i, if not already done

        print("\nx[i,j,t] variables:\n")
        for visit in self.visits:
            print("-\t x[{},{},{}]".format(visit[0], visit[1], visit[2]))

        print("\nTour(s)")
        print("-\t {}".format(self.tours[0]))

    def plot(self, name):
        """
        Plots results, optimizes model first if not done yet
        """
        if self.m.Status == 1:
            print("Model not yet optimized, now optimizing")
            self.optimize(verbose=False)
        plot_tsp(self.location, self.tours[0], name)


class NearestNeighbour:
    def __init__(self, n, verbose=False, start=0):
        tsp_data = parse_tsp_txt(n)
        self.location = tsp_data[0]
        self.dist = tsp_data[1]
        self.start = start
        self.n = n

        if verbose:
            print('NearestNeighbour Heuristic with {} cities'.format(n))

    def nearest_node(self, i, dj):
        options = [(j, d) for (j, d) in enumerate(dj)
                   if not i == j and j not in self.tour]
        return min(options, key=lambda option: option[1])[0]

    def calc_obj_val(self):
        self.visits = []
        for i in self.tour[:-1]:
            self.visits.append((self.tour[i], self.tour[i + 1]))
        self.objVal = sum([self.dist[i][j] for (i, j) in self.visits])

    def optimize(self, verbose=True):
        self.tour = [self.start]
        while len(self.tour) < self.n:
            i = self.tour[-1]
            dj = self.dist[i]
            dest = self.nearest_node(i, dj)
            self.tour.append(dest)
        self.tour.append(self.start)

        self.calc_obj_val()
        if verbose:
            self.print_results()

    def print_results(self):
        if not len(self.visits) == self.n:
            print("Model not yet optimized, now optimizing")
            self.optimize(verbose=False)
        print("\nObj:", self.objVal)
        # Sort visits Xij's by i, if not already done

        print("\nx[i,j] = 1 variables:")
        print("| i | j | dij | ")
        print("| - | -| -- | ")
        for (i, j) in self.visits:
            print(f"| {i} | {j} | {self.dist[i][j]} | ")
        print("\nTour")
        print(f"{self.tour}")

    def plot(self, name):
        """
        Plots results, optimizes model first if not done yet
        """
        if not len(self.visits) == self.n:
            print("Model not yet optimized, now optimizing")
            self.optimize(verbose=False)
        plot(self.location, [self.tour], name)


class LateAcceptance:
    def __init__(self, n, lh, verbose=False):
        tsp_data = parse_tsp_txt(n)
        self.location = tsp_data[0]
        self.dist = tsp_data[1]
        self.n = n
        self.lh = lh
        self.visits = []
        self.s = [i for i in range(n)]
        self.C = self.calc_obj_val(self.s)
        self.f = [self.C] * (lh)

        self.I = 0
        self.I_idle = 0

        if verbose:
            print('NearestNeighbour Heuristic with {} cities'.format(n))

    def calc_obj_val(self, s):
        self.visits = []
        for i in range(len(s) - 1):
            self.visits.append((s[i], s[i + 1]))
        return sum([self.dist[i][j] for (i, j) in self.visits])

    def candidate_solution(self):
        new_tour = self.s[1:-1]
        r_remove = choice(new_tour)
        r_insert = choice(new_tour)
        new_tour.remove(r_remove)
        new_tour.insert(r_insert, r_remove)
        return [0] + new_tour + [0]

    def optimize(self, verbose=False):
        while not (self.I > 10000):
            self.step(self)
        if verbose:
            self.print_results()

    def step(self):
        s_candidate = self.candidate_solution()
        C_candidate = self.calc_obj_val(s_candidate)
        if C_candidate >= self.C:
            self.I_idle += 1
        if C_candidate < self.C:
            self.I_idle = 0
        v = self.I % self.lh
        if C_candidate < self.f[v] or C_candidate <= self.C:
            self.s = s_candidate
            self.C = self.calc_obj_val(self.s)
        if self.C < self.f[v]:
            self.f[v] = self.C
        self.I += 1

    def print_results(self):
        print("\nObj:", self.C)
        print("\nx[i,j] = 1 variables:")
        print("| i | j | dij | ")
        print("| - | -| -- | ")
        for (i, j) in self.visits:
            print(f"| {i} | {j} | {self.dist[i][j]} | ")
        print("\nTour")
        print(f"{self.s}")

    def plot(self, name):
        """
        Plots results, optimizes model first if not done yet
        """
        if not len(self.visits) == self.n:
            print("Model not yet optimized, now optimizing")
            self.optimize(verbose=False)
        plot(self.location, [self.tour], name)
