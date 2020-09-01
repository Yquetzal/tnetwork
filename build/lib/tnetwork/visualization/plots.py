import bokeh
import bokeh.plotting

import numpy as np
import networkx as nx
from tnetwork.visualization.palette import myPalette
import pandas as pd
from datetime import datetime, timedelta
import tnetwork as tn

import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle
from matplotlib.dates import AutoDateFormatter, AutoDateLocator, date2num

import math

def _add_node_periods(dynamic_net:tn.DynGraphIG,forData):
    for n,periods in dynamic_net.node_presence().items():
        if periods!=None:
            for (start,end) in periods.periods():
                forData.append([start, n, "no", end-start])

def _add_communities_periods(coms:tn.DynCommunitiesIG,forData):
    for n, belongings in coms.affiliations().items():
        for com, periods in belongings.items():
            for (start, end) in periods.periods():
                forData.append([start, str(n), com, end - start])

def _create_com_colormap(data):
    allComs = sorted(list(set(data["com"])))
    if "no" in allComs:
        allComs.remove("no")
    colorMap = {}
    colorMap["no"] = "gainsboro"
    for i, c in enumerate(allComs):
        colorMap[c] = myPalette[i % 40]
    data["color"] = [colorMap[c] for c in data["com"]]
    return data

def _handle_time(CDS,to_datetime):
    CDS.add(np.array([str(CDS.data["time"][i]) + "|" + str(n) for i, n in enumerate(CDS.data["node"])]), "index")

    if to_datetime != False:
        CDS.data["time"] = [to_datetime(x) for x in CDS.data["time"]]
        CDS.data["duration"] = [timedelta(seconds=int(x)) for x in CDS.data["duration"]]
    return CDS

def _ig_graph2CDS(dynamic_net:tn.DynGraphIG, coms:tn.DynCommunitiesIG=None, to_datetime=False):
    forData = []
    _add_node_periods(dynamic_net,forData)


    if coms != None:
        _add_communities_periods(coms,forData)

    data = pd.DataFrame(columns=["time", "node", "com","duration"], data=forData)

    # pick a color for each community
    data = _create_com_colormap(data)

    CDS = bokeh.models.ColumnDataSource(data)

    CDS = _handle_time(CDS,to_datetime)
    return CDS

def _ls_graph2CDS(dynamic_net:tn.DynGraphLS, coms:tn.DynCommunitiesIG=None, to_datetime=False):

    frequency = dynamic_net.frequency()
    forData = []
    _add_node_periods(dynamic_net,forData)
    if len(forData)==0:
        for n,times in dynamic_net.nodes_interactions().items():
            for t in times:
                forData.append([t, str(n), "black", frequency])


    if coms != None:
        _add_communities_periods(coms,forData)



    data = pd.DataFrame(columns=["time", "node", "com","duration"], data=forData)

    # pick a color for each community
    data = _create_com_colormap(data)

    CDS = bokeh.models.ColumnDataSource(data)

    CDS = _handle_time(CDS,to_datetime)
    return CDS

def _sn_graph2CDS(dynamic_net, coms=None, to_datetime=False,ts=None):

    allComs=[]
    if coms!=None:
        allComs = sorted(list(coms.communities().keys()))
        if "no" in allComs:
            allComs.remove("no")
    forData = []
    dates = ts

    durations = [dates[i+1]-dates[i] for i in range(len(dates)-1)]

    if len(durations)==0:
        final_duration=1
    else:
        final_duration=np.min(durations)

    for i in range(len(dates)):
        nodesInGraph=[]
        belongings={}
        t = dates[i]

        if t in dynamic_net.snapshots():
            nodesInGraph = list(dynamic_net.snapshots(t).nodes())

        if i<len(dates)-1:
            duration = durations[i]
        else:
            duration = final_duration

        if coms != None:
            belongings_temp = coms.snapshot_affiliations(t)
            if belongings_temp != None:
                for n in belongings_temp:
                    belongings[n] = list(belongings_temp[n])[0]


        nodesGraphAndComs = set(nodesInGraph + list(belongings.keys()))
        for n in nodesGraphAndComs:
            comName="no"
            if coms!=None and belongings!=None:
                if n in belongings:
                    comName = belongings[n]

            forData.append([t, str(n), comName,duration])
    data = pd.DataFrame(columns=["time", "node", "com","duration"], data=forData)


    # pick a color for each community
    # colorMap = {}
    # colorMap["no"]="gainsboro"
    # for i, c in enumerate(allComs):
    #     colorMap[c] = myPalette[i % 40]
    # data["color"] = [colorMap[c] for c in data["com"]]
    data = _create_com_colormap(data)

    CDS = bokeh.models.ColumnDataSource(data)
    CDS = _handle_time(CDS, to_datetime)
    # CDS.add(np.array([str(data["time"][i]) + "|" + str(n) for i, n in enumerate(data["node"])]), "index")
    #
    # if to_datetime!=False:
    #     CDS.data["time"] = [to_datetime(x) for x in CDS.data["time"]]
    #     CDS.data["duration"] = [timedelta(seconds=int(x)) for x in CDS.data["duration"]]

    return CDS

