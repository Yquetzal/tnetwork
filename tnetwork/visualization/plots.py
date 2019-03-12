import bokeh
import bokeh.plotting
# from bokeh.models import ColumnDataSource ,CDSView, HoverTool
# from bokeh.models import GraphRenderer, StaticLayoutProvider, Circle
# from bokeh.models import Slider, TapTool, MultiLine
# from bokeh.layouts import column
# from bokeh.io import show, output_notebook


import numpy as np
import networkx as nx
from tnetwork.visualization.palette import myPalette
import pandas as pd
from datetime import datetime, timedelta
import tnetwork as tn


def _sg_graph2CDS(dynamic_net:tn.DynGraphIG, coms:tn.DynCommunitiesIG=None, to_datetime=False):

    forData = []

    for n,periods in dynamic_net.node_presence().items():
        for (start,end) in periods.periods():
            forData.append([start, n, "no", end-start])

    if coms != None:
        for n,belongings in coms.affiliations.items():
            for com,periods in belongings.items():
                for (start,end) in periods.periods():
                    forData.append([start, n, com, end - start])

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

    CDS = bokeh.models.ColumnDataSource(data)
    CDS.add(np.array([str(data["time"][i]) + "|" + str(n) for i, n in enumerate(data["node"])]), "index")

    if to_datetime!=False:
        CDS.data["time"] = [to_datetime(x) for x in CDS.data["time"]]
        CDS.data["duration"] = [timedelta(seconds=x) for x in CDS.data["duration"]]

    return CDS


def _sn_graph2CDS(dynamic_net, coms=None, to_datetime=False):

    # construct the dataset
    forData = []
    dates = list(dynamic_net.snapshots_timesteps())
    durations = [dates[i+1]-dates[i] for i in range(len(dates)-1)]


    for i in range(len(dates)):
        if i<len(dates)-1:
            duration = durations[i]
        else:
            duration = np.min(durations)

        t = dates[i]
        if coms != None:
            belongings = coms.affiliations(t)
            for n in belongings:
                belongings[n] = belongings[n][0] #keep only onl

        for n in dynamic_net.snapshots()[t].nodes:
            comName="no"
            if coms!=None and belongings!=None:
                if n in belongings:
                    comName = belongings[n]

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

    CDS = bokeh.models.ColumnDataSource(data)
    CDS.add(np.array([str(data["time"][i]) + "|" + str(n) for i, n in enumerate(data["node"])]), "index")

    if to_datetime!=False:
        CDS.data["time"] = [to_datetime(x) for x in CDS.data["time"]]
        CDS.data["duration"] = [timedelta(seconds=x) for x in CDS.data["duration"]]

    return CDS

def _unique_positions(dynamic_graph,):
    cumulated = dynamic_graph.cumulated_graph()
    positions = nx.fruchterman_reingold_layout(cumulated)
    return(positions)

