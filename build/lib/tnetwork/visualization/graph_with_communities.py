from bokeh.plotting import figure
from bokeh.models import ColumnDataSource ,CDSView
from bokeh.models import GraphRenderer, StaticLayoutProvider, Circle
from bokeh.models import Slider
from bokeh.layouts import column

import numpy as np
import networkx as nx
from tnetwork.visualization.palette import myPalette
import pandas as pd

from bokeh.io import show, output_notebook

def _communities2CDS(coms):

    # construct the dataset
    forData = []
    dates = list(coms.snapshots().keys())
    durations = [dates[i+1]-dates[i] for i in range(len(dates)-1)]


    for i in range(len(dates)):
        if i<len(dates)-1:
            duration = durations[i]
        else:
            duration = np.average(durations)
        (t,part) = coms.snapshots().peekitem(i)
        for nodes, comName in part.items():
            for n in nodes:
                forData.append([t, n, comName,duration])
    data = pd.DataFrame(columns=["time", "node", "com","duration"], data=forData)

    # pick a color for each community
    allComs = list(set(data["com"]))
    colorMap = {}
    for i, c in enumerate(allComs):
        colorMap[c] = myPalette[i % 40]
    data["color"] = [colorMap[c] for c in data["com"]]

    CDS = ColumnDataSource(data)
    CDS.add(np.array([str(data["time"][i]) + "_" + str(n) for i, n in enumerate(data["node"])]), "index")
    return CDS

def _unique_positions(dynamic_graph):
    cumulated = dynamic_graph.cumulated_graph()
    positions = nx.fruchterman_reingold_layout(cumulated)
    return(positions)

def _init_net(dynamic_net, communities, currentT, width,height):
    CDS = _communities2CDS(communities)
    TOOLTIPS = [
        ("name", "@node"),
        ("community", "@com")
    ]
    tools = ["box_select", "reset"]

    plot = figure(title="Graph Layout", x_range=(-1.1, 1.1), y_range=(-1.1, 1.1),
                       tools=tools, plot_width=width, plot_height=height, tooltips=TOOLTIPS)

    graph_plot = GraphRenderer()
    graph_plot.node_renderer.data_source = CDS

    graph_plot.node_renderer.glyph = Circle(size=15, fill_color="color")
    graph_plot.node_renderer.hover_glyph = Circle(size=15, fill_color=myPalette[-1])
    unique_pos = _unique_positions(dynamic_net)
    unique_pos = {str(currentT) + "_" + n: position for n, position in unique_pos.items()}
    graph_plot.layout_provider = StaticLayoutProvider(graph_layout=unique_pos)

    _update_net(currentT,graph_plot,dynamic_net)
    plot.renderers.append(graph_plot)
    return(plot,graph_plot)

def _update_net(currentT, graph_plot, dynamic_net):
    CDS = graph_plot.node_renderer.data_source

    graph_plot.node_renderer.view = CDSView(source=CDS)

    node_positions =graph_plot.layout_provider.__getattribute__("graph_layout")
    graph_plot.layout_provider = StaticLayoutProvider(
        graph_layout={str(currentT) + "_" + n.split("_")[1]: position for n, position in node_positions.items()})

    edges = dynamic_net.snapshots()[currentT].edges()
    n1s = []
    n2s = []
    for (n1, n2) in edges:
        n1s.append(str(currentT) + "_" + n1)
        n2s.append(str(currentT) + "_" + n2)

    graph_plot.edge_renderer.data_source.data = dict(
        start=n1s,
        end=n2s)



def plot_as_graph(dynamic_graph, communities, t=None, width=800,height=600):
    """
    Plot an interactive network allowing to see the topology of the network at time t.
    :param dynamic_graph: a dynamic network
    :param communities: dynamic snapshots of the network
    :param t: time of the first snapshot to display
    :param width: width of the figure
    :param height: height of the figure
    """

    if t == None:
        t = dynamic_graph.snapshots_timesteps()[0]

    (a_figure,a_graph_plot) = _init_net(dynamic_graph,communities,t,width,height)

    allTimes = dynamic_graph.snapshots_timesteps()
    slider_Step = min([allTimes[i+1]-allTimes[i] for i in range(0,len(allTimes)-1)])
    slider = Slider(start=dynamic_graph.snapshots_timesteps()[0], end=dynamic_graph.snapshots_timesteps()[-1], value=t,
                    step=slider_Step, title="step")




    def update_graph(a, oldt, newt):
        _update_net(newt,a_graph_plot,dynamic_graph)

    slider.on_change('value', update_graph)

    output_notebook()

    layout = column(slider, a_figure)

    def modify_doc(doc):
        doc.add_root(layout)

    show(modify_doc)










def plot_longitudinal(communities, width=800,height=600):
    """
    Plot snapshots such as each node corresponds to an horizontal line and time corresponds to the horizontal axis
    :param communities: dynamic snapshots
    :param width: width of the figure
    :param height: height of the figure
    """

    CDS = _communities2CDS(communities)

    TOOLTIPS = [
        ("name", "@node"),
        ("community", "@com")
    ]


    tools = ["box_select", "reset"]

    nodeList = sorted(list(set(CDS.data["node"])))
    longi = figure(plot_width=width, plot_height=height, y_range=nodeList, tools=tools,tooltips=TOOLTIPS)
    longi.rect(x="time", y="node", width="duration", height=0.9, fill_color="color", hover_color="grey", source=CDS,
               line_color=None)


    longi.xgrid.grid_line_color = None
    longi.ygrid.grid_line_color = None

    def modify_doc(doc):
        doc.add_root(longi)

    output_notebook()

    show(modify_doc)