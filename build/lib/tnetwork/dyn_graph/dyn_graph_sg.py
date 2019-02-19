
import networkx as nx
import math
from tnetwork.dyn_graph.dyn_graph import DynGraph
from tnetwork.utils.intervals import intervals


class DynGraphSG(DynGraph):


    def __init__(self, data=None):

        self._start=math.inf
        self._end=-math.inf
        self._graph = nx.Graph()


    def add_interaction(self, u_of_edge,v_of_edge, time):
        """
        Add an interaction between nodes u and v at time time
        :param u: first node
        :param v: second node
        :param time: pair (start,end)
        :return:
        """

        u = u_of_edge
        v = v_of_edge
        start=time[0]
        end = time[1]
        if not self._graph.has_node(u):
            self.add_node_presence(u_of_edge, start, end)

        if not self._graph.has_node(v):
            self.add_node_presence(v, start, end)

        if not self._graph.has_edge(u,v):
            self._graph.add_edge(u,v,t=intervals())

        self._graph[u][v]["t"].add_interval((start, end))

        self._start = min(self._start, start)
        self._end = max(self._end, end)

    def add_interactions_from(self, nodePairs, times):
        """
        Add interactions between provided pairs for the provided intervals
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
        Add presence for node n between start and end
        :param n: node
        :param time: a period, couple (start, stop)
        """

        start = time[0]
        stop = time[1]
        if not self._graph.has_node(n):
            self._graph.add_node(n,t=intervals())

        self._graph.node[n]["t"].add_interval((start, stop))

    def add_nodes_presence_from(self, nodes,times):
        """
        Add interactions between provided pairs for the provided intervals
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