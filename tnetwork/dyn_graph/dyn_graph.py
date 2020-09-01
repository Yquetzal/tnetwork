from collections.abc import Iterable
import networkx as nx

class DynGraph():
    """
    Template of dynamic networks.

    Contains functions that must be implemented by all types of dynamic networks
    """

    def node_presence(self, nbunch=None):
        """
        Return presence time of nodes
        """
        raise NotImplementedError("Not implemented")

    def frequency(self,value:int=None):
        """
        Set and/or return graph frequency

        The frequency of a dynamic network is the smallest possible difference between two consecutive observations.
        Note that if for some reason you really need continuous value, you can set the frequency to -1, but you will need
        to set explicitely the temporality every time it is needed for a computation (conversion between formats, visualization, etc)

        :param value: if None, the frequency is not changed. If -1, time is considered continuous.
        :return: current frequency value
        """
        if value!=None:
            self.freq=value
        return self.freq

    def summary(self):
        """
        Print a summary of the graph
        """
        print("start:",self.start())
        print("end:",self.end())
        print("nb_nodes: ",len(self.node_presence()))
        print("nb_interactions: ",len(self.interactions()))

    def edge_presence(self, nbunch=None):
        """
        Return presence time of edges
        """
        raise NotImplementedError("Not implemented")

    def add_interaction(self,u,v,time):
        """
        Add an interaction at a time
        """
        raise NotImplementedError("Not implemented")

    def add_interactions_from(self, nodePairs, times):
        """
        Add interactions at times
        """
        raise NotImplementedError("Not implemented")


    def add_node_presence(self,node,time):
        """
        Add presence of a node
        """
        raise NotImplementedError("Not implemented")

    def add_nodes_presence_from(self, nodes, times):
        """
        Add nodes at times
        """
        raise NotImplementedError("Not implemented")

    def remove_node_presence(self,node,time):
        """
        Remove a node presence
        """
        raise NotImplementedError("Not implemented")

    def graph_at_time(self,t):
        """
        Return graph at a time
        """
        raise NotImplementedError("Not implemented")

    def remove_interaction(self,u,v,time):
        """
        Remove an interaction at a time
        """
        raise NotImplementedError("Not implemented")

    def remove_interactions_from(self, nodePairs, times):
        """
        Remove interactions at times
        """
        raise NotImplementedError("Not implemented")

    def cumulated_graph(self,times=None):
        """
        Return the cumulated graph over a period
        """
        raise NotImplementedError("Not implemented")

    def slice(self,start, end):
        """
        Return a slice of the temporal network

        :param start: start of the slice
        :param end: end of the slice
        :return:
        """
        raise NotImplementedError("Not implemented")

    def start(self):
        """
        First valid date of the data
        """
        raise NotImplementedError("Not implemented")

    def end(self):
        """
        Last valid date of the data
        """
        raise NotImplementedError("Not implemented")

    def interactions(self):
        """
         Return all interactions as a set

         :return: a set of pairs ((n1,n2),time)
         """
        to_return = []
        for e, presences in self.edge_presence().items():
            to_return += [(e, p) for p in presences]
        return set(to_return)

    def change_times(self):
        """
        Return all times with interactions/change
        """
        raise NotImplementedError("Not implemented")

    def aggregate_sliding_window(self, bin_size=None, shift=None, t_start=None, t_end=None,weighted=True):
        """
        Aggregate using sliding windows
        """
        raise NotImplementedError("Not implemented")

    def write_interactions(self,filename):
        """
        Export custom format with only interactions
        """
        raise NotImplementedError("Not implemented")
