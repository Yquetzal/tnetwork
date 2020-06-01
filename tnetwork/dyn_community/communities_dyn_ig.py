from tnetwork.dyn_community.communitiesEventsHandler import *
from tnetwork.utils.intervals import *
import operator
import math
from tnetwork.utils.community_utils import affiliations2nodesets
from collections.abc import Iterable
import tnetwork as tn
from tnetwork.dyn_community.communities_dyn import DynCommunities
import numbers


class DynCommunitiesIG(DynCommunities):
    """
    Dynamic communities as interval graphs

    This class maintains a redondant representation for faster access:

    * _by_node: for each node, for each community, Interval of affectation (affectations)
    * _by_com: for each com, for each node, Interval of affectation (communities)

    Note that they are hidden for this reason, if you modify one, you need to be careful maintaining the other one.
    You can however access them without problem directly, or use the corresponding functions (affiliation and communities)
    
    """
    def __init__(self,start=None,end=None):
        """
        Instanciate a dynamic community structure

        Start and end dates can be used to give a "duration" to the graph independently from its nodes and edges
        (for instance, to study activity during a whole year, the graph might start on January 1st at 00:00 while
        the first recorded activity occurs in the afternoon or on another day)

        :param start: set a start time, by default will be the first time of the added snapshot_affiliations
        :param end: set an end time, by default will be the last time of the added snapshot_affiliations
        """
        self._by_node = {} #type:{str:{str:{Intervals}}
        self._by_com = {} #type:{str:{str:{Intervals}}
        self.events=CommunitiesEvent()

        if start==None:
            self.start=math.inf
        if end==None:
            self.end=-math.inf


    def slice(self,start,end):
        """
        Keep only the selected period

        :param start: start of the period to keep
        :param end: end of the period to keep
        :return: a dynamic graph over the period
        """

        to_return = tn.DynCommunitiesIG()
        interv = tn.Intervals((start,end))
        for c_id,c in self.communities().items():
            for n,the_inter in c.items():
                duration = interv.intersection(the_inter)
                if duration.duration()>0:
                    to_return.add_affiliation(n,c_id,duration)
        return to_return

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
        :return: either a dictionary (by node) of dictionaries (by community) of Intervals if t==None or a dictionary (by node) of list of snapshot_communities
        """
        if t==None:
            return self._by_node

        return self._affiliations_at_t(t)
    
    def communities(self, t=None):
        """
        Affiliations by communities

        :param t: time of the community ro return. Default: all
        :return: either a dictionary (by community) of dictionaries (by node) of Intervals if t==None or a dictionary (by community) of Intervals
        """
        if t == None:
            return self._by_com

        affils = self.affiliations(t)
        return affiliations2nodesets(affils)

    def _fast_set_affiliations(self, affils_by_communities):
        self._by_com = affils_by_communities
        for c in self._by_com:
            for n in self._by_com[c]:
                self._by_node.setdefault(n,{})[c]=self._by_com[c][n]
                self.start=min([self.start,self._by_com[c][n].start()])
                self.end=max([self.end,self._by_com[c][n].end()])



    def _2Intervals(self,to_convert):
        if isinstance(to_convert,Intervals):
            return to_convert

        return Intervals(to_convert)


    def add_affiliation(self, nodes, cIDs, times):
        """
        Affiliate node n to community com for period times

        :param nodes: node or list/set of nodes
        :param cIDs: community or list/set of communities. str
        :param times: period as an Interval object, or a pair (start,end) or list of pairs

        """

        times = self._2Intervals(times)
        if isinstance(cIDs, str) or not isinstance(cIDs, Iterable):
            cIDs = set([cIDs])
        if isinstance(nodes, str) or not isinstance(nodes, Iterable):
            nodes=set([nodes])
        else:
            nodes = set(nodes)

        for n in nodes:
            for cID in cIDs:
                self._by_node.setdefault(n, {}).setdefault(cID, Intervals())
                self._by_node[n][cID] = self._by_node[n][cID].union(times)
                self._by_com.setdefault(cID, {}).setdefault(n, Intervals())
                self._by_com[cID][n] = self._by_node[n][cID].union(times)


        self.start = min(self.start, times.start())
        self.end = max(self.end, times.end())

    def add_affiliations_from(self, communities, times):
        """
        Add communities provided as a cluster

        Given a community provided as a dict id:{set of nodes} , add it for the period times (intervals)

        :param communities: dict id:{set of nodes}
        :param times: an Intervals object or a single period as a pair (start, end)
        """

        if not isinstance(times,Intervals):
            times = Intervals(times)
        for id,affils in communities.items():
            for n in affils:
                self.add_affiliation(n, id, times)

    def remove_affiliation(self, n:str, com, times:Intervals):
        """
        Remove affiliations

        remove affiliations of node n from community com between the period times

        :param n: node
        :param com: community
        :param times: Intervals
        """
        (t,e) = times
        n = str(n)
        self._by_node[n][com]._substract_one_period((t, e))
        self._by_com[com][n]._substract_one_period((t, e))

    def affiliations_durations(self, nodes=None, communities=None):
        """
        Durations of affiliations

        Return the duration in each community (for non-zero values) for the provided nodes and the provided communities (default: all)
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

        if len(nodes) == 1 and len(communities) == 1:
            toReturn = list(toReturn.items())[0][1]
        else:
            if len(nodes)==1:
                toReturn = {c:t for (n,c),t in toReturn.items()}
            if len(communities)==1:
                toReturn = {n:t for (n,c),t in toReturn.items()}

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

        Return nodes such as those with the same main community are close to each other.
        By default, use the main community according to internal function nodes_main_com
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

    def to_DynCommunitiesSN(self,slices=None):
        """
            Convert to a snapshot representation.

            :param slices: can be one of

            - None, snapshots are created such as a new snapshot is created at every node/edge change,
            - an integer, snapshots are created using a sliding window
            - a list of periods, represented as pairs (start, end), each period yielding a snapshot

            :return: a dynamic graph represented as snapshots, the weight of nodes/edges correspond to their presence time during the snapshot

        """
        dgSN = tn.DynCommunitiesSN()
        if slices == None:
            raise("lack implementation to find automatically sn periods. Please use argument slices=...")
            times = self.change_times()
            slices = [(times[i], times[i + 1]) for i in range(len(times) - 1)]

        if isinstance(slices, int):
            duration = slices
            slices = []
            start = self.start
            end = start + duration
            while (end <= self.end):
                end = start + duration
                slices.append((start, end))
                start = end
                end = end + duration

        for ts in slices:
            dgSN.set_communities(t=ts[0])

        sorted_times = [x[0] for x in slices]

        for cID, coms in self.communities().items():
            for n,interv in coms.items():
                intersection = interv._discretize(sorted_times)
                for t,presence in intersection.items():
                    if presence > 0:
                        dgSN.add_affiliation(n,cID,t)


        return dgSN

    # def to_DynCommunitiesSN(self,slices=None):
    #     """
    #         Convert to a snapshot representation.
    #
    #         :param slices: can be one of
    #
    #         - None, snapshot_affiliations are created such as a new snapshot is created at every node/edge change,
    #         - an integer, snapshot_affiliations are created using a sliding window
    #         - a list of periods, represented as pairs (start, end), each period yielding a snapshot
    #
    #         :return: a dynamic graph represented as snapshot_affiliations, the weight of nodes/edges correspond to their presence time during the snapshot
    #
    #     """
    #     dgSN = tn.DynCommunitiesSN()
    #     if slices == None:
    #         times = self.change_times()
    #         slices = [(times[i], times[i + 1]) for i in range(len(times) - 1)]
    #
    #     if isinstance(slices, int):
    #         duration = slices
    #         slices = []
    #         start = self.start
    #         end = start + duration
    #         while (end <= self.end):
    #             end = start + duration
    #             slices.append((start, end))
    #             start = end
    #             end = end + duration
    #
    #     for ts in slices:
    #         dgSN.set_communities(t=ts[0])
    #
    #     for cID, coms in self.communities().items():
    #         for n,interv in coms.items():
    #             for ts in slices:
    #                 presence = interv.intersection(Intervals([ts])).duration()
    #                 if presence > 0:
    #                     dgSN.add_affiliation(n,cID,ts[0])
    #
    #
    #     return dgSN