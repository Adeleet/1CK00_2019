from random import choice

import numpy as np
import pandas as pd
from gurobipy import *

from helper_functions import *
from visualizer import plot, plot_tsp


class DifferentGraph:
    """
    A direct Graph G(V,A) to solve a TSP problem

    Arguments:
        n (int) :                       TSP variant, n = 5, 7, 30 or 100

        exclude_constraints (list) :    integers to exclude constraints:
            (7) : For each location i, only 1 outgoing visit chosen
            (8) : For each location i, number of ingoing == number of outgoing
            (9) : No subtours allowed
            (11) : A tour has to start from location 0 (depot)


    """

    def __init__(self, n, exclude_constraints=[], verbose=False):
        tsp_data = parse_tsp_txt(n)
        self.location = tsp_data[0]
        self.dist = tsp_data[1]
        self.m = Model()
        self.n = n
        if verbose:
            print('Different Graph model with {} cities'.format(self.n))
            if len(exclude_constraints) > 0:
                print("Excluded constraints: {}".format(exclude_constraints))

        # Define x variables: xvars[i,j] := visit selected that travels from i to j
        self.xvars = tupledict()
        for i in range(self.n):
            for j in range(self.n):
                if not i == j:
                    self.xvars[i, j] = self.m.addVar(obj=self.dist[i][j],
                                                     vtype=GRB.BINARY,
                                                     name='x[%d,%d]' % (i, j))

        # Define u variables: uvars[i] := position of node i in tour
        self.uvars = [
            self.m.addVar(lb=1, ub=n, vtype=GRB.INTEGER, name='u[%d]' % i)
            for i in range(self.n)
        ]

        if not 7 in exclude_constraints:
            # (7) Constraint (7): for each location i: only 1 outgoing visit chosen
            for i in range(self.n):
                self.m.addConstr(self.xvars.sum(i, "*") == 1)
        if not 8 in exclude_constraints:
            # Constraint (8): for each location i: #ingoing == #outgoing
            for i in range(self.n):
                self.m.addConstr(
                    self.xvars.sum("*", i) == self.xvars.sum(i, "*"))
        if not 9 in exclude_constraints:
            # Constraint (9): subtour constraints
            M = n - 1
            for i in range(self.n):
                for j in range(self.n):
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
        """
        Calls gurobi's update function to update model with variables and constraints
        """
        self.m.update()

    def optimize(self, verbose=True):
        """
        Calls gurobi's optimize function to update model with variables and constraints
        Calculates visits and tours and assigns these to instance
        """
        if not verbose:
            self.m.setParam('OutputFlag', False)
        self.m.optimize()
        self.visits = get_visits(self.xvars)
        self.tours = get_tours(self.visits)

    def print_results(self):
        if self.m.Status == 1:
            print("Model not yet optimized, now optimizing")
            self.optimize(verbose=True)
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
            self.optimize(verbose=True)
        plot(self.location, self.tours, name)


class TimeSpaceNetwork:
    def __init__(self, n, verbose=True):
        """
		Intializes a Time-Space Network (class 4)

		Arguments:
			n:                  number of locations

		Attributes:
			location (list):     (x,y) coordinates parsed from .txt file
			dist (list):         (i,j) distance from i to j
			m (gurobipy.Model):  gurobi model used for optimization
			xvars:               decision variables
		"""
        tsp_data = parse_tsp_txt(n)
        self.location = tsp_data[0]
        self.dist = tsp_data[1]
        self.n = n
        self.m = Model()
        self.xvars = tupledict()

        if verbose:
            print('Time Space Network model with {} cities'.format(self.n))

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
        for i in range(self.n):
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
            self.optimize(verbose=True)
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
            self.optimize(verbose=True)
        plot_tsp(self.location, self.tours[0], name)