def _unique_positions(dynamic_graph,ts,**kwargs):
    cumulated = dynamic_graph.cumulated_graph(ts)
    positions = nx.spring_layout(cumulated,**kwargs)
    return(positions)

def _init_net_properties(dynamic_net,CDS,unique_pos,currentT, width, height, to_datetime):
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

    plot = bokeh.plotting.figure(title="t= "+str(currentT), x_range=(-1.1, 1.1), y_range=(-1.1, 1.1),
                       tools=tools, plot_width=width, plot_height=height,active_scroll="wheel_zoom")
    plot.output_backend = "svg"

    plot.xaxis.visible = False
    plot.yaxis.visible = False

    plot.add_tools( bokeh.models.TapTool())
    graph_plot = bokeh.models.GraphRenderer()
    graph_plot.node_renderer.data_source = CDS

    graph_plot.node_renderer.glyph = bokeh.models.Circle(size=15, fill_color="color")
    graph_plot.node_renderer.hover_glyph = bokeh.models.Circle(size=15, fill_color=myPalette[-1])


    unique_pos = {str(currentT) + "|" + str(n): position for n, position in unique_pos.items()}
    graph_plot.layout_provider = bokeh.models.StaticLayoutProvider(graph_layout=unique_pos)

    graph_plot.edge_renderer.glyph = bokeh.models.MultiLine(line_color="#CCCCCC", line_alpha=0.8)
    graph_plot.edge_renderer.selection_glyph = bokeh.models.MultiLine(line_color="orange", line_width=5)
    graph_plot.edge_renderer.hover_glyph = bokeh.models.MultiLine(line_color="green", line_width=5)

    #graph_plot.inspection_policy = bokeh.models.graphs.EdgesAndLinkedNodes()



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

        edges = dynamic_net.graph_at_time(currentT).edges()
        n1s = []
        n2s = []
        for (n1, n2) in edges:
            n1s.append(str(currentT) + "|" + str(n1))
            n2s.append(str(currentT) + "|" + str(n2))
        graph_plot.edge_renderer.data_source.data = dict(
            start=n1s,
            end=n2s)


def _plot_as_graph_nx(ts,dynamic_graph,CDS,unique_pos,width,height,to_datetime):

    colors_all = {}
    #extract colors for graphs
    for i in range(len(CDS.data["color"])):
        t = CDS.data["time"][i]
        node = CDS.data["node"][i]
        c = CDS.data["color"][i]
        colors_all.setdefault(t,{})
        colors_all[t][node]=c



    for i,current_t in enumerate(ts):
        #(a_figure, a_graph_plot) = _init_net_properties(dynamic_graph, CDS, unique_pos, current_t, width, height,
                                                        #to_datetime)
        #list_of_figures.append(a_figure)
        ax = plt.subplot(1,len(ts),i+1)
        ax.title.set_text('t='+str(current_t))
        #fig = plt.figure(figsize=(width, height))
        ax.figure.set_dpi(100)
        ax.figure.set_size_inches(width/100*len(ts), height/100)
        graph = dynamic_graph.graph_at_time(current_t)
        nodes = graph.nodes()
        colors = [colors_all[current_t][str(n)] for n in nodes]

        nx.draw_networkx(graph,pos=unique_pos,node_color=colors,with_labels=False,node_size=50,linewidths=1,edge_color="#CCCCCC")
    #plt.show()
    return plt.gcf()

