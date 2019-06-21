from helper_functions import parse_tsp_txt
from models import NearestNeighbour
from visualizer import plot, plot_tsp

model3 = NearestNeighbour(30)
model3.optimize(verbose=False)
model3.plot("3_NearestNeighbour")

print("\n| Starting Point | ObjVal | \n| -- | -- |")
for start_city in [2, 16, 17]:
    model = NearestNeighbour(30, start=start_city)
    model.optimize(verbose=False)
    print(f"| {start_city} | {model.objVal} | ")

optimality_gap = 100 * (model3.objVal - 496) / model3.objVal
print(f"Optimality gap: {round(optimality_gap, 2)}%")
