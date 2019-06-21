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


def get_tours(visits):
    """
    Returns tours[], where each tour is a (sub)tour using the selected visits
    If there are no subtours, tours is a list containing a single (complete)
    tour

    Parameters:
        xvars (gurobipy.tupledict) : Selected Xij variables of the optimized model
        visits (list)              : List of tuples (i,j) obtained from get_visits

    Returns:
        tours (list) : ordered list of locations of (sub)tours

    """
    n = len(visits)
    is_timespace = len(visits[0]) == 3

    # Timespace tour
    if is_timespace:
        tour = []
        visits_dict = dict(zip([v[0] for v in visits], [v[1] for v in visits]))
        key = 0

        for i in range(n + 1):
            tour.append(key)
            key = visits_dict[key]
        return [tour]

    # Non-timespace tour
    visited = [False] * n
    tours = []
    for i in range(n):
        if visited[i]:
            continue
        j = i
        new_tour = []
        while not visited[j]:
            visited[j] = True
            new_tour.append(j)
            j = visits[j][1]
        new_tour.append(new_tour[0])
        tours.append(new_tour)
    return tours


def get_visits(xvars):
    """
    Returns xvars as tuples (i,j) where Xij = 1

    Parameters:
        xvars (gurobipy.tupledict) : Selected Xij variables of the optimized model
        timespace (bool)           : Boolean indicating if timespace model

    Returns
        If a timespace model is used:
            visits (list) : List of tuples (i,j,t) that are selected (Xij = 1)
        If a timespace model is not used:
            visits (list) : List of tuples (i,j) that are selected (Xij = 1)
    """
    is_timespace = len(list(xvars)[0]) == 3
    if is_timespace:
        visits = [var[0] for var in xvars.iteritems() if var[1].X == 1]
        return sorted(visits, key=lambda visit: visit[2])

    n = max(xvars.keys())[0] + 1
    visits = []
    for i in range(n):
        for j in range(n):
            if not i == j and xvars[i, j].X == 1:
                visits.append((i, j))
    return sorted(visits, key=lambda visit: visit[0])
