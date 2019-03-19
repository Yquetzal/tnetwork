import sortedcontainers
from collections import Iterable

import networkx as nx
from copy import deepcopy
from tnetwork.utils.bidict import bidict
import pkg_resources

import tnetwork as tn
import numbers
from tnetwork.dyn_graph.dyn_graph import DynGraph

from datetime import datetime, timezone

class DynGraphSN(DynGraph):
    """
    A class to represent dynamic graphs as snapshot sequence.

    Each snapshot is represented as a networkx graph, and is associated to a time step identifier. The time step can be
    an position in the sequence (1,2,3,...) or an arbitrary temporal indicator (year, timestamp...).

    Snpashots are ordered according to their time step identifier using a sorted dictionary (SortedDict).

    """


    def __init__(self, data=None):
        """
        Instanciate a new graph, with or without initial data

        :param data: can be a dictionary {time step:graph} or a list of graph, in which sase time steps are integers starting at 0
        """

        self._snapshots = sortedcontainers.SortedDict()
        if data!=None:
            if isinstance(data,dict):
                self._snapshots = sortedcontainers.SortedDict(data)
            elif isinstance(data,list):
                self._snapshots = sortedcontainers.SortedDict({i:g for i,g in enumerate(data)})
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


        dg = tn.read_graph_link_stream(fileLocation)
        return dg


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
        Add interactions between nodes for times

        :param nodes: list of nodes, or a single node
        :param times: list of times of same length as node, or a single time
        """
        if not isinstance(nodes,list):
            nodes = list([nodes])
            if len(nodes)==1:
                nodes=nodes*len(times)

        if isinstance(times, numbers.Number): #means it is a single time, not list of times
            times = [times]*len(nodes)


        for i,node in enumerate(nodes):
            self.add_node_presence(node, times[i])

    def remove_node_presence(self, n, time):
        """
        Remove presence for a node at a time

        :param n: node
        :param time: a snapshot time
        """

        self._snapshots[time].remove_node(n)

    def add_interaction(self,u_of_edge,v_of_edge,time):
        """
        Add a single interaction at a single time step.

        :param u_of_edge: first node
        :param v_of_edge: second node
        :param time: time step identifier
        """

        self.add_interactions_from([(u_of_edge,v_of_edge)],[time])

    def add_interactions_from(self, nodePairs, times):
        """
        Add interactions between the provided node pairs for the provided times.

        If one the two parameters is a single element,
        will add the node pair at all provided time steps, or all the node pairs at the provided time step.

        :param nodePairs: list of pairs of nodes, or a single pair of nodes
        :param times: list of times for this node, or a single time
        """
        #note: could be optimized

        if len(nodePairs)==2 and (isinstance(nodePairs[0],str) or not isinstance(nodePairs[0],Iterable)):
            nodePairs = [nodePairs]*len(times)
        if not isinstance(times,Iterable):
            times = [times]*len(nodePairs)

        for i,nodePair in enumerate(nodePairs):
            t = times[i]
            if not t in self._snapshots:
                self.add_snapshot(t)
            self.apply_nx_function(nx.Graph.add_edge,start=t,stop=t,u_of_edge=nodePair[0],v_of_edge=nodePair[1])



    def remove_interaction(self,u_of_edge,v_of_edge,time):
        """
        Remove a single interaction at a single time step.

        Note: it does not remove the node

        :param u_of_edge: first node
        :param v_of_edge: second node
        :param time: time step identifier
        """

        self.remove_interactions_from([(u_of_edge,v_of_edge)],[time])

    def remove_interactions_from(self, nodePairs, times):
        """
        Remove interactions between the provided node pairs for the provided times.

        If of the two parameters is a single element,
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

    def to_DynGraphIG(self, sn_duration=None, convert_time_to_integer=False):
        """
        Convert the graph into a DynGraph_IG.

        By default, snapshot_affiliations last from their time ID to the time ID of the next snapshot.
        Be careful, for the last snaphsot, we cannot know his duration, therefore, if sn_duration is not provided, it has a default duration equal to the min
        of all durations

        :param sn_duration: duration of sns
        :param convert_time_to_integer: if True, use the snapshot order in the list of SN rather than its time step
        :return:
        """
        toReturn = tn.DynGraphIG()


        for i in range(len(self._snapshots)):
            if convert_time_to_integer:
                current_t=i
                tNext=i+1
            else:
                current_t = self._snapshots.peekitem(i)[0]

                if sn_duration!=None:
                    tNext = current_t+sn_duration

                else:
                    if i<len(self._snapshots)-1:
                        tNext=self._snapshots.peekitem(i + 1)[0]
                    else:
                        #computing the min duration to choose as duration of the last period
                        dates = self.snapshots_timesteps()
                        minDuration = min([dates[i + 1] - dates[i] for i in range(len(dates) - 1)])
                        tNext = current_t+minDuration

            if (len(self._snapshots.peekitem(i)[1].nodes()))>0:
                toReturn.add_nodes_presence_from(self._snapshots.peekitem(i)[1].nodes(), (current_t, tNext))

                if len(list(self._snapshots.peekitem(i)[1].edges()))>0:
                    toReturn.add_interactions_from(list(self._snapshots.peekitem(i)[1].edges()), (current_t, tNext) )


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
            e_weights = nx.get_edge_attributes(g, "weight")
            n_weights = nx.get_node_attributes(g,"weight")

            # add weight of one to unweighted graphs
            if len(e_weights) == 0:
                e_weights = {(u, v): 1 for (u, v) in g.edges()}
            if len(n_weights) == 0:
                n_weights = {n: 1 for n in g.nodes()}

            for n, w in n_weights.items():
                if newG.has_node(n):
                    newG.node[n]["weight"] += w
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


    def aggregate_sliding_window(self, bin_size=None, shift=None, t_start=None, t_end=None):
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

        toReturn = DynGraphSN()
        for (binStart,binEnd) in bins:
            #print("aggregating",binStart,binEnd)
            keys = self.snapshots().irange(binStart, binEnd, inclusive=(True, False))
            keys = list(keys)
            if len(keys)>0:
                toReturn.add_snapshot(binStart, self._combine_weighted_graphs([self._snapshots[k] for k in keys]))
            else:
                toReturn.add_snapshot(binStart)
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

        return to_return

    def snapshots(self, t=None):
        """
        Return snapshot_affiliations as a sorted dictionary, key: the time information, value: a networkx graph. If t is provided, return graph at that particular time
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

    def last_snapshot(self):
        """
        Return the last snapshot

        :return: the last snapshot as a networkx graph
        """
        return self.snapshots()[self.snapshots_timesteps()[-1]]

    def full_copy(self):
        return deepcopy(self)