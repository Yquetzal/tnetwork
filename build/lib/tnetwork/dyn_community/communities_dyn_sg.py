from tnetwork.dyn_community.communitiesEventsHandler import *
from tnetwork.utils.intervals import *
import numpy as np
import operator

class DynamicCommunitiesSG:
    def __init__(self):
        self.nodes = {} #type:{str:{int:{intervals}}
        self.communities = {}
        self.events=CommunitiesEvent()


    def addBelonging(self, n, com, t, e=np.inf):
        n = str(n)
        self.nodes.setdefault(n,{}).setdefault(com,intervals()).add_interval((t, e))
        self.communities.setdefault(com, {}).setdefault(n,intervals()).add_interval((t, e))

    def removeBelonging(self,n,com,t,e=np.inf):
        n = str(n)
        self.nodes[n][com].remove_interval((t, e))
        self.communities[com][n].remove_interval((t, e))

    def addEvent(self,comsBefore, comsAfter,tBefore,tAfter,type): #type can be merge, continue, split or unknown
        self.events.add_event(comsBefore, comsAfter, tBefore, tAfter, type)



    def belongingsT(self,nodes=None,communities=None):
        """
        return the duration in each community (for non-zero values) for the provided nodes and the provided communities (default: all)
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
            nBunch=[nodes]
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
        Function that return a node order trying to keep nodes belonging to the same communities close to each other
        :param theDynCom:
        :return:
        """
        node2Com = {}
        for n in self.nodes:
            belongings = self.belongingsT(n)  # for each community, belonging duration
            ordered = sorted(belongings.items(), key=operator.itemgetter(1))
            ordered.reverse()
            node2Com[n] = ordered[0][0]  # assign to each node its main com

        return node2Com

    def nodes_natural_order(self):
        return sorted(self.nodes)

    def nodes_ordered_by_com(self,node2com=None):
        """
        return nodes such as those with the same main community are close to each other. By default, use the main community according to function nodes_main_com
        :param node2Com: a dictionary associating a community to each

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