def _plot_as_graph_bokeh(ts,slider,dynamic_graph,CDS,unique_pos,width,height,to_datetime,auto_show):
    if not slider:
        list_of_figures = []
        for current_t in ts:
            (a_figure, a_graph_plot) = _init_net_properties(dynamic_graph, CDS, unique_pos, current_t, width, height, to_datetime)
            list_of_figures.append(a_figure)
        layout = bokeh.layouts.row(list_of_figures)

    else:
        init_t = ts[0]
        #slider_Step = min([allTimes[i+1]-allTimes[i] for i in range(0,len(allTimes)-1)])
        slider_Step = 1
        slider_object = bokeh.models.Slider(start=0, end=len(ts), value=init_t,
                                            step=1, title="Plotted_step")#,callback_policy="mouseup")

        (a_figure, a_graph_plot) = _init_net_properties(dynamic_graph, CDS, unique_pos, init_t, width,
                                                        height, to_datetime)

        def update_graph(a, oldt, newt):
            _update_net(ts[newt], a_graph_plot, dynamic_graph)

        slider_object.on_change('value', update_graph)

        layout = bokeh.layouts.column(slider_object, a_figure)




    if auto_show:
       def modify_doc(doc):
           doc.add_root(layout)
       bokeh.io.output_notebook()
       bokeh.io.show(modify_doc)
    else:
        bokeh.io.reset_output()

    return layout

def plot_as_graph(dynamic_graph, communities=None, ts=None, width=800, height=600, slider=False, to_datetime=False,bokeh = False, auto_show=False, **kwargs):
    """
    Plot to see the static graph at each snapshot

    can be row of graphs or an interactive graph with a slider to change snapshot.
    In all cases, the position of nodes is the same in all snapshots.

    The position of nodes is determined using the networkx force directed layout, addition parameters of the function are passed
    to this functions (e.g., iterations=100, k=2...)

    :param dynamic_graph: DynGraphSN
    :param communities: dynamic snapshot_affiliations of the network (can be ignored)
    :param ts: time of snapshot(s) to display. single value or list. default None means all snapshots.
    :param slider: If None, a slider allows to interactively choose the step (work only in jupyter notebooks on a local machine)
    :param to_datetime: one of True/False/function. If True, step IDs are converted to dates using datetime.utcfromtimestamp. If a function, should take a step ID and return a datetime object.
    :param width: width of the figure
    :param height: height of the figure
    :return: bokeh layout containing slider and plot, or only plot if no slider.
    """


    if to_datetime==True:
        to_datetime=datetime.utcfromtimestamp


    # cleaning ts parameter
    if ts == None:
        if isinstance(dynamic_graph, tn.DynGraphIG):
            raise Exception(
                "If using IG graphs/communities, you must specified the desired t to plot")

        ts= list(dynamic_graph.snapshots_timesteps())
        if communities != None:
            ts = ts + list(communities.snapshots.keys())
            ts = sorted(list(set(ts)))

    if not isinstance(ts, list):
        ts = [ts]

    # Obtain snapshots for desired ts (graph and communities)
    if isinstance(dynamic_graph,tn.DynGraphIG):
        temp_graph_sn = tn.DynGraphSN()
        for t in ts:
            temp_graph_sn.add_snapshot(t, dynamic_graph.graph_at_time(t))
        if communities!=None:
            temp_coms_sn = tn.DynCommunitiesSN()
            for t in ts:
                temp_coms_sn.set_communities(t,communities.communities(t))
            communities = temp_coms_sn

        dynamic_graph=temp_graph_sn

    #Obtain CDS for those snapshots
    CDS = _sn_graph2CDS(dynamic_graph, communities, to_datetime, ts=ts)


    unique_pos = _unique_positions(dynamic_graph,ts=ts,**kwargs)

    if bokeh:
        return _plot_as_graph_bokeh(ts,slider,dynamic_graph,CDS,unique_pos,width,height,to_datetime,auto_show)
    else:
        return _plot_as_graph_nx(ts,dynamic_graph,CDS,unique_pos,width,height,to_datetime)











