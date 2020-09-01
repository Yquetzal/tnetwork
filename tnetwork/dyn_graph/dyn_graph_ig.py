
import networkx as nx
import math
from tnetwork.dyn_graph.dyn_graph import DynGraph
from tnetwork.utils.intervals import Intervals
import tnetwork as tn
import numpy as np
from collections.abc import Iterable

class DynGraphIG(DynGraph):
    """
     A class to represent dynamic graphs as interval graphs.

    It is represented using a networkx Graph, using an attribute ("t") for each node and each edge representing
    its periods of presence. The representation is done using the class Intervals (tnetwork.utils.intervals)
    Time steps are represented by integers, that can correspond to an arbitrary scale (1,2,3,...) or to timestamps in
    order to represent dates.

    """


    def __init__(self,edges=None, nodes=None,  start=None,end=None,frequency=1):
        """
        Instanciate a dynamic graph

        A start end end dates can be used to give a "duration" to the graph independently from its nodes and edges
        (for instance, to study activity during a whole year, the graph might start on January 1st at 00:00 while
        the first recorded activity occurs in the afternoon or on another day)

        :param start: set a start time, by default will be the first time of the added affiliations
        :param end: set an end time, by default will be the last time of the added affiliations
        :param edges: data to initialize the dynamic graph, dictionary {(n1,n2):time}. Keys are edges, time is Intervals object
        :param nodes: data to initialize the dynamic graph, dictionary {n:time}. Keys are ndoes, time is Intervals object

        """
        self._start=start
        self._end=end
        self.frequency(frequency)
        if start==None:
            self._start=math.inf
        if end==None:
            self._end=-math.inf

        self._graph = nx.Graph()
        if nodes!=None:
            self._graph.add_nodes_from(nodes.keys())
            nx.set_node_attributes(self._graph,nodes,"t")
            if start == None or end == None:
                times = set([x.start() for x in nodes.values()] + [x.end() for x in nodes.values()])
                if start == None:
                    self._start = min(times)
                    start = min(times)
                if end == None:
                    self._end = max(times)
                    end = max(times)

        if edges!=None:
            self._graph.add_weighted_edges_from([(k[0],k[1],v) for k,v in edges.items()],"t")
            #nx.set_edge_attributes(self._graph,edges,"t")
            if start==None or end==None:
                if start == None or end == None:
                    times = set([x.start() for x in edges.values()] + [x.end() for x in edges.values()])
                    if start == None:
                        self._start = min(times)
                    if end == None:
                        self._end = max(times)


    def start(self):
        return self._start

    def end(self):
        return self._end

    def node_presence(self, nodes=None):
        """
        Presence period of nodes

        Several usages:

        * If nodes==None (default), return a dict for each node, its existing times
        * If nodes is a single node, return the interval of presence of this node
        * If nodes is a set of nodes, return interval of presence of those nodes as a dictionary

        :param nodes:
        :return: dictionary, for each node, its presence Intervals, or single Interval for single node
        """
        toReturn = {}

        ns = nx.get_node_attributes(self._graph,"t")
        if nodes==None:
            return ns

        if isinstance(nodes,str):
            return ns[nodes]

        return {k:v for k,v in ns.items() if k in nodes}

    def add_interaction(self, u,v, time):
        """
        Add an interaction between nodes u and v at time time

        :param u: first node
        :param b: second node
        :param time: pair (start,end) or Intervals
        :return:
        """
        if not isinstance(time,Intervals):
            time= Intervals(time)

        self.add_node_presence(u, time)
        self.add_node_presence(v, time)

        self._add_interaction_safe(u,v, time)

        start = time.start()
        end=time.end()
        self._start = min(self._start, start)
        self._end = max(self._end, end)

    def cumulated_graph(self,times=None):
        """
        Compute the cumulated graph.

        Return a networkx graph corresponding to the cumulated graph of the given period (whole graph by default)

        :param times: Intervals object or list of pairs (start, end)
        :return: a networkx (weighted) graph
        """

        if times==None:
            times=Intervals([(self._start, self._end)])
        elif not isinstance(times,Intervals):
            times = Intervals(times)

        to_return = nx.Graph()
        for n,t in nx.get_node_attributes(self._graph,"t").items():
            intersect = t.intersection(times)
            to_return.add_node(n,weight=intersect.duration())

        for (u,v),t in nx.get_edge_attributes(self._graph,"t").items():
            intersect = t.intersection(times)
            to_return.add_edge(u,v,weight=intersect.duration())

        return to_return

    def graph_at_time(self,t:int) -> nx.Graph:
        """
        Graph as it is at time t

        Return a networkx graph corresponding to the graphs as it is at time t, i.e., edges and nodes present at that time

        :param t: timestep
        :return: a networkx Graph
        """
        to_return = nx.Graph()
        for n,intv in nx.get_node_attributes(self._graph,"t").items():
            if intv.contains_t(t):
                to_return.add_node(n)

        for e, intv in nx.get_edge_attributes(self._graph, "t").items():
            if intv.contains_t(t):
                to_return.add_edge(e[0],e[1])
        return to_return

    def _add_interaction_safe(self, u,v, time):
        """
        Same as add_interaction but do not modify nodes presences to save time. To use only if nodes
        have been added manually first

        :param u:
        :param v:
        :param time: pair or directly an Intervals object
        :return:
        """

        if not self._graph.has_edge(u,v):
            self._graph.add_edge(u, v, t=Intervals())

        if isinstance(time,Intervals):
            self._graph[u][v]["t"]+=time
            #self._graph.add_edge(u,v,t=time)
        else:
            start = time[0]
            end = time[1]
            self._graph[u][v]["t"].add_interval((start, end))


    def add_interactions_from(self, nodePairs, times):
        """
       Add interactions between provided pairs for the provided periods

        Add each provided nodePair at each provided time

        :param nodePairs: list of pairs of nodes, or a single pair of nodes as a tuple or set
        :param times: a single time or a list of times, as pair (start,end) or an Interval Object
        """

        list_element_example = list(nodePairs)[0]
        if not isinstance(list_element_example, Iterable) or isinstance(list_element_example, str):
            nodePairs = [nodePairs]


        if not isinstance(times,Iterable): #Single Interval object
            times = [times]
        else: #single interaval as a pair or multiple things
            list_element_example = list(times)[0]
            if not isinstance(list_element_example, Iterable): #if an element of a list is an int, it's a single pair
                times = [times]


        for i,nodePair in enumerate(nodePairs):
            np = list(nodePair)
            self.add_interaction(np[0], np[1], times)

    def add_node_presence(self, n, time):
        """
        Add presence for a node for a period

        :param n: node
        :param time: a period, couple (start, stop) or an interval
        """
        if not isinstance(time,Intervals):
            time= Intervals(time)


        if not self._graph.has_node(n):
            self._graph.add_node(n, t=time)
        else:
            self._graph.nodes[n]["t"]+=time

        self._start = min(self._start, time.start())
        self._end = max(self._end, time.end())

    def add_nodes_presence_from(self, nodes,times):
        """
        Add interactions between provided pairs for the provided periods

        :param nodes: list of nodes, or a single node
        :param times: list of times defined as couple (start, stop) , of same length as node, or a single time
        """
        if not isinstance(nodes,Iterable):
            nodes = [nodes]


        if not isinstance(times,Iterable): #Single Interval object
            times = [times]
        else: #single interaval as a pair or multiple things
            list_element_example = list(times)[0]
            if not isinstance(list_element_example, Iterable): #if an element of a list is an int, it's a single pair
                times = [times]


        for i,node in enumerate(nodes):
            self.add_node_presence(node, times)

    def remove_node_presence(self,node,time):
        """
        Remove node and its interactions over the period

        :param node: node to remove
        :param time: a period, couple (start, stop) or an interval
        """
        if not isinstance(time,Intervals):
            time= Intervals(time)


        if self._graph.has_node(node):
            self._graph.nodes()[node]["t"]= self._graph.nodes()[node]["t"]-time
            if self._graph.nodes()[node]["t"].duration()==0:
                self._graph.remove_node(node)

            if self._start in time or self._end in time or time.end()==self._end:
                new_max = -math.inf
                new_min = math.inf
                for k,v in self.node_presence().items():
                    new_max = max(new_max,v.end())
                    new_min = min(new_min,v.start())

                self._start = new_min
                self._end = new_max

    def remove_interaction(self,u,v,time):
        """
        Remove an interaction between nodes u and v at time time

        :param u: first node
        :param v: second node
        :param time: pair (start,end)
        :return:
        """

        if self._graph.has_edge(u,v):
            self._graph[u][v]["t"]=self._graph[u][v]["t"]-time

    def remove_interactions_from(self, nodePairs, times):
        """
        Remove interactions between provided pairs for the provided periods

        :param nodePairs: a list of node pairs
        :param times: a pair of time step of the form (start,stop), or a list of pair of time step of same length as nodePairs
        """

        #if not isinstance(nodePairs[0],tuple): #means it is a single pair, not list of pairs
        #    nodePairs=[nodePairs]*len(times)

        if not isinstance(times[0], tuple):
            times = [times]*len(nodePairs)

        for i, nodePair in enumerate(nodePairs):
            self.remove_interaction(nodePair[0], nodePair[1], times[i])


    def interactions_intervals(self, edges=None):
        """
        Return the periods of interactions for each pair of nodes with at least an interaction

        :param edges: the list of edges to get interactions for, all by default
        :return: dictionary, keys : pair of nodes, values : an interval object
        """


        es = nx.get_edge_attributes(self._graph,"t")
        es = {frozenset(k):v for k,v in es.items()}
        if edges==None:
            return es
        else:
            list_element_example = list(edges)[0]
            if not isinstance(list_element_example, Iterable) or isinstance(list_element_example, str):
                edges = [edges]

        edges = [frozenset(e) for e in edges]
        edges = {k:v for k,v in es.items() if k in edges}
        if len(edges)==1:
            return list(edges.values())[0]
        return edges

    def edge_presence(self, edges=None,as_intervals=False):
        """
         Return the periods of interactions for each pair of nodes with at least an interaction

         :param edges: the list of edges to get interactions for, all by default
         :return: dictionary, keys : pair of nodes, values : an interval object
         """
        if as_intervals:
            return self.interactions_intervals(edges)

        to_return = self.interactions_intervals(edges)
        if isinstance(to_return,Intervals):
            return to_return.periods()

        return {n:pres.periods() for n,pres in to_return.items()}

        #return self.interactions_intervals(edges)

    def change_times(self) ->[int]:
        """
        List of all times with a node/edge change

        Return the list of all times at which a change (new edge, end of edge, node appear/disappear) occurs
        :return: list of int
        """
        to_return = set()
        for e,interv in self.interactions_intervals().items():
            for period in interv.periods():
                to_return.update(period)

        for n,interv in self.node_presence().items():
            for period in interv.periods():
                to_return.update(period)

        return sorted(list(to_return))



    def slice(self,start,end):
        """
        Keep only the selected period

        :param start: time of the beginning of the slice
        :param end: time of the end of the slice
        """


        to_return = tn.DynGraphIG()
        slice_time = Intervals((start,end))
        for n,presence in self.node_presence().items():
            duration = slice_time.intersection(presence)
            if duration.duration()>0:
                to_return.add_node_presence(n,duration)

        for e,presence in self.interactions_intervals().items():
            el = list(e)
            duration = slice_time.intersection(presence)
            if duration.duration()>0:
                to_return.add_interaction(el[0],el[1],duration)

        return to_return

    def to_DynGraphSN(self,slices=None,discard_empty=True):
        """
        Convert to a snapshot representation.

        :param slices: can be one of

        - None, snapshot_affiliations are created such as a new snapshot is created at every node/edge change,
        - an integer, snapshot_affiliations are created using a sliding window
        - a list of periods, represented as pairs (start, end), each period yielding a snapshot
        :param discard_empty: if True, the returned dynamic network won't have empty snapshots

        :return: a dynamic graph represented as snapshot_affiliations, the weight of nodes/edges correspond to their presence time during the snapshot

        """
        dgSN = tn.DynGraphSN()
        if slices==None:
            freq = self.frequency()
            slices = freq
            #times = self.change_times()

        if isinstance(slices,int):
            duration = slices
            dgSN.frequency(slices)

            slices = []
            start = self._start
            end = start+duration
            slices.append((start, end))
            while(end<=self._end):
                start=end
                end = start+duration
                slices.append((start, end))

        for ts in slices:
            dgSN.add_snapshot(t=ts[0],graphSN=nx.Graph())

        sorted_times = [x[0] for x in slices]
        to_add = {}

        for n,interv in self.node_presence().items():
            intersection = interv._discretize(sorted_times)
            for t, duration in intersection.items():
                to_add.setdefault(t, []).append((n, {"weight": duration}))
        for t in to_add:
            dgSN.snapshots(t).add_nodes_from(to_add[t])

        to_add = {}
        for e,interv in self.interactions_intervals().items():
            elist=list(e)
            intersection = interv._discretize(sorted_times)
            for t,duration in intersection.items():
                to_add.setdefault(t,[]).append((elist[0],elist[1],{"weight":duration}))
        for t in to_add:
            dgSN.snapshots(t).add_edges_from(to_add[t])

        if discard_empty:
            dgSN.discard_empty_snapshots()

        return dgSN


    # def to_DynGraphSN(self,slices=None):
    #     """
    #     Convert to a snapshot representation.
    #
    #     :param slices: can be one of
    #
    #     - None, snapshot_affiliations are created such as a new snapshot is created at every node/edge change,
    #     - an integer, snapshot_affiliations are created using a sliding window
    #     - a list of periods, represented as pairs (start, end), each period yielding a snapshot
    #
    #     :return: a dynamic graph represented as snapshot_affiliations, the weight of nodes/edges correspond to their presence time during the snapshot
    #
    #     """
    #     dgSN = tn.DynGraphSN()
    #     if slices==None:
    #         times = self.change_times()
    #         slices = [(times[i],times[i+1]) for i in range(len(times)-1)]
    #
    #     if isinstance(slices,int):
    #         duration = slices
    #         slices = []
    #         start = self.start
    #         end = start+duration
    #         while(end<=self.end):
    #             end = start+duration
    #             slices.append((start,end))
    #             start=end
    #             end = end+duration
    #
    #     for ts in slices:
    #         dgSN.add_snapshot(t=ts[0],graphSN=nx.Graph())
    #
    #     #print(self.node_presence())
    #     for n,interv in self.node_presence().items():
    #         for ts in slices:
    #             presence = interv.intersection(Intervals([ts])).duration()
    #             if presence>0:
    #                 dgSN.snapshots(ts[0]).add_node(n,weight=presence)
    #
    #     for e,interv in self.interactions().items():
    #         for ts in slices:
    #             presence = interv.intersection(Intervals([ts])).duration()
    #             if presence>0:
    #                 dgSN.snapshots(ts[0]).add_edge(e[0],e[1],weight=presence)
    #
    #     return dgSN

    def code_length(self):

        total_code = 0
        #nb_nodes = len(self._graph.nodes())
        #nb_different_edges = len(self._graph.edges())
        #code_one_node = np.log2(nb_nodes)
        code_time = np.log2(len(self.change_times())+1)

        #total_code+=code_one_node*2*nb_different_edges



        #g_cumulated = self.cumulated_graph()
        node_encoding = np.log2(len(self._graph.nodes()))
        edge_encoding = node_encoding * 2
        nb_time = len(self.change_times())

        nb_unique_edges = len(self._graph.edges())
        nb_periods = 0
        for e,ts in self.interactions_intervals().items():
            nb_periods+=len(ts.periods())
        time_encoding = np.log2(nb_time)
        #time_encoding = np.log2(nb_periods*2)

        #(N1,N2)_(T1,T2)_(T3,T4)_STOP_(N2,N3)

        total_code = edge_encoding*nb_unique_edges + 2*nb_periods*time_encoding + nb_unique_edges*time_encoding
        print("ig: ",edge_encoding,time_encoding,nb_unique_edges,nb_periods)

        return total_code

    def write_interactions(self,filename):
        """
        Write a file with interactions

        Write interactions in the corresponding json format

        :param filename:
        :return:
        """
        tn.write_as_IG(self,filename)