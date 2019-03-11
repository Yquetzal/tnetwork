
import networkx as nx
import math
from tnetwork.dyn_graph.dyn_graph import DynGraph
from tnetwork.utils.intervals import Intervals
import tnetwork as tn


class DynGraphIG(DynGraph):
    """
     A class to represent dynamic graphs as interval graphs.

    It is represented using a networkx Graph, using an attribute ("t") for each node and each edge representing
    its periods of presence. The representation is done using the class Intervals (tnetwork.utils.intervals)
    Time steps are represented by integers, that can correspond to an arbitrary scale (1,2,3,...) or to timestamps in
    order to represent dates.

    """


    def __init__(self, start=None,end=None):
        """
        Instanciate a dynamic graph

        A start end end dates can be used to give a "duration" to the graph independently from its nodes and edges
        (for instance, to study activity during a whole year, the graph might start on January 1st at 00:00 while
        the first recorded activity occurs in the afternoon or on another day)

        :param start: set a start time, by default will be the first time of the added affiliations
        :param end: set an end time, by default will be the last time of the added affiliations
        """
        if start==None:
            self.start=math.inf
        if end==None:
            self.end=-math.inf

        self._graph = nx.Graph()

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
            self._graph.add_edge(u,v,t=time)
        else:
            start = time[0]
            end = time[1]
            self._graph[u][v]["t"].add_interval((start, end))



    def add_interaction(self, u_of_edge,v_of_edge, time):
        """
        Add an interaction between nodes u and v at time time

        :param u_of_edge: first node
        :param v_of_edge: second node
        :param time: pair (start,end)
        :return:
        """

        u = u_of_edge
        v = v_of_edge


        self.add_node_presence(u, time)
        self.add_node_presence(v, time)

        self._add_interaction_safe(u,v, time)

        start = time[0]
        end=time[1]
        self.start = min(self.start, start)
        self.end = max(self.end, end)

    def add_interactions_from(self, nodePairs, times):
        """
        Add interactions between provided pairs for the provided periods

        :param nodePairs: a node pair, or a list of node pairs
        :param times: a pair of time step of the form (start,stop), or a list of pair of time step of same length as nodePairs
        """
        if not isinstance(nodePairs[0],tuple): #means it is a single pair, not list of pairs
            nodePairs=[nodePairs]*len(times)

        if not isinstance(times[0], tuple): #means it is a single pair, not list of pairs
            times = [times]*len(nodePairs)


        for i,nodePair in enumerate(nodePairs):
            self.add_interaction(nodePair[0], nodePair[1], times[i])

    def add_node_presence(self, n, time):
        """
        Add presence for a node for a period

        :param n: node
        :param time: a period, couple (start, stop)
        """


        if not self._graph.has_node(n):
            self._graph.add_node(n, t=Intervals())

        if isinstance(time,Intervals):
            self._graph.node[n]["t"]=time
        else:
            start = time[0]
            stop = time[1]
            self._graph.node[n]["t"].add_interval((start, stop))

    def add_nodes_presence_from(self, nodes,times):
        """
        Add interactions between provided pairs for the provided periods

        :param nodes: list of nodes, or a single node
        :param times: list of times defined as couple (start, stop) , of same length as node, or a single time
        """
        if not isinstance(nodes,list):
            nodes = list(nodes)
            if len(nodes)==1:
                nodes=nodes*len(times)

        if not isinstance(times[0], tuple): #means it is a single pair, not list of pairs
            times = [times]*len(nodes)


        for i,node in enumerate(nodes):
            self.add_node_presence(node, times[i])

    def node_presence(self, nodes=None):
        """
        return the presence period of each node, as a dictionary

        :param nodes:
        :return: dictionary, for each node, its existing times
        """
        toReturn = {}

        ns = nx.get_node_attributes(self._graph,"t")
        if nodes==None:
            return ns

        return {k:v for k,v in ns.items() if k in nodes}

    def interactions(self,edges=None):
        """
        Return the periods of interactions for each pair of nodes with at least an interaction

        :param edges: the list of edges to get interactions for, all by default
        :return: dictionary, keys : pair of nodes, values : an interval object
        """
        es = nx.get_edge_attributes(self._graph,"t")
        if edges==None:
            return es

        return {k:v for k,v in es.items() if k in edges}

    def change_times(self) ->[int]:
        """
        List of all times with a node/edge change

        Return the list of all times at which a change (new edge, end of edge, node appear/disappear) occurs
        :return: list of int
        """
        to_return = set()
        for e,interv in self.interactions().items():
            for period in interv.periods():
                to_return.update(period)

        for n,interv in self.node_presence().items():
            for period in interv.periods():
                to_return.update(period)

        return sorted(list(to_return))



    def to_DynGraphSN(self,slices=None):
        """
        Convert to a snapshot representation.

        :param slices: can be one of

        - None, affiliations are created such as a new snapshot is created at every node/edge change,
        - an integer, affiliations are created using a sliding window
        - a list of periods, represented as pairs (start, end), each period yieling a snapshot

        :return: a dynamic graph represented as affiliations, the weight of nodes/edges correspond to their presence time during the snapshot

        """
        dgSN = tn.DynGraphSN()
        if slices==None:
            times = self.change_times()
            slices = [(times[i],times[i+1]) for i in range(len(times)-1)]

        if isinstance(slices,int):
            duration = slices
            slices = []
            start = self.start
            end = start+duration
            while(end<self.end):
                end = start+duration
                slices.append((start,end))
                start=end
                end = end+duration

        for ts in slices:
            dgSN.add_snapshot(t=ts[0],graphSN=nx.Graph())

        for n,interv in self.node_presence().items():
            for ts in slices:
                presence = interv.intersection(Intervals([ts])).duration()
                if presence>0:
                    dgSN.snapshots(ts[0]).add_node(n,weight=presence)

        for e,interv in self.interactions().items():
            for ts in slices:
                presence = interv.intersection(Intervals([ts])).duration()
                if presence>0:
                    dgSN.snapshots(ts[0]).add_edge(e[0],e[1],weight=presence)

        return dgSN