from bokeh.plotting import figure
from bokeh.models import ColumnDataSource ,CDSView, HoverTool
from bokeh.models import GraphRenderer, StaticLayoutProvider, Circle
from bokeh.models import Slider, TapTool, MultiLine
from bokeh.layouts import column
from bokeh.models.graphs import  NodesAndLinkedEdges
import numpy as np
import networkx as nx
from tnetwork.visualization.palette import myPalette
import pandas as pd
from datetime import datetime, timedelta
import tnetwork as tn

from bokeh.io import show, output_notebook

def _dyn_graph2CDS(dynamic_net, coms=None,to_datetime=False):

    # construct the dataset
    forData = []
    dates = list(dynamic_net.snapshots_timesteps())
    durations = [dates[i+1]-dates[i] for i in range(len(dates)-1)]


    for i in range(len(dates)):
        if i<len(dates)-1:
            duration = durations[i]
        else:
            duration = np.average(durations)
        t = dates[i]
        if coms != None:
            belongings = coms.belongings_by_node(t)
        for n in dynamic_net.snapshots()[t].nodes:
            comName="no"
            if coms!=None and belongings!=None:
                comName = belongings[n][0]

            forData.append([t, n, comName,duration])
    data = pd.DataFrame(columns=["time", "node", "com","duration"], data=forData)




    # pick a color for each community
    allComs = list(set(data["com"]))
    colorMap = {}
    for i, c in enumerate(allComs):
        if c=="no":
            colorMap[c]="gainsboro"
        else:
            colorMap[c] = myPalette[i % 40]
    data["color"] = [colorMap[c] for c in data["com"]]

    CDS = ColumnDataSource(data)
    CDS.add(np.array([str(data["time"][i]) + "_" + str(n) for i, n in enumerate(data["node"])]), "index")

    if to_datetime!=False:
        CDS.data["time"] = [to_datetime(x) for x in CDS.data["time"]]
        CDS.data["duration"] = [timedelta(seconds=x) for x in CDS.data["duration"]]

    return CDS

def _unique_positions(dynamic_graph,):
    cumulated = dynamic_graph.cumulated_graph()
    positions = nx.fruchterman_reingold_layout(cumulated)
    return(positions)

def _init_net(dynamic_net, communities, currentT, width,height,to_datetime):
    CDS = _dyn_graph2CDS(dynamic_net, communities,to_datetime)

    ht = HoverTool(
        tooltips=[
            ("name", "@node"),
            ("community", "@com")
        ])

    if to_datetime!=False:
        ht.tooltips.append(("time", "@time{%F %H:%M}"))
        ht.formatters = {
            'time': 'datetime'
        }

    tools = [ "reset","pan","wheel_zoom",ht ]

    plot = figure(title="Graph Layout", x_range=(-1.1, 1.1), y_range=(-1.1, 1.1),
                       tools=tools, plot_width=width, plot_height=height)
    plot.xaxis.visible = False
    plot.yaxis.visible = False

    plot.add_tools( TapTool())
    graph_plot = GraphRenderer()
    graph_plot.node_renderer.data_source = CDS

    graph_plot.node_renderer.glyph = Circle(size=15, fill_color="color")
    graph_plot.node_renderer.hover_glyph = Circle(size=15, fill_color=myPalette[-1])
    unique_pos = _unique_positions(dynamic_net)
    unique_pos = {str(currentT) + "_" + str(n): position for n, position in unique_pos.items()}
    graph_plot.layout_provider = StaticLayoutProvider(graph_layout=unique_pos)

    graph_plot.edge_renderer.selection_glyph = MultiLine(line_color="orange", line_width=5)
    graph_plot.selection_policy = NodesAndLinkedEdges()



    _update_net(currentT,graph_plot,dynamic_net)
    plot.renderers.append(graph_plot)
    return(plot,graph_plot)

def _update_net(currentT, graph_plot, dynamic_net):
    """

    :param currentT:
    :param graph_plot:
    :param dynamic_net:
    :return:
    """
    if currentT in dynamic_net.snapshots_timesteps():
        CDS = graph_plot.node_renderer.data_source

        graph_plot.node_renderer.view = CDSView(source=CDS)

        node_positions =graph_plot.layout_provider.__getattribute__("graph_layout")
        graph_plot.layout_provider = StaticLayoutProvider(
            graph_layout={str(currentT) + "_" + n.split("_")[1]: position for n, position in node_positions.items()})

        edges = dynamic_net.snapshots()[currentT].edges()
        n1s = []
        n2s = []
        for (n1, n2) in edges:
            n1s.append(str(currentT) + "_" + str(n1))
            n2s.append(str(currentT) + "_" + str(n2))

        graph_plot.edge_renderer.data_source.data = dict(
            start=n1s,
            end=n2s)



