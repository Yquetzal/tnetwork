from tnetwork.dyn_community.communitiesEventsHandler import *
from tnetwork.utils.intervals import *
import numpy as np
import operator
import math

class DynamicCommunitiesSG:
    """

    """
    def __init__(self,start=None,end=None):
        """
        :param start: set a start time, by default will be the first time of the added snapshots
        :param end: set an end time, by default will be the last time of the added snapshots
        """
        self.nodes = {} #type:{str:{str:{Intervals}}
        self.communities = {} #type:{str:{str:{Intervals}}
        self.events=CommunitiesEvent()

        if start==None:
            self.start=math.inf
        if end==None:
            self.end=-math.inf

    def snapshots(self, t=None):
        if t==None:
            return self.nodes

        return self.communities_at_t(t)

    def add_belonging(self, n:str, com:str, times:(int,int)):
        """
        Add the node n to the community com during the period described in times
        :param n:
        :param com:
        :param times:
        :return:
        """
        n = str(n)
        self.nodes.setdefault(n,{}).setdefault(com, Intervals()).add_interval(times)
        self.communities.setdefault(com, {}).setdefault(n, Intervals()).add_interval(times)

        self.start = min(self.start, min(times))
        self.end = max(self.end, max(times))

    def add_belongins_from(self,clusters, times):
        """
        Given a cluster provided as a dict or bidict {frozenset of nodes}:id , add it to time t
        :param clusters: dict or bidict{frozenset of nodes}:id
        """
        for affils,id in clusters.items():
            for n in affils:
                self.add_belonging(n,id,times)

    def remove_belonging(self, n, com, t, e=np.inf):
        n = str(n)
        self.nodes[n][com].remove_interval((t, e))
        self.communities[com][n].remove_interval((t, e))

    def communities_at_t(self, t:int):
        to_return = dict()
        for n,coms in self.nodes.items():
            for c,period in coms.items():
                if period.contains_t(t):
                    to_return[n]=c
        return to_return

    def belongings_durations(self, nodes=None, communities=None):
        """
        return the duration in each community (for non-zero values) for the provided nodes and the provided snapshots (default: all)
        return set of triplets (n,c,duration), or set of pairs of one if the parameters has a single value, or a single value if single node and single com
        :param nBunch:
        :param cBunch:
        :return:
        """

        toReturn={}
        if nodes==None:
            nodes=self.nodes.keys()
        if communities==None:
            communities=self.communities.keys()

        if isinstance(nodes,str):
            nodes=[nodes]
        if isinstance(communities,str):
            communities=[communities]
            nodes = set(nodes)
        communities = set(communities)

        for n in nodes:
            for c in communities & set(self.nodes[n]):
                toReturn[(n,c)]=self.nodes[n][c].duration()

        if len(nodes)==1:
            toReturn = {c:t for (n,c),t in toReturn.items()}
        if len(communities)==1:
            toReturn = {n:t for (n,c),t in toReturn.items()}
        if len(nodes)==1 and len(communities)==1:
            toReturn = list(toReturn.items)[0][1]
        return toReturn

    def nodes_main_com(self):
        """
        Function that return a node order trying to keep nodes belonging to the same snapshots close to each other
        :param theDynCom:
        :return:
        """
        node2Com = {}
        for n in self.nodes:
            belongings = self.belongings_durations(n)  # for each community, belonging duration
            ordered = sorted(belongings.items(), key=operator.itemgetter(1))
            ordered.reverse()
            node2Com[n] = ordered[0][0]  # assign to each node its main com

        return node2Com

    def nodes_natural_order(self):
        return sorted(self.nodes)

    def nodes_ordered_by_com(self,node2com=None):
        """
        return nodes such as those with the same main community are close to each other. By default, use the main community according to function nodes_main_com
        :param node2Com: a dictionary associating a node to its communities

        :return:
        """
        if node2com==None:
            node2com = self.nodes_main_com()
        allMainComs = sorted(set(node2com.values()))

        to_return = []
        for c in allMainComs:
            for n in node2com:
                if node2com[n] == c:
                    to_return.append(n)
        return to_return