def _plot_longitudinal_pyplot(CDS,nodes,to_datetime,width,height):
    fig, ax = plt.subplots(1,figsize=(width/100,height/100),dpi=100)
    periods = []

    node2y = {n:i for i,n in enumerate(nodes)}
    # Loop over data points; create box from errors at each point
    x_column = "time"

    max_x = 0
    min_x = math.inf
    for i in range(len(CDS.data[x_column])):
        if CDS.data["node"][i] in nodes:
            start_x = CDS.data[x_column][i]
            slot_width = CDS.data["duration"][i]
            if to_datetime:
                start_x=date2num(start_x)
                slot_width = date2num(CDS.data[x_column][i]+slot_width)-start_x
            max_x=max(max_x,start_x+slot_width)
            min_x = min(min_x,start_x)
            rect = Rectangle(( start_x,node2y[CDS.data["node"][i]]), width=slot_width, height=0.9,color=CDS.data["color"][i],edgecolor=None)

            periods.append(rect)
    pc = PatchCollection(periods,match_original=True)

    # Add collection to axes
    ax.add_collection(pc)

    if to_datetime:
        locator = AutoDateLocator(minticks=2)
        formatter = AutoDateFormatter(locator)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)

    ax.set(xlim=(min_x, max_x+(max_x-min_x)/50), ylim=(0, float(len(nodes))))

    if to_datetime:
        plt.xticks(rotation=50)

    if len(nodes)<=30:
        plt.yticks(np.arange(0.5,float(len(nodes))+0.5,1.0), nodes)
    else:
        ax.set_yticklabels([])
    return plt.gcf()


def _plot_longitudinal_bokeh(CDS,nodes,to_datetime,width,height,auto_show):
    tools = ["reset", "wheel_zoom", "box_zoom", "pan", "save"]
    ht = bokeh.models.HoverTool(
        tooltips=[
            ("name", "@node"),
            ("community", "@com"),
            ("start", "@time"),
            ("duration", "@duration_display")
        ])
    #        <style>
    #        .bk-tooltip>div:not(:first-child) {display:none;}
    #    </style>""")
    # ht.point_policy="follow_mouse"

    x_column = "time_shift"

    x_axis_type = "auto"
    if to_datetime != False:
        x_axis_type = "datetime"
        # CDS.data["time_f"] = [to_datetime(x) for x in CDS.data["time_shift"]]
        # x_column = "time_f"
        ht.tooltips = ht.tooltips + [("time", "@time{%F %H:%M}")]
        ht.formatters = {
            'start': 'datetime'
        }

    tools.append(ht)
    longi = bokeh.plotting.figure(plot_width=width, plot_height=height, y_range=nodes, tools=tools,
                                  x_axis_type=x_axis_type, output_backend="webgl")  # ,active_scroll="wheel_zoom"
    longi.output_backend = "svg"

    longi.rect(x=x_column, y="node", width="duration", height=0.9, fill_color="color", hover_color="grey", source=CDS,
               line_color=None, line_width=0)
    ends = [CDS.data["time"][i] + CDS.data["duration"][i] for i in range(len(CDS.data["duration"]))]
    # longi.x_range =Range1d(-1,max(ends))

    longi.xgrid.grid_line_color = None
    longi.ygrid.grid_line_color = None

    if auto_show:
        def modify_doc(doc):
            doc.add_root(longi)

        bokeh.io.output_notebook()
        bokeh.io.show(modify_doc)
    else:
        bokeh.io.reset_output()
    return (longi)

