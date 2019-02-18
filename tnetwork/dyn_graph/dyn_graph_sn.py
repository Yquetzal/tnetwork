from sortedcontainers import *
from collections import Iterable

import networkx as nx
from copy import deepcopy
from .dyn_graph_sg import DynGraphSG
from tnetwork.utils.bidict import bidict
import pkg_resources

import tnetwork as dx
from tnetwork.dyn_graph.dyn_graph import DynGraph


class DynGraphSN(DynGraph):


    def __init__(self, data=None):
        """
        Instanciate a dynamic graph represented as sequence of snapshots.
        each snapshot is represented by a networkx graph, and is associated to a time step identifier.
        Snpashots are ordered according to their time step identifier, so it is better to use numbers, for instance index, dates or timestamps.
        :param data: can be a dictionary {time step:graph} or a list of graph, in which sase time steps are integers starting at 0
        """

        self._snapshots = SortedDict()
        if data!=None:
            if isinstance(data,dict):
                self._snapshots = SortedDict(data)
            elif isinstance(data,list):
                self._snapshots = SortedDict({i:g for i,g in enumerate(data)})
            else:
                raise Exception("data should be a list or a dictionary")




    @staticmethod
    def graph_socioPatterns2012():
        """
        Function that return the graph of interactions between students in 2012, from the SocioPatterns project.
        >>> dg = DynGraphSN.graph_socioPatterns2012()

        :return:
        """

        resource_package = __name__
        resource_path = '/'.join(('toy_data', 'thiers_2012.csv'))
        fileLocation = pkg_resources.resource_filename(resource_package, resource_path)


        dg = dx.read_graph_link_stream(fileLocation)
        return dg




    def add_interaction(self,u_of_edge,v_of_edge,time):
        """
        add a single interaction at a single time step
        :param u_of_edge: first node
        :param v_of_edge: second node
        :param time: time step identifier
        """

        self.add_interactions_from([(u_of_edge,v_of_edge)],[time])

    def add_interactions_from(self, nodePairs, times):
        """
        Add interactions between the provided node pairs for the provided times. If of the two parameters is a single element,
        will add the node pair at all provided time steps, or all the node pairs at the provided time step.
        :param nodePairs: list of pairs of nodes, or a single pair of nodes
        :param times: list of times for this node, or a single time
        :return:
        """
        #note: could be optimized

        if len(nodePairs)==2 and not isinstance(nodePairs[0],Iterable):
            nodePairs = [nodePairs]*len(times)

        if not isinstance(times,Iterable):
            times = [times]*len(nodePairs)

        for i,nodePair in enumerate(nodePairs):
            t = times[i]
            if not t in self._snapshots:
                self.add_snaphsot(t)
            self.apply_nx_function(nx.Graph.add_edge,start=t,stop=t,u_of_edge=nodePair[0],v_of_edge=nodePair[1])



    def remove_interaction(self,u_of_edge,v_of_edge,time):
        """
        remove a single interaction at a single time step. Note: it does not remove the node
        :param u_of_edge: first node
        :param v_of_edge: second node
        :param time: time step identifier
        """

        self.remove_interactions_from([(u_of_edge,v_of_edge)],[time])

    def remove_interactions_from(self, nodePairs, times):
        """
        Remove interactions between the provided node pairs for the provided times. If of the two parameters is a single element,
        will remove the node pair at all provided time steps, or all the node pairs at the provided time step.
        :param nodePairs: list of pairs of nodes, or a single pair of nodes
        :param times: list of times for this node, or a single time
        :return:
        """
        #note: could be optimized

        if len(nodePairs)==2 and not isinstance(nodePairs[0],Iterable):
            nodePairs = [nodePairs]*len(times)

        if not isinstance(times,Iterable):
            times = [times]*len(nodePairs)

        for i,nodePair in enumerate(nodePairs):
            t = times[i]

            self.apply_nx_function(nx.Graph.remove_edge,start=t,stop=t,u=nodePair[0],v=nodePair[1])

    def graph_at_time(self,t):
        """
        return the graph as it is at time t
        :param t: a time step identifier
        :return: the graph as a networkx graph
        """
        return self.snapshots(t)


    def add_snaphsot(self, t, graphSN=None):
        """
        Add a snapshot for a time step t
        :param t: the time step identifier
        :param graphSN: the graph to add (networkx object
        """

        if graphSN==None:
            graphSN=nx.Graph()
        self._snapshots[t]=graphSN




    def snapshots_timesteps(self):
        """
        return the list of time steps
        :return: list of time steps
        """
        return list(self._snapshots.keys())


    def apply_nx_function(self,function,start=None,stop=None,**kwargs):
        """
        Apply a networkx function to each snapshot and return the list of result. Parameters of the function to apply can be passed as parameter to this function.
        example
        >>> dg = DynGraphSN.graph_socioPatterns2012()
        >>> dg.apply_nx_function(nx.nodes)
        >>> dg.apply_nx_function(nx.Graph.add_node,node_for_adding="nodeTest")
        :param function: the networkx function
        :return: the list of results for each snapshot
        """

        if start==None:
            start = self.snapshots_timesteps()[0]
        if stop==None:
            stop = self.snapshots_timesteps()[-1]
        to_return = []
        keys = self.snapshots().irange(start, stop, inclusive=(True, True))
        for t in keys:
            theG = self._snapshots[t]
            try:
                answer = function(theG, **kwargs)
            except Exception as e:
                print(str(e))
                answer = Exception
            to_return.append(answer)

        return to_return


    def remove_node(self, u, t=None): #if only a node is given, removed from all instances
        """
        Remove a node from the provided in
        :param u: a node
        :param t: a time step, a set of time step, or None for all time step
        :return:
        """
        if t==None:
            t=self._snapshots.keys()
        else:
            if isinstance(t, str) or not isinstance(t, Iterable):
                t=[t]
        for aT in t:
            if u in self._snapshots[aT]:
                self._snapshots[aT].remove_node(u)

    def remove_nodes_from(self, nbunch): #is list of (node,t), remove specifically. If list(node), remove all occurences
        """

        :param nbunch:
        :return:
        """
        for nOcc in nbunch:
            if isinstance(nOcc,tuple):
                (u, t)=nOcc
            else:
                u=nOcc
                t= None
            self.remove_node(u,t)

    def to_DynGraphSG(self, convert_time_to_integer=False, last_SN_duration=1):
        """
        Convert the graph into a DynGraph_SG, i.e. a representation as a Stream graph (edges have durations).

        Be careful, for the last snaphsot, we cannot know his duration, therefore, if last_SN_duration is not provided, it has a default duration of 1.
        :param convert_time_to_integer: if True, use the snapshot order in the list of SN rather than its time step
        :param last_SN_duration: duration of the last SN
        :return:
        """
        toReturn = DynGraphSG()



        for i in range(len(self._snapshots)):
            if convert_time_to_integer:
                t=i
                tNext=i+1
            else:
                t = self._snapshots.peekitem(i)[0]
                if i<len(self._snapshots)-1:
                    tNext=self._snapshots.peekitem(i + 1)[0]
                else:
                    #tNext = self._snapshots.peekitem("END")[1]
                    if type(t) is str:
                        tNext="END"
                    else:
                        tNext = t+last_SN_duration ####### BE CAREFUL we could choose inf or.....

            if (len(self._snapshots.peekitem(i)[1].nodes()))>0:
                toReturn.add_nodes_presence_from(self._snapshots.peekitem(i)[1].nodes(), (t, tNext))

                if len(list(self._snapshots.peekitem(i)[1].edges()))>0:
                    toReturn.add_interactions_from(list(self._snapshots.peekitem(i)[1].edges()), (t, tNext) )


        return toReturn

    def _combine_weighted_graphs(self,graphList, weight=1.0):
        """
        function to aggregate several graphs into a weighted graph
        :param graphList: enumerable of graphs
        :param weight: default weight
        :return:
        """
        newG = nx.Graph()
        for g in graphList:
            weights = nx.get_edge_attributes(g, "weight")
            # add weight of one to unweighted graphs
            if len(weights) == 0:
                weights = {(u, v): 1 for (u, v) in g.edges()}

            for (u, v), w in weights.items():
                if newG.has_edge(u, v):
                    newG[u][v]["weight"] += w
                else:
                    newG.add_edge(u, v, weight=w)
        return newG


    def cumulated_graph(self):
        """
        Compute the cumulated graph. Return a networkx graph
        :return: a networkx (weighted) graph
        """
        return self.aggregate_sliding_window().snapshots().peekitem(0)[1]


    def aggregate_sliding_window(self, bin_size=None, shift=None, t_start=None, t_end=None):
        """
        Return a new dynamic graph without modifying the original one, aggregated using sliding windows of the desired size. If Shift is not provided or equal to bin_size, windows are non overlapping.
        If no parameter is provided, creates a single graph aggregating the whole period.
        Yielded graphs are weighted (weight: number of apparition of edges during the period)
        :param bin_size: desired size of bins, in the internal time unit (not necessarily equals to the number of snapshots)
        :param shift: time distance (shift) between the start of two successive bins, in the internal time unit (not necessarily number of sn)
        :param t_start: time step to start the binning (default: first)
        :param t_end: time step (not included) to stop the binning (default: last)
        :return: a DynGraph_SN object
        """



        if t_start==None:
            t_start = self.snapshots_timesteps()[0]
        if t_end==None:
            t_end=self.snapshots_timesteps()[-1]

        if bin_size == None:
            bin_size=t_end-t_start

        if shift==None:
            shift=bin_size


        bins = []
        for t in range(t_start, t_end, shift):
            bins.append((t, t + bin_size))

        toReturn = DynGraphSN()
        for (binStart,binEnd) in bins:
            #print("aggregating",binStart,binEnd)
            keys = self.snapshots().irange(binStart, binEnd, inclusive=(True, False))
            keys = list(keys)
            if len(keys)>0:
                toReturn.add_snaphsot(binStart, self._combine_weighted_graphs([self._snapshots[k] for k in keys]))
            else:
                toReturn.add_snaphsot(binStart)
        return toReturn


    def snapshots(self, t=None):
        """
        Return snapshots as a sorted dictionary, key: the time information, value: a networkx graph. If t is provided, return graph at that particular time
        :param t: the time of the snapshot to return
        :return:
        """
        if t==None:
            return self._snapshots
        return self._snapshots[t]

    def node_presence(self, nbunch=None):
        """
        Compute for each node the list of its apparitions
        :return: a dictionary, key:node, value: list of time steps
        """
        toReturn = {}
        for (SNt,g) in self.snapshots().items():
            for n in g.nodes():
                if not n in toReturn:
                    toReturn[n]=[]
                toReturn[n].append(SNt)
        return toReturn

    def to_tensor(self,always_all_nodes=True):
        """
        Compute the list of matrices corresponding to each graph, with nodes ordered in a same order
        And the dic of nodes corresponding
        adn the list for each sn of nodes
        :always_all_nodes: if True, even if a note is not active during a snapshot, it is included in the matrix
        :return: 3 elements:(A,B,C) A: list of numpy matrices, B: a bidictionary {node name:node order in the matrix}, C: active node at each step, as a list of list of nodes
        """
        allNodes = list(self.aggregate().nodes().keys())
        nodeIDdict = bidict()
        for i in range(len(allNodes)):
            nodeIDdict[allNodes[i]] = i + 1

        # Create a dynamic network as sequence of nx graphs
        Gs = list(self.snapshots().values())
        nodesPresent = []
        GsMat = []

        nodeIdOrderedList = list(nodeIDdict.keys())
        for g0 in Gs:
            g2 = g0.copy()
            # get nodes of the current graph ordered according to the global order
            filteredOrderedNodes = [x for x in nodeIDdict.keys() if x in g2.nodes]

            # transform to numpy matrix
            if(always_all_nodes):
                g2.add_nodes_presence_from(nodeIdOrderedList)
            GsMat.append(nx.to_numpy_matrix(g2, nodelist=nodeIdOrderedList).tolist())
            nodesPresent.append([nodeIDdict[name] for name in filteredOrderedNodes])
        return(GsMat,nodeIDdict,nodesPresent)

    def full_copy(self):
        return deepcopy(self)