import sortedcontainers
from collections.abc import Iterable

import networkx as nx
from copy import deepcopy
import bidict
import numpy as np

import tnetwork as tn
import numbers
from tnetwork.dyn_graph.dyn_graph import DynGraph

from datetime import datetime, timezone
from tnetwork.dyn_graph.encodings import code_length_SN_M,code_length_SN_E

class DynGraphSN(DynGraph):
    """
    A class to represent dynamic graphs as snapshot sequence.

    Each snapshot is represented as a networkx graph, and is associated to a time step identifier. The time step can be
    an position in the sequence (1,2,3,...) or an arbitrary temporal indicator (year, timestamp...).

    Snpashots are ordered according to their time step identifier using a sorted dictionary (SortedDict).

    """


    def __init__(self, data=None,frequency=1):
        """
        Instanciate a new graph, with or without initial data

        :param data: can be a dictionary {time step:graph} or a list of graph, in which sase time steps are integers starting at 0
        :param frequency: minimal time difference between two observations. Default: 1
        """

        self._snapshots = sortedcontainers.SortedDict()
        self.frequency(frequency)
        if data!=None:
            if isinstance(data,dict):
                self._snapshots = sortedcontainers.SortedDict(data)
            elif isinstance(data,list):
                self._snapshots = sortedcontainers.SortedDict({i:g for i,g in enumerate(data)})
            else:
                raise Exception("data should be a list or a dictionary")



    def start(self):
        """
        Time of the first snapshot

        :return:
        """
        return self.snapshots_timesteps()[0]

    def end(self):
        """
        Time of the last snapshot

        :return:
        """
        return self.snapshots_timesteps()[-1]



    def add_node_presence(self, n, time):
        """
        Add presence for a node at a time

        :param n: node
        :param time: a snapshot time
        """

        if not time in self.snapshots_timesteps():
            self.add_snapshot(time)
        self._snapshots[time].add_node(n)

    def add_nodes_presence_from(self, nodes,times):
        """
        Add nodes for times

        For each node in nodes, add it for each time in times.

        :param nodes: list of nodes, or a single node
        :param times: list of times of same length as node, or a single time
        """
        if not isinstance(nodes,Iterable):
            nodes = [nodes]

        if not isinstance(times, Iterable): #means it is a single time, not list of times
            times = [times]


        for i,node in enumerate(nodes):
            for t in times:
                self.add_node_presence(node, t)

    def remove_node_presence(self, n, time):
        """
        Remove presence for a node at a time

        :param n: node
        :param time: a snapshot time
        """

        self._snapshots[time].remove_node(n)

    def add_interaction(self,u,v,time):
        """
        Add a single interaction at a single time step.

        :param u: first node
        :param v: second node
        :param time: time step identifier
        """

        self.add_interactions_from([(u,v)],[time])

    def add_interactions_from(self, nodePairs, times):
        """
        Add interactions between the provided node pairs for the provided times.

        Add each provided nodePair at each provided time

        :param nodePairs: list of pairs of nodes, or a single pair of nodes as a tuple or set
        :param times: list of times as integer or a single integer
        """
        #note: could be optimized

        #if len(nodePairs)==2 and (isinstance(nodePairs[0],str) or not isinstance(nodePairs[0],Iterable)):
        list_element_example = list(nodePairs)[0]
        if not isinstance(list_element_example, Iterable) or isinstance(list_element_example,str):
            nodePairs = [nodePairs]

        if not isinstance(times,Iterable):
            times = [times]

        for t in times:
            if not t in self._snapshots:
                self.add_snapshot(t)
            self.apply_nx_function(nx.Graph.add_edges_from,start=t,stop=t,ebunch_to_add=nodePairs)



    def remove_interaction(self,u,v,time):
        """
        Remove a single interaction at a single time step.

        Note: it does not remove the node

        :param u: first node
        :param v: second node
        :param time: time step identifier
        """

        self.remove_interactions_from([(u,v)],[time])

    def remove_interactions_from(self, nodePairs, times):
        """
        Remove interactions between the provided node pairs for the provided times.

        If one of the two parameters is a single element,
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

        for t in times:
            print("-------",t)
            self.apply_nx_function(nx.Graph.remove_edges_from,start=t,stop=t,ebunch=nodePairs)



    def graph_at_time(self,t):
        """
        Return the graph as it is at time t

        :param t: a time step identifier
        :return: the graph as a networkx graph
        """
        return self.snapshots(t)


    def add_snapshot(self, t=None, graphSN=None):
        """
        Add a snapshot for a time step t

        :param t: the time step identifier. If none, the last one + 1
        :param graphSN: the graph to add (networkx object), if None, add an empty snapshot
        """
        if t==None:
            if len(self.snapshots_timesteps())==0:
                t=0
            else:
                t=self.snapshots_timesteps()[-1]+1
        if graphSN==None:
            graphSN=nx.Graph()
        self._snapshots[t]=graphSN

    def remove_snapshot(self, t):
        """
        Remove a snapshot

        :param t: the time at which to remove a snapshot
        :return:
        """
        del self._snapshots[t]

    def snapshots_timesteps(self):
        """
        Return the list of time steps

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

    def to_DynGraphIG(self):
        """
        Convert the graph into a DynGraph_IG.

            ##Can be optimized !

        :return:
        """
        sn_duration=self.frequency()

        by_edges = dict()
        by_nodes = dict()
        for t,g in self.snapshots().items():
            for e in g.edges():
                by_edges.setdefault(frozenset(e),[]).append(t)
            for n in g.nodes():
                by_nodes.setdefault(n,[]).append(t)

        by_edges = {tuple(e):tn.Intervals.from_time_list(v,sn_duration) for e,v in by_edges.items()}
        by_nodes = {n:tn.Intervals.from_time_list(v,sn_duration) for n,v in by_nodes.items()}
        return tn.DynGraphIG(start=min(self.snapshots_timesteps()),end=max(self.snapshots_timesteps())+sn_duration,edges=by_edges,nodes=by_nodes,frequency=sn_duration)

    def to_DynGraphLS(self):
        """
        Convert to a linkstream

        Currently, conserve only edges
        :return:
        """
        sn_duration = self.frequency()

        by_edges = dict()
        by_nodes = dict()

        for t, g in self.snapshots().items():
            for e in g.edges():
                by_edges.setdefault(frozenset(e), []).append(t)
            for n in g.nodes():
                by_nodes.setdefault(n, []).append(t)

        by_edges = {tuple(e): v for e, v in by_edges.items()}
        by_nodes = {n: tn.Intervals.from_time_list(v, sn_duration) for n, v in by_nodes.items()}
        return tn.DynGraphLS(start=min(self.snapshots_timesteps()),end=max(self.snapshots_timesteps())+sn_duration,edges=by_edges,nodes=by_nodes,frequency=sn_duration)


    # def to_DynGraphIG(self, sn_duration, convert_time_to_integer=False):
    #     """
    #     Convert the graph into a DynGraph_IG.
    #
    #     ##Can be optimized !
    #
    #     By default, snapshots last from their time ID to the time ID of the next snapshot.
    #     Be careful, for the last snaphsot, we cannot know his duration, therefore, if sn_duration is not provided, it has a default duration equal to the min
    #     of all durations
    #
    #     :param sn_duration: duration of sns, None for automatic behavior
    #     :param convert_time_to_integer: if True, use the snapshot order in the list of SN rather than its time step
    #     :return:
    #     """
    #     toReturn = tn.DynGraphIG()
    #
    #
    #     for i in range(len(self._snapshots)):
    #         if convert_time_to_integer:
    #             current_t=i
    #             tNext=i+1
    #         else:
    #             current_t = self._snapshots.peekitem(i)[0]
    #
    #             if sn_duration!=None:
    #                 tNext = current_t+sn_duration
    #
    #             else:
    #                 if i<len(self._snapshots)-1:
    #                     tNext=self._snapshots.peekitem(i + 1)[0]
    #                 else:
    #                     #computing the min duration to choose as duration of the last period
    #                     dates = self.snapshots_timesteps()
    #
    #                     minDuration = min([dates[i + 1] - dates[i] for i in range(len(dates) - 1)])
    #                     tNext = current_t+minDuration
    #
    #         if (len(self._snapshots.peekitem(i)[1].nodes()))>0:
    #             toReturn.add_nodes_presence_from(self._snapshots.peekitem(i)[1].nodes(), (current_t, tNext))
    #
    #             if len(list(self._snapshots.peekitem(i)[1].edges()))>0:
    #                 toReturn.add_interactions_from(list(self._snapshots.peekitem(i)[1].edges()), (current_t, tNext) )
    #
    #
    #     return toReturn

    def _combine_weighted_graphs(self,graphList, weight=1.0):
        """
        Function to aggregate several graphs into a weighted graph

        :param graphList: enumerable of graphs
        :param weight: default weight
        :return:
        """
        newG = nx.Graph()
        for g in graphList:
            e_weights = nx.get_edge_attributes(g, "weight")
            n_weights = nx.get_node_attributes(g,"weight")

            # add weight of one to unweighted graphs
            if len(e_weights) == 0:
                e_weights = {(u, v): 1 for (u, v) in g.edges()}
            if len(n_weights) == 0:
                n_weights = {n: 1 for n in g.nodes()}

            for n, w in n_weights.items():
                if newG.has_node(n):
                    newG.nodes[n]["weight"] += w
                else:
                    newG.add_node(n, weight=w)

            for (u, v), w in e_weights.items():
                if newG.has_edge(u, v):
                    newG[u][v]["weight"] += w
                else:
                    newG.add_edge(u, v, weight=w)
        return newG


    def cumulated_graph(self,times=None):
        """
        Compute the cumulated graph.

        Return a networkx graph corresponding to the cumulated graph of the given period (whole graph by default)

        :param times: list/set of time steps ID of snapshots to cumulate. Default (None) means all snapshots
        :return: a networkx (weighted) graph
        """

        if times==None:
            snapshots=list(self.snapshots().values())
        else:
            snapshots= [sn for t,sn in self.snapshots().items() if t in times]

        return self._combine_weighted_graphs(snapshots)

    def slice(self,start,end):
        """
        Keep only the selected period

        :param start: time of the beginning of the slice
        :param end: time of the end of the slice
        """

        to_return = tn.DynGraphSN()
        interv = tn.Intervals((start,end))
        for t in list(self._snapshots.keys()):
            if interv.contains_t(t):
                to_return.add_snapshot(t,self._snapshots[t])
        return to_return

    def change_times(self):
        """
        Times of non-empty snapshots

        :return: list of times
        """
        return [t for t,g in self.snapshots().items() if len(g.edges()) > 0]

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

        toReturn = DynGraphSN(frequency=bin_size)
        for (binStart,binEnd) in bins:
            keys = self.snapshots().irange(binStart, binEnd, inclusive=(True, False))
            keys = list(keys)
            if len(keys)>0:
                if weighted:
                    toReturn.add_snapshot(binStart, self._combine_weighted_graphs([self._snapshots[k] for k in keys]))
                else:
                    all_edges = [list(self._snapshots[k].edges()) for k in keys]
                    all_edges = list(set([e for edge_list in all_edges for e in edge_list ]))
                    toReturn.add_snapshot(binStart,nx.Graph(all_edges))
                    #toReturn.add_snapshot(binStart,nx.compose_all([self._snapshots[k] for k in keys]))

            else:
                toReturn.add_snapshot(binStart)

        toReturn.discard_empty_snapshots()
        return toReturn

    def _get_monday_from_calendar_week(self, year, calendar_week):
        monday = datetime.datetime.strptime(f'{year}-{calendar_week}-1', "%Y-%W-%w").date()
        return monday

    def _date_threasholded(self,date,period):
        date = date.replace(second=0)
        if period == "minute":
            return date
        date = date.replace(minute=0)
        if period == "hour":
            return date
        date = date.replace(hour=0)
        if period == "day":
            return date


        if period == "week":
            week = date.isocalendar()[1]
            temp = datetime.combine(self._get_monday_from_calendar_week(date.year, week), datetime.min.time())
            return temp

        date = date.replace(day=0)

        if period == "month":
            return date
        date = date.replace(month=0)
        if period == "year":
            return date

    def aggregate_time_period(self, period, step_to_datetime=datetime.utcfromtimestamp):
        """
        Aggregate graph by time period (day, year, ...)

        Return a new dynamic graph without modifying the original one, aggregated such as all
        Yielded graphs are weighted (weight: number of apparition of edges during the period)

        :param period: either a string (minute,hour,day,week,month,year) or a function returning the timestamp truncated to the start of the desired period
        :param step_to_datetime: function to convert time step to a datetime object, default is utfromtimestamp
        :return: a DynGraph_SN object
        """
        to_return = tn.DynGraphSN()



        if isinstance(period,str):
            period_func = lambda x : self._date_threasholded(x,period)
        else:
            period_func = period

        for t,g in self.snapshots().items():
            t_date = step_to_datetime(t)

            new_t = period_func(t_date)

            #new_t = new_t.timestamp()
            new_t = int(new_t.replace(tzinfo=timezone.utc).timestamp())
            if not new_t in to_return.snapshots():
                to_return.add_snapshot(new_t, g)
            to_return._snapshots[new_t]=self._combine_weighted_graphs([to_return.snapshots(new_t),self.snapshots(t)])
        to_return.frequency(to_return.snapshots_timesteps()[1]-to_return.snapshots_timesteps()[0])
        to_return.discard_empty_snapshots()
        return to_return

    def snapshots(self, t=None):
        """
        Return all snapshots or a particular one

        Default: return a  sorted dictionary, key: the time information, value: a networkx graph.
        If t is provided, return graph at that particular time

        :param t: the time of the snapshot to return
        :return:
        """
        if t==None:
            return self._snapshots
        return self._snapshots[t]

    def node_presence(self, nodes=None):
        """
        Presence time of nodes

         Several usages:

        * If nodes==None (default), return a dict for each note, its existing times
        * If nodes is a single node, return the interval of presence of this node
        * If nodes is a set of nodes, return interval of presence of those nodes as a dictionary

        :param nodes: list of ndoes
        :return: a dictionary, key:node, value: list of time steps
        """


        if isinstance(nodes,str):
            nodes= {nodes}

        toReturn = {}
        for (SNt,g) in self.snapshots().items():
            if nodes==None:
                nodes_this_step = g.nodes()
            else:
                nodes_this_step = g.nodes() & nodes
            for n in nodes_this_step:
                toReturn.setdefault(n,[])
                toReturn[n].append(SNt)
        if nodes!=None and len(nodes)==1:
            return toReturn[list(nodes)[0]]
        return toReturn

    def edge_presence(self, edges=None):
        """
        Presence time of edges

         Several usages:

        * If edges==None (default), return a dict for each edge, its existing times
        * If edges is a set of edges, return interval of presence of those edges as a dictionary

        :param edges: list of edges
        :return: a dictionary, key:edge(pair), value: list of time steps
        """

        if edges!=None:
            list_element_example = list(edges)[0]
            if not isinstance(list_element_example, Iterable) or isinstance(list_element_example, str):
                edges = [edges]

        toReturn = {}
        for (SNt, g) in self.snapshots().items():
            if edges == None:
                edges_this_step = g.edges()
            else:
                edges_this_step = g.edges() & edges
            for e in edges_this_step:
                ef = frozenset([e[0],e[1]])
                toReturn.setdefault(ef, [])
                toReturn[ef].append(SNt)

        if edges != None:
            to_return2 = {}
            for e in edges:
                e2=frozenset(e)
                to_return2[e2]=toReturn[e2]
            if len(to_return2)==1:
                return list(to_return2.values())[0]
            return to_return2

        return toReturn


    def to_tensor(self,always_all_nodes=True):
        """
        Return a tensor representation

        Compute the list of matrices corresponding to each graph, with nodes ordered in a same order
        And the dic of nodes corresponding
        and the list for each sn of nodes
        :param always_all_nodes: if True, even if a node is not active during a snapshot, it is included in the matrix
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

    def last_snapshot(self):
        """
        Return the last snapshot

        :return: the last snapshot as a networkx graph
        """
        return self.snapshots()[self.snapshots_timesteps()[-1]]

    def full_copy(self):
        return deepcopy(self)


    def normalize_to_integers(self,nodes_start_at=1,time_start_at=1):
        """
        Transform time IDs and nodes to Integer


        :return: a new dynamic graph object, a dictionary of nodes {originalID:newID} and a dictionary of times {originalID:newID}
        """
        all_nodes = set()
        to_return = tn.DynGraphSN()
        for g in self.snapshots().values():
            all_nodes.update(set(g.nodes))
        nodes_dict = {v: (i+nodes_start_at) for i, v in enumerate(all_nodes)}

        for i,g in enumerate(self.snapshots().values()):
            to_return.add_snapshot(i+time_start_at,nx.relabel_nodes(g, nodes_dict))

        times = list(self.snapshots().keys())
        time_dict = {i+time_start_at:times[i] for i in range(len(times))}
        nodes_dict_inv = {v:k for k,v in nodes_dict.items()}

        return to_return,nodes_dict_inv,time_dict

    def code_length(self,as_matrix=True,as_edgelist=True):
        to_return =[]
        to_return.append(code_length_SN_M(self))
        to_return.append(code_length_SN_E(self))

        return tuple(to_return)
    # def code_length(self,as_ls=False):
    #     if as_ls:
    #         return self.code_length_ls()
    #     else:
    #         return self.code_length_sn()

    # def code_length_sn(self):
    #     """
    #     Time info should not be repeated
    #     2 versions:
    #     - edges are little repeated => each interaction encoded explicitly
    #     - edges are strongly repeated => matrix form
    #     :return:
    #     """
    #     #we ignore the code of edges identical for all
    #     g_cumulated = self.cumulated_graph()
    #     node_encoding = np.log2(len(g_cumulated.nodes()))
    #     edge_encoding = node_encoding*2
    #     nb_time = len([x for x in self.snapshots().values() if len(x.edges())>0])
    #     time_encoding =  np.log2(nb_time)# +1 for stop
    #
    #     nb_unique_edges = len(g_cumulated.edges())
    #     nb_interactions = sum([len(x.edges()) for x in self.snapshots().values()])
    #
    #     #if "matrix_form":
    #     #matrix form
    #     total_code_matrix = nb_unique_edges*nb_time+edge_encoding*nb_unique_edges+time_encoding*nb_time
    #     print("sn_m: ",edge_encoding,time_encoding,nb_unique_edges,nb_time)
    #     #else:
    #     print("sn_e: ",edge_encoding,time_encoding,nb_interactions,nb_time)
    #     #T1_(N1,N2)_(N3,N4)_STOP_T2_...
    #     total_code_edges = nb_interactions*edge_encoding + nb_time*time_encoding + nb_time*edge_encoding
    #     return total_code_matrix,total_code_edges

    # def _compute_encoding_properties(self):
    #
    #     nb_nodes = len(g_cumulated.nodes())
    #     nb_time = len([x for x in self.snapshots().values() if len(x.edges()) > 0])
    #     #time_encoding = np.log2(len(self.snapshots()))  # +1 for stop
    #     nb_unique_edges = len(g_cumulated.edges())
    #     nb_interactions = sum([len(x.edges()) for x in self.snapshots().values()])
    #     return(nb_nodes,nb_unique_edges,nb_interactions,nb_time)



    def code_length_update(self):
        g_cumulated = self.cumulated_graph()
        node_encoding = np.log2(len(g_cumulated.nodes()))
        edge_encoding = node_encoding * 2
        nb_time = len([x for x in self.snapshots().values() if len(x.edges()) > 0])
        nb_unique_edges = len(g_cumulated.edges())
        #nb_interactions = sum([len(x.edges()) for x in self.snapshots().values()])
        nb_changes = 0
        ordered_graphs = list(self.snapshots().values())
        for i,g in enumerate(ordered_graphs):
            if i==0:
                nb_changes+=len(g.edges())
            else:
                #modified_edges = nx.symmetric_difference(ordered_graphs[i-1],ordered_graphs[i])
                some_edges_1 = {tuple(sorted(edge)) for edge in ordered_graphs[i-1].edges()}
                some_edges_2 = {tuple(sorted(edge)) for edge in ordered_graphs[i].edges()}
                changes= some_edges_1.symmetric_difference(some_edges_2)


                nb_changes+=len(changes)

        time_encoding = np.log2(nb_time)

        #T1_(N1,N2)_(N3,N4)_STOP_T2_CHANGE...
        total_code_edges = nb_changes*edge_encoding + nb_time*time_encoding + nb_time*edge_encoding
        print("updates: ",edge_encoding,time_encoding,nb_changes,nb_unique_edges)

        return total_code_edges

    def stability(self):
        """
        Fraction of successive edge appearances that are in adjacent snasphots
        :return:
        """
        times = self.snapshots_timesteps()
        edge_presence = self.edge_presence()
        successions = 0
        adjacent=0
        for n,presences in edge_presence.items():
            successions += len(presences)-1
            for i in range(len(presences)-1):
                if times.index(presences[i])==times.index(presences[i+1])-1:
                    adjacent+=1
        print(adjacent,successions)
        if successions==0:
            return 1
        return adjacent/successions

    def synchronicity(self):
        """
        Fraction of edges life that appear

        Careful, naive version currently !!!

        for each edge, over its period of existence
        for each other edge, how many appearance, thus how many simultaneous possible
        and how many effective

        -Must take into account that nodes exist over period: if their lifetime do not overlap they are not supposed to be
        synchronous
        -Must take into account that



        :return:
        """

        # times = self.snapshots_timesteps()
        # edge_presence = self.edge_presence()
        # active = 0
        # sn_during_life = 0
        # for n, presences in edge_presence.items():
        #     active += len(presences)
        #     sn_during_life += times.index(presences[-1])- times.index(presences[0])+1
        # print(active, sn_during_life)
        # return active / sn_during_life



        times = self.snapshots_timesteps()
        non_zero = [t for t in times if len(self.snapshots(t).edges())>0]

        edge_presence = self.edge_presence()
        nb_different_edges = len(edge_presence)

        total_interactions = sum([len(x) for x in edge_presence.values()])
        avg_inter_by_sn = total_interactions/len(non_zero)
        #max_possible_inter_by_sn = nb_different_edges
        max_possible_inter_by_sn=total_interactions/max([len(x) for x in edge_presence.values()])
        print("synchro",avg_inter_by_sn,max_possible_inter_by_sn)
        return avg_inter_by_sn/max_possible_inter_by_sn

    def write_interactions(self,filename):
        """
        Write interactions in a file

        Write in corresponding json format

        :param filename:
        :return:
        """
        tn.write_as_SN_E(self,filename)

    def discard_empty_snapshots(self):
        """
        Discard snapshots with no edges

        """
        to_remove=[]
        for t,g in self.snapshots().items():
            if len(g.edges())==0 and len(g.nodes())==0:
                to_remove.append(t)
        for t in to_remove:
            self.remove_snapshot(t)