def plot_longitudinal(dynamic_graph=None,communities=None, sn_duration=None,to_datetime=False, nodes=None,width=800,height=600,bokeh=False,auto_show=False):
    """
    A longitudinal view of nodes/snapshot_communities

    Plot snapshot_affiliations such as each node corresponds to a horizontal line and time corresponds to the horizontal axis

    :param dynamic_graph: DynGraphSN or DynGraphIG
    :param communities: dynamic snapshot_affiliations, DynCommunitiesSN or DynCommunitiesIG
    :param sn_duration: the duration of a snapshot, as int or timedelta. If none, default is the network frequency
    :param to_datetime: one of True/False/function. If True, step IDs are converted to dates using datetime.utcfromtimestamp. If a function, should take a step ID and return a datetime object.
    :param nodes: If none, plot all nodes in lexicographic order. If a list of nodes, plot only those nodes, in that order
    :param width: width of the figure
    :param height: height of the figure
    """


    if dynamic_graph==None:
        if isinstance(communities,tn.DynCommunitiesSN):
            dynamic_graph = tn.DynGraphSN()
        else:
            dynamic_graph = tn.DynGraphIG()

    if sn_duration==None and not isinstance(dynamic_graph,tn.DynCommunitiesIG):
        sn_duration = dynamic_graph.frequency()

    if to_datetime==True:
        to_datetime=datetime.utcfromtimestamp
        if sn_duration!=None and not isinstance(sn_duration,timedelta):
            sn_duration=timedelta(seconds=sn_duration)


    if isinstance(dynamic_graph,tn.DynGraphSN):
        if communities == None:
            communities = tn.DynCommunitiesSN()
        t = list(dynamic_graph.snapshots_timesteps())

        if communities != None and isinstance(communities,tn.DynCommunitiesSN):
            t = t + list(communities.snapshots.keys())
            t = sorted(list(set(t)))
        CDS = _sn_graph2CDS(dynamic_graph, communities, to_datetime=to_datetime,ts=t)
    elif isinstance(dynamic_graph,tn.DynGraphIG):
        if communities == None:
            communities = tn.DynCommunitiesIG()
        CDS = _ig_graph2CDS(dynamic_graph, communities, to_datetime=to_datetime)
    elif isinstance(dynamic_graph,tn.DynGraphLS):
        if communities == None:
            communities = tn.DynCommunitiesIG()
        CDS = _ls_graph2CDS(dynamic_graph, communities, to_datetime=to_datetime)

    if isinstance(dynamic_graph,tn.DynGraphSN):# or isinstance(dynamic_graph,tn.DynGraphLS) and sn_duration!=None:
        CDS.data["duration"] = [sn_duration]*len(CDS.data["time"])



    if to_datetime!=False:
        CDS.data["duration_display"] = [x/1000 for x in CDS.data["duration"]]
    else:
        CDS.data["duration_display"]=CDS.data["duration"]

    #CDS.data["duration"] = [v+0.1 for v in CDS.data["duration"]]

    #should work for timedelta and integers
    CDS.data["time_shift"] = [CDS.data["time"][i] + CDS.data["duration"][i] / 2 for i in range(len(CDS.data["duration"]))]

    if nodes==None:
        nodes = sorted(list(set(CDS.data["node"])))

    nodes = [str(x) for x in nodes]


    #return _plot_longitudinal_bokeh(CDS,nodes,to_datetime,width,height,auto_show)
    if bokeh:
        return _plot_longitudinal_bokeh(CDS,nodes,to_datetime,width,height, auto_show)
    else:
        return _plot_longitudinal_pyplot(CDS,nodes,to_datetime,width,height)



# def plot_longitudinal_sn_clusters(dynamic_graph,clusters,level=None, **kwargs):
#     """
#     A longitudinal view of snapshot clusters
#
#     Snapshot clusters are a way to represent periods of the dynamic graphs similar in some way. It is similar to dynamic snapshot_communities,
#     but all nodes of a snapshot belongs always to the same "community".
#
#     Optional parameters (kwargs) are the same as for plot_longitudinal.
#
#     :param dynamic_graph:  DynGraphSN or DynGraphIG
#     :param clusters: clusters as a set of set of partitions ID. Can also be a hierarchical partitioning, represented as a list of clusters. The level to display is in this case decided by the level parameter
#     :param level: if clusters is a hierarchical clustering, the level to display
#     """
#     if level!=None: #single level
#         clusters = clusters[level]
#     coms = tn.DynCommunitiesSN()
#     for i,cl in enumerate(clusters): #cl: a cluster
#         for t in cl:
#             coms.add_community(t, nodes=dynamic_graph.snapshot_affiliations(t).nodes, id=i)
#     if isinstance(dynamic_graph, tn.DynGraphIG):
#         coms = coms.to_DynCommunitiesIG()
#     return plot_longitudinal(dynamic_graph,communities=coms, **kwargs)
#
#