class NearestNeighbour:
    """
    Initialize a Nearest Neighbour Heuristic

    Arguments:
        n (int) :                       TSP variant, n = 5, 7, 30 or 100

    """

    def __init__(self, n, verbose=False, start=0):
        tsp_data = parse_tsp_txt(n)
        self.location = tsp_data[0]
        self.dist = tsp_data[1]
        self.start = start
        self.n = n

        if verbose:
            print('NearestNeighbour Heuristic with {} cities'.format(self.n))

    def nearest_node(self, i, dj):
        """
        Retrieves nearest node from i to dj

        Arguments:
            i (int)     : origin or source point
            dj (list)   : distances from i to j

        Returns:
            node (int) : index of nearest node
        """
        options = [(j, d) for (j, d) in enumerate(dj)
                   if not i == j and j not in self.tour]
        return min(options, key=lambda option: option[1])[0]

    def calc_obj_val(self):
        """
        Returns the current objective value from its visits
        """
        self.visits = []
        for i in self.tour[:-1]:
            self.visits.append((self.tour[i], self.tour[i + 1]))
        self.objVal = sum([self.dist[i][j] for (i, j) in self.visits])
        return self.objVal

    def optimize(self, verbose=False):
        """
        Visit a nearest node until the tour has visited all points
        """
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
            self.optimize(verbose=True)
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
            self.optimize(verbose=True)
        plot(self.location, [self.tour], name)


class LateAcceptance:
    """
    Late Acceptance Heuristic for TSP problems

    Arguments:
        n            (int)  : TSP variant, n = 5, 7, 30 or 100
        L            (int)  : number of candidates to consider per step
        limit_idle   (bool) : use limit of 1000 steps without improvements,
                              incase limit_idle is not set, use 10,000 steps
                              without considering if a step causes an
                              improvement or not
        verbose      (bool) : enable verbose logging
        random_start (bool) : start the Heuristic with a random solution

    """

    def __init__(self, n, L, limit_idle=True, verbose=True,
                 random_start=False):
        tsp_data = parse_tsp_txt(n)
        self.location = tsp_data[0]
        self.dist = tsp_data[1]
        self.limit_idle = limit_idle
        self.n = n
        self.L = L
        self.visits = []
        self.s = [i for i in range(self.n)]
        if random_start:
            self.s = self.candidate_solution()
        self.C = self.calc_obj_val(self.s)
        self.f = [self.C] * (L)
        self.I = 0
        self.I_idle = 0

        if verbose:
            print('NearestNeighbour Heuristic with {} cities'.format(self.n))

    def random_start_results(self, rand_number, L=None, n=None):
        """
		Runs the Late Heuristic model multiple times with random starts

		Arguments:
			L (int) :           parameter of Late Heuristic Model
			n (int) :           tsp dataset to run on
			rand_number (int) : number of random models (random starts)
		Returns:
			results (list): objective results for each random model start
		"""
        results = []
        if L == None:
            L = self.L
        if n == None:
            n = self.n
        for i in range(rand_number):
            self.__init__(n, L, random_start=True, verbose=False)
            self.optimize()
            results.append(self.ObjVal)

        return results

    def calc_obj_val(self, s):
        self.visits = []
        for i in range(len(s) - 1):
            self.visits.append((s[i], s[i + 1]))
        return sum([self.dist[i][j] for (i, j) in self.visits])

    def candidate_solution(self):
        """
        Generates a random candidate solution, using simple insert/remove
        """
        new_tour = self.s[1:-1]
        r_remove = choice(new_tour)
        r_insert = choice(new_tour)
        new_tour.remove(r_remove)
        new_tour.insert(r_insert, r_remove)
        return [0] + new_tour + [0]

    def optimize(self, verbose=False):
        """
        Optimizes model, with a limit of 1,000 idle steps or 10,000 steps
        """
        if self.limit_idle:
            while not (self.I_idle > 1000):
                self.step()
        else:
            while not (self.I > 10000):
                self.step()
        self.ObjVal = self.C
        if verbose:
            self.print_results()

    def step(self):
        """
        Calculate candidate_solution according to the Late Acceptance Heuristic.
        The idle counter is increased/reset depending on if the
        candidate_solution is lower than the current solution.
        Afterwards, define index v := i mod L and see if the candidate_solution
        can be accepted if it is less than then f[v]
        """
        s_candidate = self.candidate_solution()
        C_candidate = self.calc_obj_val(s_candidate)
        if C_candidate >= self.C:
            self.I_idle += 1
        if C_candidate < self.C:
            self.I_idle = 0
        v = self.I % self.L
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
            self.optimize(verbose=True)
        plot(self.location, [self.tour], name)


