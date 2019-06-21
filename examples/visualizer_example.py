from visualizer import plot, plot_tsp

#Example of how to use visualizer.py

#Print a VRP solution. Locations are pairs of x/y coordinates,
#routes is a 2-d list representing the routes. The variable
#name is used as the title of the graph, and is also the name of the
#output file.

locations = [(1, 2), (2, 3), (5, 0), (4, 8), (5, 9)]
routes = [[0, 1, 2, 0], [0, 3, 4, 0]]
name = "VRP"

plot(locations, routes, name)

#Print a TSP solution. Locations are pairs of x/y coordinates,
#route is a list representing the TSP tour. The variable
#name is used as the title of the graph, and is also the name of the
#output file.

# locations=[(1,2),(2,3),(5,0),(4,8),(5,9)]
# route=[0,1,2,3,4,0]
# name="TSP"
# plot_tsp(locations,route,name)
