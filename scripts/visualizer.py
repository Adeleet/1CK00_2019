def plot(locations, routes, name):
    import matplotlib.pyplot as plt
    import random
    random.seed(0)

    fig, ax = plt.subplots(figsize=(10,10))
    plt.scatter(*zip(*locations))

    for i,(u,v) in enumerate(locations):
        ax.annotate(i,(u+0.1,v))

    for index, route in enumerate(routes):
        cors=[locations[i] for i in route]
        x,y=zip(*cors)
        color = "#%06x" % random.randint(0, 0xFFFFFF) #random color in hex format
        plt.plot(x,y,  color, linestyle='-', linewidth=2, label='Route {}'.format(index))

    #Plot a legend
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels)

    plt.title(name)
    plt.savefig(name+'.png', bbox_inches='tight')
    plt.show()
    return

def plot_tsp(locations, route, name):
    plot(locations,[route],name)
    return