def _init_net(dynamic_net, communities, currentT, width,height,to_datetime):
    CDS = _sn_graph2CDS(dynamic_net, communities, to_datetime)
    ht = bokeh.models.HoverTool(
        tooltips=[
            ("name", "@node"),
            ("community", "@com")
        ])

    if to_datetime!=False:
        ht.tooltips.append(("time", "@time{%F %H:%M}"))
        ht.formatters = {
            'time': 'datetime'
        }

    tools = [ "reset","pan","wheel_zoom","save",ht ]

    plot = bokeh.plotting.figure(title="Graph Layout", x_range=(-1.1, 1.1), y_range=(-1.1, 1.1),
                       tools=tools, plot_width=width, plot_height=height,active_scroll="wheel_zoom")
    plot.output_backend = "svg"

    plot.xaxis.visible = False
    plot.yaxis.visible = False

    plot.add_tools( bokeh.models.TapTool())
    graph_plot = bokeh.models.GraphRenderer()
    graph_plot.node_renderer.data_source = CDS

    graph_plot.node_renderer.glyph = bokeh.models.Circle(size=15, fill_color="color")
    graph_plot.node_renderer.hover_glyph = bokeh.models.Circle(size=15, fill_color=myPalette[-1])
    unique_pos = _unique_positions(dynamic_net)
    unique_pos = {str(currentT) + "|" + str(n): position for n, position in unique_pos.items()}
    graph_plot.layout_provider = bokeh.models.StaticLayoutProvider(graph_layout=unique_pos)

    graph_plot.edge_renderer.selection_glyph = bokeh.models.MultiLine(line_color="orange", line_width=5)
 #   graph_plot.selection_policy = NodesAndLinkedEdges()



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

        graph_plot.node_renderer.view = bokeh.models.CDSView(source=CDS)

        node_positions =graph_plot.layout_provider.__getattribute__("graph_layout")
        graph_plot.layout_provider = bokeh.models.StaticLayoutProvider(
            graph_layout={str(currentT) + "|" + n.split("|")[1]: position for n, position in node_positions.items()})

        edges = dynamic_net.affiliations()[currentT].edges()
        print(edges)
        n1s = []
        n2s = []
        for (n1, n2) in edges:
            n1s.append(str(currentT) + "|" + str(n1))
            n2s.append(str(currentT) + "|" + str(n2))
        graph_plot.edge_renderer.data_source.data = dict(
            start=n1s,
            end=n2s)



def plot_as_graph(dynamic_graph, communities=None, t=None,to_datetime=False, width=800,height=600,auto_show=False):
    """
    Interactive plot to see the static graph at each snapshot

    :param dynamic_graph: DynGraphSN
    :param communities: dynamic affiliations of the network (can be ignored)
    :param t: time of the snapshot to display. If None, a slider allows to interactively choose the step (work only in jupyter notebooks on a local machine)
    :param to_datetime: one of True/False/function. If True, step IDs are converted to dates using datetime.utcfromtimestamp. If a function, should take a step ID and return a datetime object.
    :param width: width of the figure
    :param height: height of the figure
    :param auto_show: if True, the plot is directly displayed in a jupyter notebook. In any other setting, should be False, and the graph should be displayed as any bokeh plot, depending on the setting.
    :return: bokeh layout containing slider and plot, or only plot if no slider.
    """
    if isinstance(dynamic_graph, tn.DynGraphIG):
        raise Exception("currently, only snapshot graphs are supported, please convert using DynGraphSG.to_DynGraphSN()")
    slider_bool=False
    if to_datetime==True:
        to_datetime=datetime.utcfromtimestamp

    if t == None:
        t = dynamic_graph.snapshots_timesteps()[0]
        slider_bool=True

    (a_figure,a_graph_plot) = _init_net(dynamic_graph,communities,t,width,height,to_datetime)




    if slider_bool:
        allTimes = dynamic_graph.snapshots_timesteps()
        slider_Step = min([allTimes[i+1]-allTimes[i] for i in range(0,len(allTimes)-1)])

        slider = bokeh.models.Slider(start=dynamic_graph.snapshots_timesteps()[0], end=dynamic_graph.snapshots_timesteps()[-1], value=t,
                        step=slider_Step, title="Plotted_step")#,callback_policy="mouseup")




        def update_graph(a, oldt, newt):
            _update_net(newt,a_graph_plot,dynamic_graph)

        slider.on_change('value', update_graph)


        layout = bokeh.layouts.column(slider, a_figure)
    else:
        layout=a_figure



    if auto_show:
        def modify_doc(doc):
            doc.add_root(layout)
        bokeh.io.output_notebook()
        bokeh.io.show(modify_doc)

    return(layout)