class CVRPModel:
    """
    Initializes a Vehicle Routing Problem Model with Capacity constraints:

    Arguments:
        Q       (int)   : capacity constraint of vehicles
        r       (int)   : profit per demand
        K       (int)   : number of vehicles to use
        f       (int)   : fixed cost of using a vehicle
        dist    (list)  : 2D map of n * n customer, where dist[i][j] represents
                          the distance from node i to j
        demand  (list)  : list of demands, where d[0] = 0 (source depot)
    """

    def __init__(self, Q, r, K, f, dist, demand):
        self.m = Model()
        self.n = len(dist)
        self.K = K
        self.dist = dist
        self.demand = demand
        self.Q = Q
        self.r = r

        # (1) Objective Function:

        # (1) Initialize 3-parameter binary values Xijk: vehicle k from i to j
        self.xvars = tupledict()
        for i in range(self.n):
            for j in range(self.n):
                if not i == j:
                    for k in range(self.K):
                        self.xvars[i, j, k] = self.m.addVar(
                            vtype=GRB.BINARY, name=f"x[{i}][{j}][{k}]")

        # (1) Initialize 2-parameter integer variabes Ujk:
        #position of node i in the tour of vehicle k.
        self.uvars = tupledict()

        for k in range(self.K):
            for j in range(self.n):
                self.uvars[j, k] = self.m.addVar(vtype=GRB.INTEGER,
                                                 lb=0,
                                                 ub=self.n,
                                                 name=f"u[{j}][{k}]")
        self.m.update()

        # (1) Transportation costs: sum all binary Xij * Dij
        self.transport_costs = sum([
            self.dist[i][j] * self.xvars.sum(i, j, "*") for i in range(self.n)
            for j in range(self.n)
        ])

        # (1) Fixed fee, every vehicle costs f, so f*K is total vehicle cost
        self.fixed_costs = K * f

        # (1) Revenue of r per demand j for each j visited.
        # Simply sum all variables as we will handle restrictions later on in the constraints
        self.revenue = sum([
            self.demand[j] * self.r * self.xvars.sum("*", j, "*")
            for j in range(self.n)
        ])

        self.m.setObjective(
            (self.revenue - self.transport_costs - self.fixed_costs),
            GRB.MAXIMIZE)

        # (2) Constraint: Only visit each place once
        for j in range(1, self.n):
            self.m.addConstr(self.xvars.sum("*", j, "*") <= 1)

        # (3) Constraint: Only leave each place once
        for i in range(1, self.n):
            self.m.addConstr(self.xvars.sum(i, "*", "*") <= 1)

        for k in range(K):
            # (4) Constraint: each vehicle can visit a place at most once
            for j in range(self.n):
                self.m.addConstr(self.xvars.sum("*", j, self.K) <= 1)

            # (5) Constraint: each vehicle can leave a place at most once
            for i in range(self.n):
                self.m.addConstr(self.xvars.sum(i, "*", self.K) <= 1)

        # (6) If vehicle k visits i, it should also leave i
        for k in range(K):
            for j in range(self.n):
                self.m.addConstr(
                    self.xvars.sum("*", j, k) == self.xvars.sum(j, "*", k))

        # (7) Subtour constraints: each vehicle makes a single tour
        M = self.n - 1
        for i in range(self.n):
            for j in range(1, self.n):
                if not i == j:
                    self.m.addConstr(
                        self.uvars.sum(j, "*") >= self.uvars.sum(i, "*") + 1 -
                        M * (1 - self.xvars.sum(i, j, "*")))

        # (8) Capacity constraints: each vehicle carries at most Q
        for k in range(K):
            self.m.addConstr(
                sum([
                    self.xvars.sum("*", j, k) * self.demand[j]
                    for j in range(self.n)
                ]) <= self.Q)

    def optimize(self):
        """
        Calls gurobis optimize function on the linear program
        """
        self.m.optimize()

    def get_vehicle_tour(self, k):
        """
        Gets the tour for a vehicle resulting from the CVRP

        Arguments:
            k (int) : number of the vehicle to get the tour for

        Returns:
            tour (list) : list of locations visited, starting and ending in
                          location 0 (depot)
        """

        visits = get_visits(self.xvars)
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

    def get_tours(self):
        """
        Get tours for each vehicle in the CVRP

        Returns:
            tour (list) : tour[k] := tour (list) of vehicle k
        """
        return [self.get_vehicle_tour(k) for k in range(self.K)]