def plot_as_graph(dynamic_graph, communities=None, t=None,to_datetime=False, width=800,height=600,auto_show=False):
    """
    Interactive plot to see the static graph at each snapshot

    :param dynamic_graph: a dynamic network
    :param communities: dynamic communities of the network
    :param t: time of the first snapshot to display
    :param to_datetime: one of True/False/function. If True, step IDs are converted to dates using datetime.utcfromtimestamp. If a function, should take a step ID and return a datetime object.
    :param width: width of the figure
    :param height: height of the figure
    :return: bokeh layout containing slider and plot
    """

    if to_datetime==True:
        to_datetime=datetime.utcfromtimestamp

    if t == None:
        t = dynamic_graph.snapshots_timesteps()[0]

    (a_figure,a_graph_plot) = _init_net(dynamic_graph,communities,t,width,height,to_datetime)




    if t==None:
        allTimes = dynamic_graph.snapshots_timesteps()
        slider_Step = min([allTimes[i+1]-allTimes[i] for i in range(0,len(allTimes)-1)])

        slider = Slider(start=dynamic_graph.snapshots_timesteps()[0], end=dynamic_graph.snapshots_timesteps()[-1], value=t,
                        step=slider_Step, title="Plotted_step")




        def update_graph(a, oldt, newt):
            _update_net(newt,a_graph_plot,dynamic_graph)

        slider.on_change('value', update_graph)


        layout = column(slider, a_figure)
    else:
        layout=a_figure



    if auto_show:
        def modify_doc(doc):
            doc.add_root(layout)
        output_notebook()
        show(modify_doc)

    return(layout)










def plot_longitudinal(dynamic_graph,communities=None, sn_duration=None,to_datetime=False, width=800,height=600,auto_show=False):
    """
    Plot communities such as each node corresponds to an horizontal line and time corresponds to the horizontal axis
    :param dynamic_graph: a dynamic network
    :param communities: dynamic communities
    :param sn_duration: the duration of a snapshot, as int or timedelta. If none, inferred automatically as lasting until next snpashot
    :param to_datetime: one of True/False/function. If True, step IDs are converted to dates using datetime.utcfromtimestamp. If a function, should take a step ID and return a datetime object.
    :param width: width of the figure
    :param height: height of the figure
    """

    if to_datetime==True:
        to_datetime=datetime.utcfromtimestamp
    CDS = _dyn_graph2CDS(dynamic_graph,communities,to_datetime=to_datetime)
    if sn_duration!=None:
        CDS.data["duration"] = [sn_duration]*len(CDS.data["time"])
    #CDS.data["time"] = [times[i]+duration[i]/2 for i in range(len(times))]


    #if to_datetime!=False:
    #    CDS.data["time_shift"] = [CDS.data["time"]+CDS.data["duration"][i]]
    #else:

    #should work for timedelta and integers
    CDS.data["time_shift"] = [CDS.data["time"][i] + CDS.data["duration"][i] / 2 for i in range(len(CDS.data["duration"]))]


    tools = ["reset","pan","wheel_zoom" ]
    ht = HoverTool(
        tooltips=[
            ("name", "@node"),
            ("community", "@com"),
            ("time", "@time")
        ])
    ht.point_policy="follow_mouse"
    nodeList = sorted(list(set(CDS.data["node"])))

    x_column = "time_shift"
    x_axis_type = "auto"
    if to_datetime!=False:
        x_axis_type="datetime"
        #CDS.data["time_f"] = [to_datetime(x) for x in CDS.data["time_shift"]]
        #x_column = "time_f"
        ht.tooltips = ht.tooltips[:-1]+[ ("time", "@time{%F %H:%M}")]
        ht.formatters={
                'time': 'datetime'
            }


    tools.append(ht)
    longi = figure(plot_width=width, plot_height=height, y_range=nodeList, tools=tools,x_axis_type=x_axis_type)



    longi.rect(x=x_column, y="node", width="duration", height=0.9, fill_color="color", hover_color="grey", source=CDS,
               line_color=None)


    longi.xgrid.grid_line_color = None
    longi.ygrid.grid_line_color = None



    if auto_show:
        def modify_doc(doc):
            doc.add_root(longi)
        output_notebook()

        show(modify_doc)
    else:
        return (longi)

def plot_longitudinal_sn_clusters(dynamic_graph,clusters,level=None, sn_duration=None,to_datetime=False,width=800,height=600,auto_show=False):
    """
    Plot clusters of snapshots

    If clusters is a list of set, plot each node, otherwise plot the hierarchy of clusters. If levels is not None, plot this level as a single cluster.
    :param dynamic_graph: a dynamic network
    :param clusters: clusters.
    :param sn_duration: the duration of a snapshot, as int or timedelta. If none, inferred automatically as lasting until next snpashot
    :param to_datetime: one of True/False/function. If True, step IDs are converted to dates using datetime.utcfromtimestamp. If a function, should take a step ID and return a datetime object.
    :param width: width of the figure
    :param height: height of the figure
    """
    if level!=None: #single level
        clusters = clusters[level]
    coms = tn.DynamicCommunitiesSN()
    for i,cl in enumerate(clusters): #cl: a cluster
        for t in cl: #cn: a
            coms.add_community(t, com=dynamic_graph.snapshots(t).nodes, id=i)

    return plot_longitudinal(dynamic_graph,communities=coms, sn_duration=sn_duration,to_datetime=to_datetime, width=width,height=height,auto_show=auto_show)