def plot_longitudinal(dynamic_graph,communities=None, sn_duration=None,to_datetime=False, nodes=None,width=800,height=600,auto_show=False):
    """
    A longitudinal view of nodes/communities

    Plot affiliations such as each node corresponds to a horizontal line and time corresponds to the horizontal axis

    :param dynamic_graph: DynGraphSN or DynGraphIG
    :param communities: dynamic affiliations, DynCommunitiesSN or DynCommunitiesIG
    :param sn_duration: the duration of a snapshot, as int or timedelta. If none, inferred automatically as lasting until next snpashot
    :param to_datetime: one of True/False/function. If True, step IDs are converted to dates using datetime.utcfromtimestamp. If a function, should take a step ID and return a datetime object.
    :param nodes: If none, plot all nodes in lexicographic order. If a list of nodes, plot only those nodes, in that order
    :param width: width of the figure
    :param height: height of the figure
    """

    if to_datetime==True:
        to_datetime=datetime.utcfromtimestamp

    if isinstance(dynamic_graph,tn.DynGraphSN):
        CDS = _sn_graph2CDS(dynamic_graph, communities, to_datetime=to_datetime)
    else:
        CDS = _sg_graph2CDS(dynamic_graph, communities, to_datetime=to_datetime)

    if sn_duration!=None:
        CDS.data["duration"] = [sn_duration]*len(CDS.data["time"])
    CDS.data["duration_display"]=CDS.data["duration"]
    CDS.data["duration"] = [v+0.1 for v in CDS.data["duration"]]

    #should work for timedelta and integers
    CDS.data["time_shift"] = [CDS.data["time"][i] + CDS.data["duration"][i] / 2 for i in range(len(CDS.data["duration"]))]


    tools = ["reset","wheel_zoom","box_zoom","pan","save"]
    ht = bokeh.models.HoverTool(
        tooltips=[
            ("name", "@node"),
            ("community", "@com"),
            ("start", "@time"),
            ("duration","@{duration_display}")
        ])
    #        <style>
    #        .bk-tooltip>div:not(:first-child) {display:none;}
    #    </style>""")
    ht.point_policy="follow_mouse"
    if nodes==None:
        nodes = sorted(list(set(CDS.data["node"])))

    x_column = "time_shift"
    x_axis_type = "auto"
    if to_datetime!=False:
        x_axis_type="datetime"
        #CDS.data["time_f"] = [to_datetime(x) for x in CDS.data["time_shift"]]
        #x_column = "time_f"
        ht.tooltips = ht.tooltips+[ ("time", "@time{%F %H:%M}")]
        ht.formatters={
                'start': 'datetime'
            }


    tools.append(ht)
    longi = bokeh.plotting.figure(plot_width=width, plot_height=height, y_range=nodes, tools=tools,x_axis_type=x_axis_type)#,active_scroll="wheel_zoom"
    longi.output_backend = "svg"


    longi.rect(x=x_column, y="node", width="duration", height=0.9, fill_color="color", hover_color="grey", source=CDS,
               line_color=None,line_width=0)


    longi.xgrid.grid_line_color = None
    longi.ygrid.grid_line_color = None



    if auto_show:
        def modify_doc(doc):
            doc.add_root(longi)
            bokeh.iooutput_notebook()

        bokeh.ioshow(modify_doc)
    else:
        return (longi)

def plot_longitudinal_sn_clusters(dynamic_graph,clusters,level=None, **kwargs):
    """
    A longitudinal view of snapshot clusters

    Snapshot clusters are a way to represent periods of the dynamic graphs similar in some way. It is similar to dynamic communities,
    but all nodes of a snapshot belongs always to the same "community".

    Optional parameters (kwargs) are the same as for plot_longitudinal.

    :param dynamic_graph:  DynGraphSN or DynGraphIG
    :param clusters: clusters as a set of set of partitions ID. Can also be a hierarchical partitioning, represented as a list of clusters. The level to display is in this case decided by the level parameter
    :param level: if clusters is a hierarchical clustering, the level to display
    """
    if level!=None: #single level
        clusters = clusters[level]
    coms = tn.DynCommunitiesSN()
    for i,cl in enumerate(clusters): #cl: a cluster
        for t in cl:
            coms.add_community(t, nodes=dynamic_graph.affiliations(t).nodes, id=i)
    if isinstance(dynamic_graph, tn.DynGraphIG):
        coms = coms.to_SGcommunities()
    return plot_longitudinal(dynamic_graph,communities=coms, **kwargs)


