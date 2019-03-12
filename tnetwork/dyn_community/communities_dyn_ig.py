from tnetwork.dyn_community.communitiesEventsHandler import *
from tnetwork.utils.intervals import *
import operator
import math
from tnetwork.utils.community_utils import affiliations2nodesets

class DynCommunitiesIG:
    """
    Dynamic affiliations as interval graphs

    This class maintains a redondant representation for faster access: 
    _by_node: for each node, for each community, Interval of affectation
    _by_com: for each com, for each node, Interval of affectation
    Note that they are hidden for this reason, if you modify one, you need to be careful maintaining the other one.
    You can however access them without problem directly, or use the corresponding functions (affiliations and affiliations)
    
    """
    def __init__(self,start=None,end=None):
        """
        Instanciate a dynamic community structure

        A start end end dates can be used to give a "duration" to the graph independently from its nodes and edges
        (for instance, to study activity during a whole year, the graph might start on January 1st at 00:00 while
        the first recorded activity occurs in the afternoon or on another day)

        :param start: set a start time, by default will be the first time of the added affiliations
        :param end: set an end time, by default will be the last time of the added affiliations
        """
        self._by_node = {} #type:{str:{str:{Intervals}}
        self._by_com = {} #type:{str:{str:{Intervals}}
        self.events=CommunitiesEvent()

        if start==None:
            self.start=math.inf
        if end==None:
            self.end=-math.inf


    def _affiliations_at_t(self,t):
        """
        Afilliations at t
        :param t:
        :return: dictionary (by node) of list of communities
        """
        to_return ={}
        for n in self._by_node:
            for c,period in self._by_node[n].items():
                if period.contains_t(t):
                    to_return.setdefault(n,set())
                    to_return[n].add(c)
        return(to_return)

    def affiliations(self, t=None):
        """
        Affiliations by nodes

        :param t: time of the affiliations ro return. Default: all
        :return: either a dictionary (by node) of dictionaries (by community) of Intervals if t==None or a dictionary (by node) of list of communities
        """
        if t==None:
            return self._by_node

        return self._affiliations_at_t(t)
    
    def communities(self, t=None):
        """
        Affiliations by communities

        :param t: time of the affiliations ro return. Default: all
        :return: either a dictionary (by community) of dictionaries (by node) of Intervals if t==None or a dictionary (by community) of Intervals
        """
        if t == None:
            return self._by_com

        return affiliations2nodesets(self.affiliations(t))

    def add_affiliation(self, n:str, com:str, times:(int, int)):
        """
        Affiliate node n to community com for period times

        :param n: node
        :param com: community
        :param times: period as a pair (int,int)

        """
        n = str(n)
        self._by_node.setdefault(n, {}).setdefault(com, Intervals()).add_interval(times)
        self._by_com.setdefault(com, {}).setdefault(n, Intervals()).add_interval(times)

        self.start = min(self.start, min(times))
        self.end = max(self.end, max(times))

    def add_affiliations_from(self, clusters, times):
        """
        Add affiliations provided as a cluster

        Given a cluster provided as a dict or bidict {frozenset of nodes}:id , add it for the period times

        :param clusters: dict or bidict{frozenset of nodes}:id
        """
        for affils,id in clusters.items():
            for n in affils:
                self.add_affiliation(n, id, times)

    def remove_affiliation(self, n:str, com, times:(int,int)):
        """
        Remove affiliations

        remove affiliations of node n from community com between the period times

        :param n: node
        :param com: community
        :param times: Intervals
        """
        (t,e) = times
        n = str(n)
        self._by_node[n][com].remove_interval((t, e))
        self._by_com[com][n].remove_interval((t, e))

    def affiliations_durations(self, nodes=None, communities=None):
        """
        Durations of affiliations

        Return the duration in each community (for non-zero values) for the provided nodes and the provided affiliations (default: all)
        return set of triplets (n,c,duration), or set of pairs of one if the parameters has a single value, or a single value if single node and single com

        :param nodes: node(s) for which we want durations. single node or set of nodes
        :param communities: communities(s) for which we want durations. single community or set of communities
        :return: set of triplets (n,c,duration), or set of pairs of one if the parameters has a single value, or a single value if single node and single com

        """

        toReturn={}
        if nodes==None:
            nodes=self._by_node.keys()
        if communities==None:
            communities=self._by_com.keys()

        if isinstance(nodes,str):
            nodes=[nodes]
        if isinstance(communities,str):
            communities=[communities]
            nodes = set(nodes)
        communities = set(communities)

        for n in nodes:
            for c in communities & set(self._by_node[n]):
                toReturn[(n,c)]=self._by_node[n][c].duration()

        if len(nodes)==1:
            toReturn = {c:t for (n,c),t in toReturn.items()}
        if len(communities)==1:
            toReturn = {n:t for (n,c),t in toReturn.items()}
        if len(nodes)==1 and len(communities)==1:
            toReturn = list(toReturn.items)[0][1]
        return toReturn

    def nodes_main_com(self):
        """
        Main community for each node

        Function that return for each node the community in which it spends the most time

        :return: dictionary, {node:community)
        """
        node2Com = {}
        for n in self._by_node:
            belongings = self.affiliations_durations(n)  # for each community, belonging duration
            ordered = sorted(belongings.items(), key=operator.itemgetter(1))
            ordered.reverse()
            node2Com[n] = ordered[0][0]  # assign to each node its main com

        return node2Com

    def nodes_natural_order(self):
        """
        Nodes by lexicographic order

        :return: list od nodes
        """
        return sorted(list(self._by_node.keys()))

    def nodes_ordered_by_com(self,node2com=None):
        """
        Nodes ordered by their main community

        return nodes such as those with the same main community are close to each other.
        By default, use the main community according to function nodes_main_com
        Another order can be passed in parameter.

        :param node2Com: a dictionary associating a node to its main affiliation
        :return: list of nodes
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
