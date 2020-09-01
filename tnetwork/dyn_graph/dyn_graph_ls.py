
import networkx as nx
import math
from tnetwork.dyn_graph.dyn_graph import DynGraph
from tnetwork.utils.intervals import Intervals
import tnetwork as tn
import sortedcontainers
from tnetwork.dyn_graph.encodings import code_length_LS
from collections.abc import Iterable


class DynGraphLS(DynGraph):
    """
     A class to represent dynamic graphs as link streams.

    It is represented using a networkx Graph, using an attribute ("t") for each node and each edge representing
    its time of presence. The representation is done using a list of integer.

    """


    def __init__(self,edges=None, nodes=None , frequency=1, start=None,end=None):
        """
        Instanciate a dynamic graph

        A start and end dates can be used to give a "duration" to the graph independently from its nodes and edges
        (for instance, to study activity during a whole year, the graph might start on January 1st at 00:00 while
        the first recorded activity occurs in the afternoon or on another day)

        :param start: set a start time, by default will be the first added time
        :param end: set an end time, by default will be the last added time
        :param frequency: minimal time difference between two observations. Default: 1
        :param edges: data to initialize the dynamic graph, dictionary {(n1,n2):[int]}. Keys are edges, time is ordered list of int
        :param nodes: data to initialize the dynamic graph, dictionary {n:time}. Keys are nodes, time is Intervals object (see interval graph)

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
            self._graph.add_weighted_edges_from([(k[0],k[1],sortedcontainers.SortedSet(v)) for k,v in edges.items()],"t")
            #nx.set_edge_attributes(self._graph,edges,"t")
            if start==None or end==None:
                if start == None or end == None:
                    times = set([min(x) for x in edges.values()] + [max(x) for x in edges.values()])
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
            if len(ns)>0:
                return ns
            else:
                return {n:None for n in self._graph.nodes()}

        if isinstance(nodes,str):
            return ns[nodes]

        return {k:v for k,v in ns.items() if k in nodes}

    def add_interaction(self, u,v, time):
        """
        Add an interaction between nodes u and v at time time

        :param u: first node
        :param b: second node
        :param time: integer or list of integers
        :return:
        """

        if isinstance(time,int):
            time=[time]

        if not self._graph.has_edge(u, v):
            self._graph.add_edge(u, v, t=sortedcontainers.SortedSet(time))
        else:
            self._graph[u][v]["t"].update(time)
            # self._graph.add_edge(u,v,t=time)

        start = min(time)
        end=max(time)
        self._start = min(self._start, start)
        self._end = max(self._end, end)

    def cumulated_graph(self,times=None,weighted=True):
        """
        Compute the cumulated graph.

        Return a networkx graph corresponding to the cumulated graph of the given period (whole graph by default)

        :param times: a pair (start,end)
        :return: a networkx (weighted) graph
        """

        if times==None:
            times=(self._start, self._end)

        times_interval = Intervals(times)

        to_return = nx.Graph()
        for n,t in nx.get_node_attributes(self._graph,"t").items():
            intersect = t.intersection(times_interval)
            if weighted:
                to_return.add_node(n,weight=intersect.duration())
            else:
                to_return.add_node(n)

        for (u,v),t in nx.get_edge_attributes(self._graph,"t").items():
            intersect = list(t.irange(times[0], times[1], inclusive=(True, False)))
            if len(intersect)>0:
                if weighted:
                    to_return.add_edge(u,v,weight=len(intersect))
                else:
                    to_return.add_edge(u,v)


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

        for e, times in nx.get_edge_attributes(self._graph, "t").items():
            if t in times:
                to_return.add_edge(e[0],e[1])
        return to_return



    def add_interactions_from(self, nodePairs, times):
        """
        Add interactions between the provided node pairs for the provided times.

        Add each provided nodePair at each provided time

        :param nodePairs: list of pairs of nodes, or a single pair of nodes as a tuple or set
        :param times: list of times as integer or a single integer
        """
        print(nodePairs)
        list_element_example = list(nodePairs)[0]
        if not isinstance(list_element_example, Iterable) or isinstance(list_element_example, str):
            nodePairs = [nodePairs]

        if not isinstance(times, Iterable):
            times = [times]


        for i,nodePair in enumerate(nodePairs):
            npp = list(nodePair)
            self.add_interaction(npp[0], npp[1], times)

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
        :param times: list of times or a single time (integer)
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
        :param time: integer
        :return:
        """

        if self._graph.has_edge(u,v):
            self._graph[u][v]["t"].remove(time)

    def remove_interactions_from(self, nodePairs, times):
        """
        Remove interactions between provided pairs for the provided periods

        :param nodePairs: a node pair, or a list of node pairs
        :param times: a list of integer (applied to all pairs) or a list of lsit of integer (one per nodePairs)
        """
        if not isinstance(nodePairs[0],tuple): #means it is a single pair, not list of pairs
            nodePairs=[nodePairs]*len(times)

        if isinstance(times[0], int): #means it is a single list, not list of list
            times = [times]*len(nodePairs)

        for i, nodePair in enumerate(nodePairs):
            self.remove_interaction(nodePair[0], nodePair[1], times[i])


    def nodes_interactions(self):
        to_return={}
        for e,pres in self.edge_presence().items():
            elist = list(e)
            to_return.setdefault(elist[0],[])
            to_return[elist[0]]+=list(pres)
            to_return.setdefault(elist[1], [])
            to_return[elist[1]] += list(pres)
        for n,pres in to_return.items():
            to_return[n]=sortedcontainers.SortedSet(pres)
        return to_return

    def edge_presence(self, edges=None):
        """
         Return the periods of interactions for each pair of nodes with at least an interaction

         :param edges: the list of edges to get interactions for, all by default
         :return: dictionary, keys : pair of nodes, values : list of integer
         """

        list_element_example = list(edges)[0]
        if not isinstance(list_element_example, Iterable) or isinstance(list_element_example, str):
            edges = [edges]

        to_return = {frozenset(e):pres for e,pres in nx.get_edge_attributes(self._graph,"t").items()}


        if edges!=None:
            edges = [frozenset(e) for e in edges]
            to_return = {e:pres for e,pres in to_return.items() if e in edges}
            if len(edges)==1:
                return list(to_return.values())[0]
        return to_return

        #return self.interactions_intervals(edges)

    def change_times(self) ->[int]:
        """
        List of all times with a node/edge change

        Return the list of all times at which a change node change/link
        :return: list of int
        """
        to_return = set()
        for e,interv in self.edge_presence().items():
            to_return.update(interv)

        for n,interv in self.node_presence().items():
            if interv!=None:
                for period in interv.periods():
                    to_return.update(period)

        return sorted(list(to_return))



    def slice(self,start,end):
        """
        Keep only the selected period

        :param start: time of the beginning of the slice (inclusive)
        :param end: time of the end of the slice (exclusive)
        """


        to_return = tn.DynGraphLS()
        slice_time = Intervals((start,end))
        for n,presence in self.node_presence().items():
            duration = slice_time.intersection(presence)
            if duration.duration()>0:
                to_return.add_node_presence(n,duration)

        for e,presence in self.interactions_intervals().items():
            to_return.add_interaction(e[0],e[1],presence.islice(start,end))
            to_return.add_interaction(e[0],e[1],slice_time.intersection(presence))

        return to_return

    def to_DynGraphSN(self,slices=None,weighted=True):
        """
        Convert to a snapshot representation.

        :param slices: can be one of

        - None, snapshot_affiliations are created according to the frequency of the dynamic network (default one),
        - an integer, snapshot_affiliations are created using a sliding window
        - a list of periods, represented as pairs (start, end), each period yielding a snapshot

        :return: a dynamic graph represented as snapshot_affiliations, the weight of nodes/edges correspond to their presence time during the snapshot

        """
        dgSN = tn.DynGraphSN()
        if slices==None:
            slices=self.frequency()

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
                slices.append((start,end))

        all_times = sortedcontainers.SortedList(self.change_times())
        for ts in slices:
            #print(ts)
            if len(list(all_times.irange(ts[0],ts[1],inclusive=(True,False))))>0:
                dgSN.add_snapshot(t=ts[0], graphSN=self.cumulated_graph(ts, weighted=weighted))

                #dgSN.add_snapshot(t=ts[0],graphSN=nx.Graph())

        #sorted_times = [x[0] for x in slices]
        #print(self.node_presence())
        #to_add = {}


        # for n,interv in self.node_presence().items():
        #     intersection = interv._discretize(sorted_times)
        #     for t, duration in intersection.items():
        #         to_add.setdefault(t, []).append((n, {"weight": duration}))
        # for t in to_add:
        #     dgSN.snapshots(t).add_nodes_from(to_add[t])
        #
        # to_add = {}
        # for e,interv in self.interactions_intervals().items():
        #     intersection = interv._discretize(sorted_times)
        #     for t,duration in intersection.items():
        #         to_add.setdefault(t,[]).append((e[0],e[1],{"weight":duration}))
        # for t in to_add:
        #     dgSN.snapshots(t).add_edges_from(to_add[t])

        return dgSN

    def code_length(self):
        return code_length_LS(self)

    # def code_length(self):
    #
    #
    #     code_time = np.log2(len(self.change_times())+1)
    #
    #
    #
    #     #g_cumulated = self.cumulated_graph()
    #     node_encoding = np.log2(len(self._graph.nodes()))
    #     edge_encoding = node_encoding * 2
    #     nb_time = len(self.change_times())
    #
    #     nb_unique_edges = len(self._graph.edges())
    #     nb_periods = 0
    #     for e,ts in self.interactions_intervals().items():
    #         nb_periods+=len(ts.periods())
    #     time_encoding = np.log2(nb_time)
    #     #time_encoding = np.log2(nb_periods*2)
    #
    #     #(N1,N2)_(T1,T2)_(T3,T4)_STOP_(N2,N3)
    #
    #     total_code = edge_encoding*nb_unique_edges + 2*nb_periods*time_encoding + nb_unique_edges*time_encoding
    #     print("ig: ",edge_encoding,time_encoding,nb_unique_edges,nb_periods)
    #
    #     return total_code

    def write_interactions(self,filename):
        """

        :param filename:
        :return:
        """
        tn.write_as_LS(self, filename)

    def aggregate_sliding_window(self, bin_size=None, shift=None, t_start=None, t_end=None,weighted=True):
        """
        Return a new dynamic graph without modifying the original one, aggregated using sliding windows of the desired size. If Shift is not provided or equal to bin_size, windows are non overlapping.
        If no parameter is provided, creates a single graph aggregating the whole period.
        Yielded graphs are weighted (weight: number of apparition of edges during the period)

        :param bin_size: desired size of bins, in the internal time unit (not necessarily equals to the number of snapshot_affiliations)
        :param shift: time distance (shift) between the start of two successive bins, in the internal time unit (not necessarily number of sn)
        :param t_start: time step to start the binning (default: first)
        :param t_end: time step (not included) to stop the binning (default: last)
        :return: a DynGraph_SN object
        """



        if t_start==None:
            t_start = self.start()
        if t_end==None:
            t_end=self.end()

        if bin_size == None:
            bin_size=t_end-t_start

        if shift==None:
            shift=bin_size


        bins = []
        for t in range(t_start, t_end, shift):
            bins.append((t, t + bin_size))

        return self.to_DynGraphSN(bins,weighted=weighted)