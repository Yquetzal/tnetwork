from sortedcontainers import SortedDict
from tnetwork.dyn_community.communitiesEventsHandler import CommunitiesEvent
from tnetwork.utils.bidict import bidict
from collections import Iterable
import networkx as nx
import tnetwork as tn
from tnetwork.utils.community_utils import nodesets2affiliations

class DynamicCommunitiesSN:
    def __init__(self):
        """
        Initialize a dynamic community object, corresponding to a snapshot-based dynamic network
        """
        self._communities=SortedDict() #A sorted dict, key:time, value: bidict {frozenset of nodes}:id
        self.events=CommunitiesEvent()
        self._automaticID=1

    def add_empy_sn(self, t):
        """
        Add a snapshot with no snapshots at time t
        :param t: time step
        """
        if not t in self._communities:
            self._communities[t] = bidict()

    def belongings_by_node(self,t):
        """
        return the belonging of a node a time

        :param n: the node
        :param t: the time
        :return: a community ID
        """
        if not t in self.communities():
            return None
        return nodesets2affiliations(self.communities()[t])

    def add_belonging(self, n, t, cID): #be careful, if the n is a single node in the shape of a set, incorrect behavior
        """
        Add belonging for the provided node(s) to the provided communitie(s) at the provided time(s)
        :param n: accept lists of nodes or single node
        :param t:
        :param cID: accept lists of coms or single
        :return:
        """

        if isinstance(t,str) or not isinstance(t,Iterable):
            t = set([t])
        if isinstance(cID,str) or not isinstance(cID,Iterable):
            cID = set([cID])
        if isinstance(n,str) or not isinstance(n,Iterable):
            n=frozenset([n])
        else:
            n = frozenset(n)



        for ts in t:
            if not ts in self._communities:
                self._communities[ts]=bidict()
            coms = self._communities[ts]
            for cs in cID:
                if not cs in coms.inv:
                    coms.inv[cs]=frozenset()
                coms.inv[cs]=coms.inv[cs].union(n)

    def add_belongins_from(self, clusters, t):
        """
        Given a cluster provided as a dict or bidict {frozenset of nodes}:id , add it to time t
        :param clusters: dict or bidict{frozenset of nodes}:id
        """

        self._communities[t]=bidict(clusters)

    def add_community(self, t, com, id=None):
        """
        add the community com at time t (with a random id if not provided)
        :param t: time
        :param com: a community provided as a set/list of nodes
        :param id: optional id, otherwise, new unique one
        :return:
        """

        com = frozenset(com)
        if id==None:
            id=str(self._automaticID)
            self._automaticID+=1
        self.add_belonging(com, t, id)

    def com_ID(self, t, com):
        """
        Get the id of a community at a time
        :param t: time
        :param com: set of nodes
        :return: the id
        """

        return self._communities[t][com]

    def communities(self,t=None):
        """
        return all snapshots present at a given time
        :param t: time
        :return: a bidict {frozenset of nodes}:id
        """

        if t==None:
            return self._communities
        return self._communities[t]

    def _compute_fraction_identity(self, com1, com2):
        """
        compute a fraction of identity between two snapshots
        :param com1: a com
        :param com2: another com
        """

        common = len(com1 & com2)
        return (common/len(com1)*(common/len(com2)))

    def create_standard_event_graph(self, keepingPreviousEvents=False,threshold=0,score=_compute_fraction_identity):
        """
        From a set of static snapshots, do a standard matching process such as all snapshots in consecutive steps with at least a node in common are linked by an event, and compute a similarity score


        :param keepingPreviousEvents: if true, if events were already present, we keep them and compute their score
        :param threshold: a minimal value of score under which a link is not created. Default: 0
        :param score: a function describing how to compute the score. Takes 2 snapshots as input and return the score.
        """
        if not keepingPreviousEvents:
            self.events=CommunitiesEvent()
        else:
            communities = self.communities()
            for ((t1,com1),(t2,com2)) in self.events.edges():
                fraction = self._compute_fraction_identity(communities[t1].inv[com1], communities[t2].inv[com2])
                self.events[(t1, com1)][(t2, com2)]["fraction"]=fraction

        #compute events between consecutive snapshots
        communities = self.communities()
        for i in range(1,len(communities),1):
            (t1,comsBefore) = communities.peekitem(i-1)
            (t2,comsPresent) = communities.peekitem(i)
            for comNodes,comID in comsBefore.items():
                for com2Nodes,com2ID in comsPresent.items():
                    fraction = self._compute_fraction_identity(comNodes, com2Nodes)
                    if fraction>threshold:
                        self.events.add_event((t1, comID), (t2, com2ID), t1, t2, "unknown", fraction=fraction)


    def _change_com_id(self,t,oldID,newID):
        """
        Modify the ID of a community, in the community list and the event graph
        :param t:
        :param nodes:
        :param newID:
        :return:
        """
        nodesOfCom = self._communities[t].inv[oldID]
        self._communities[t][nodesOfCom] = newID
        nx.relabel_nodes(self.events, {(t,oldID): (t, newID)}, copy=False)

    def relabel_coms_from_continue_events(self, typedEvents=True):
        """
        If an event graph is present, rename the snapshots such as two snapshots that are linked by an event labeled "continue" will have the same ID.
        If events are not labels, is possible to label them automatically into merge, split and continue using the in/out degrees of nodes in the event graph
        :param typedEvents: True if continue labels have already been set.
        """
        if typedEvents:
            changedIDs = {} #
            for (u,v,d) in sorted(list(self.events.edges(data=True)), key=lambda x: x[2]["time"][0]):
                if d["type"]=="continue":

                    #update com ID in self
                    timeEnd = d["time"][1]
                    idComToChange = v[1]
                    idComToKeep = u[1]
                    if u in changedIDs:
                        idComToKeep = changedIDs[u]
                    changedIDs[v]=idComToKeep

                    nodesOfCom = self._communities[timeEnd].inv[idComToChange]
                    self._communities[timeEnd][nodesOfCom]=idComToKeep

                    #update com ID in event graph
                    nx.relabel_nodes(self.events, {(timeEnd, idComToChange): (timeEnd, idComToKeep)}, copy=False)

        if not typedEvents:
            #if events are not typed, we infer what we can, i.e one input and one input is a continue, otherwise we change label of edges accordingly
            for t in self._communities:
                for (c,cID) in self._communities[t].items():
                    node_current=(t,cID)
                    succ = self.events.out_degree([node_current])

                    if isinstance(node_current[1], frozenset):
                        com_predecessors = node_current[1] #node_current[1] contains the list of similar predecessors, instead of a single ID
                        if len(com_predecessors)==1:
                            main_pred = list(com_predecessors)[0]
                            self.events[main_pred][node_current]["type"] = "continue"
                            # self._change_com_id(node_current[0],node_current[1] , main_pred[1])
                            # node_current = (node_current[0], main_pred[1])
                            # cID = main_pred[1]
                        else:
                            main_pred_match = -1
                            main_pred = None
                            for merged in com_predecessors:
                                 self.events[merged][node_current]["type"] = "merge"
                                 #print(self.events[merged][node_current]["fraction"])
                                 if self.events[merged][node_current]["fraction"]>main_pred_match:
                                    main_pred_match = self.events[merged][node_current]["fraction"]
                                    main_pred = merged
                        self._change_com_id(node_current[0], node_current[1], main_pred[1])
                        node_current = (node_current[0], main_pred[1])
                        cID = main_pred[1]


                    #If there is at least one similar community in the next step
                    if len(succ)>0 and succ[node_current]>=1:
                        main_succ_match = -1
                        main_succ = None

                        #Find the most similar community in next step (main_succ)
                        for splitted in self.events.successors(node_current):
                            self.events[node_current][splitted]["type"] = "split"
                            if self.events[node_current][splitted]["fraction"]>main_succ_match:
                                main_succ_match = self.events[node_current][splitted]["fraction"]
                                main_succ = splitted


                        #Register to the main successor that this community wants to give it its ID.
                        candidates_names = []
                        if isinstance(main_succ[1],frozenset):
                            candidates_names+=list(main_succ[1])
                        candidates_names.append(node_current)
                        candidates_names = frozenset(candidates_names)

                        self._change_com_id(main_succ[0], main_succ[1], candidates_names)






    def to_SGcommunities(self, convertTimeToInteger=False):
        """
        Convert to SG snapshots
        :param convertTimeToInteger:
        :return:
        """
        dynComTN= tn.DynamicCommunitiesSG()
        for i in range(len(self._communities)):
            if convertTimeToInteger:
                t=i
                tNext=i+1
            else:
                t = self._communities.peekitem(i)[0]
                if i<len(self._communities)-1:
                    tNext=self._communities.peekitem(i + 1)[0]
                else:
                    tNext = self._communities.peekitem("END")[1]

            for (c,cID) in self._communities.peekitem(i)[1].items(): #for each community for this timestep
                for n in c:#get the nodes, not the
                    dynComTN.add_belonging(n, cID, t, tNext)


        #convert also events
        for (u,v,d) in self.events.edges(data=True):
            if d["type"]!="continue": #if snapshots have different IDs
                dynComTN.addEvent(u[1],v[1],d["time"][0],d["time"][1],d["type"])
        return dynComTN
