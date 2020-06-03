import sortedcontainers
from tnetwork.dyn_community.communitiesEventsHandler import CommunitiesEvent
from collections.abc import Iterable
import networkx as nx
import tnetwork as tn
#from tnetwork.utils import bidict #### do not use bidict to avoid having to use frozenset
from tnetwork.utils.community_utils import nodesets2affiliations
from tnetwork.utils.community_utils import jaccard
from tnetwork.utils.intervals import Intervals
from tnetwork.dyn_community.communities_dyn import DynCommunities
import numpy as np
from sklearn.decomposition import PCA

class DynCommunitiesSN(DynCommunities):
    """
    Dynamic communities as sequences of snapshots

    Communities are represented as a SortedDict, key:time, value: dict id:{set of nodes}
    """
    def __init__(self,snapshots=None):
        """
        Initialization

        Initialize a dynamic community object, corresponding to a snapshot-based dynamic network

        :param snapshots: list of snapshots timestep to create, initially empty
        """


        self.snapshots=sortedcontainers.SortedDict() #sorteddict t:{id:{set of nodes}}
        self.events=CommunitiesEvent()
        self._automaticID=1
        if snapshots!= None:
            for t in snapshots:
                self.add_empty_snapshot(t)

    def add_empty_snapshot(self,t):
        self.snapshots[t]={}

    def remove_communities(self,communities, times):
        for com in communities:
            for time in times:
                if com in self.snapshots[time]:
                    del self.snapshots[time][com]

    def slice(self,start,end):
        """
        Keep only the selected period

        :param start:
        :param end:
        """

        to_return = tn.DynCommunitiesSN()
        interv = tn.Intervals((start,end))
        for t in list(self.snapshots.keys()):
            if t in interv:
                to_return.set_communities(self.snapshots[t], t)
        return to_return


    def snapshot_communities(self, t=None):
        """
        Affiliations by communities

        If t is given, return communities at this t as a bidict id:{set of nodes}
        else, return a sorted dict, key:time, value: dict id:{set of nodes}

        :param t: time
        :return: a dict id:{set of nodes}
        """

        if t==None:
            return self.snapshots
        return self.snapshots[t]

    def communities_sn_by_sn(self):
        """
        Communities snapshots by snapshots

        Return for each community its nodes snaphsot by snapshot
        :return: a dict c:{SortedDict{t:{set of nodes}}
        """
        to_return = {}
        for time in self.snapshots:
            for cID, nodes in self.snapshots[time].items():
                to_return.setdefault(cID,sortedcontainers.SortedDict())
                to_return[cID][time]=nodes
        return to_return

    def communities(self, t=None):
        """
        Communities

        If t is given, return communities at this t as a dict, key=node, value=set of communities
        else, return a dict, key:node, value: dict community:list of times

        :param t: time
        :return: dictionary, key=node, value=dict community:list of times or if t is not None: dict community:list
        """
        if t == None:
            to_return = {}

            for time in self.snapshots:
                for cID,nodes in self.snapshots[time].items():
                    for n in nodes:
                        to_return.setdefault(cID,{})
                        to_return[cID].setdefault(n,[])
                        to_return[cID][n].append(time)
            return to_return

        return self.snapshots[t]

    def affiliations(self, t=None):
        """
        Affiliations by nodes

        If t is given, return affiliation at this t as a dict, key=node, value=set of communities
        else, return a dict, key:node, value: dict community:list of times

        :param t: time
        :return: dictionary, key=node, value=dict community:list of times or if t is not None: dict community:list
        """
        if t == None:
            to_return = {}

            for time in self.snapshots:
                for cID,nodes in self.snapshots[time].items():
                    for n in nodes:
                        to_return.setdefault(n,{})
                        to_return[n].setdefault(cID,[])
                        to_return[n][cID].append(time)
            return to_return


        return nodesets2affiliations(self.snapshot_communities()[t])


    def affiliations_durations(self, nodes=None, communities=None):
        """
        Duration of affiliations

        Return the duration in each community (for non-zero values) for the provided nodes and the provided communities (default: all)
        return set of triplets (n,c,duration), or set of pairs of one if the parameters has a single value, or a single value if single node and single com

        :param nodes: node(s) for which we want durations. single node or set of nodes
        :param communities: communities(s) for which we want durations. single community or set of communities
        :return: set of triplets (n,c,duration), or set of pairs of one if the parameters has a single value, or a single value if single node and single com

        """

        toReturn={}
        aff = self.affiliations()
        coms = self.communities()
        if nodes==None:
            nodes=aff.keys()

        if communities==None:
            communities=coms.keys()

        if isinstance(nodes,str):
            nodes=[nodes]
        if isinstance(communities,str):
            communities=[communities]
        nodes = set(nodes)
        communities = set(communities)


        for n in nodes:
            for c in communities & set(aff[n].keys()):
                toReturn[(n,c)]=len(aff[n][c])

        if len(nodes) == 1 and len(communities) == 1:
            toReturn = list(toReturn.items())[0][1]
        else:
            if len(nodes)==1:
                toReturn = {c:t for (n,c),t in toReturn.items()}
            if len(communities)==1:
                toReturn = {n:t for (n,c),t in toReturn.items()}

        return toReturn

    def snapshots_timesteps(self):
        """
        Return the list of time steps

        :return: list of time steps
        """
        return list(self.snapshots.keys())

    def snapshot_affiliations(self, t=None):
        """
        Affiliations by snapshots

        If t is given, return affiliation at this t as a dict, key=node, value=set of communities
        else, return a sorted dict, key:time, value: dict node:communities

        :param t: time
        :return: sorted dict, key:time, value: dict node:communities or key=node, value=set of communities
        """
        if t==None:
            return sortedcontainers.SortedDict({k:nodesets2affiliations(v) for k,v in self.snapshot_communities().items()})

        if not t in self.snapshot_communities():
            return None

        return nodesets2affiliations(self.snapshot_communities()[t])

    def add_affiliation(self, nodes, cIDs, times):
        """
        Affiliate node(s) to community(ies) at time(s)

        Add belonging for the provided node(s) to the provided communitie(s) at the provided time(s).
        (all nodes, at all times, in all communities)
        If communities do not exist, they are created.

        :param nodes: accept set/list of nodes or single node
        :param times: accept list of times or single time
        :param cIDs: accept lists of coms or single com
        :return:
        """

        if isinstance(times, str) or not isinstance(times, Iterable):
            times = set([times])
        if isinstance(cIDs, str) or not isinstance(cIDs, Iterable):
            cIDs = set([cIDs])
        if isinstance(nodes, str) or not isinstance(nodes, Iterable):
            nodes=frozenset([nodes])
        else:
            nodes = frozenset(nodes)



        for ts in times:
            if not ts in self.snapshots:
                self.snapshots[ts]=dict()
            coms = self.snapshots[ts]
            for cs in cIDs:
                cs= str(cs)
                if not cs in coms:
                    coms[cs]=set()
                coms[cs]=coms[cs].union(nodes)

    def set_communities(self, t, communities=None):
        """
        Affiliate nodes given a dictionary representation

        Given a clustering provided as a dict  id:{set of nodes} , set this clustering at the
        provided time (replace any existing clustering at that time)

        :param t: a time instant
        :param communities: communitie as  dict  id:{set of nodes}
        """

        if communities==None:
            self.snapshots[t] = dict()
        else:
            self.snapshots[t]=communities

    def add_community(self, t, nodes, id=None):
        """
        Add a community at a time

        Create a community at time t with the provided nodes and id  ( random id if not provided)

        :param t: time
        :param nodes: a community provided as a set/list of nodes
        :param id: optional id, otherwise, new unique one
        """

        nodes = set(nodes)
        if id==None:
            id=str(self._automaticID)
            self._automaticID+=1

        self.add_affiliation(nodes, id, t)
        return id

    def _com_ID(self, t, nodes):
        """
        Get the id of a community at a time
        
        given a set of nodes composing a community, return the id of this community. If there is not one and only 
        one community containing those nodes, raise an exception

        :param t: time
        :param nodes: set of nodes
        :return: ID of the community. If several matching, raise exceptions
        """
        to_return = []
        for id,com_nodes in self.snapshots[t].items():
            if com_nodes==nodes:
                to_return.append(id)

        if len(to_return)==0:
            raise Exception("no community found")
        if len(to_return)>1:
            raise Exception("several matching communities found")
        return to_return[0]



    def _compute_fraction_identity(self, com1, com2):
        """
        compute a fraction of identity between two communities

        :param com1: a com
        :param com2: another com
        """

        common = len(com1 & com2)
        return (common/len(com1)*(common/len(com2)))

    def create_standard_event_graph(self, keepingPreviousEvents=False,threshold=0.3,score=None):
        """
        From a set of static communities, do a standard matching process such as all communities in consecutive steps with at least a node in common are linked by an event, and compute a similarity score

        :param keepingPreviousEvents: if true, if events were already present, we keep them and compute their score
        :param threshold: a minimal value of score under which a link is not created. Default: 0
        :param score: a function describing how to compute the score. Takes 2 communities as input and return the score.
        """
        if score==None:
            score = jaccard
        if not keepingPreviousEvents:
            self.events=CommunitiesEvent()
        else:
            communities = self.snapshot_communities()
            for ((t1,com1),(t2,com2)) in self.events.edges():
                fraction = score(communities[t1][com1], communities[t2][com2])
                self.events[(t1, com1)][(t2, com2)]["fraction"]=fraction

        #compute events between consecutive communities
        communities = self.snapshot_communities()
        for i in range(1,len(communities),1):
            (t1,comsBefore) = communities.peekitem(i-1)
            (t2,comsPresent) = communities.peekitem(i)
            for comID,comNodes in comsBefore.items():
                for com2ID,com2Nodes in comsPresent.items():
                    fraction = score(comNodes, com2Nodes)
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

        nodesOfCom = self.snapshots[t][oldID]

        del self.snapshots[t][oldID]
        self.snapshots[t][newID]=nodesOfCom
        if (t,oldID) in self.events.nodes:
            nx.relabel_nodes(self.events, {(t,oldID): (t, newID)}, copy=False)


    def _relabel_communities_to_avoid_conflict_between_steps(self):
        ts = list(self.snapshot_communities().keys())
        for t in ts:
            ids = list(self.snapshots[t].keys())
            for id in ids:
                self._change_com_id(t,id,str(t)+"_"+str(id))

    def _relabel_coms_from_continue_events(self, typedEvents=True,rename=True):
        """

        If an event graph is present, rename the communities such as two communities that are linked by an event labeled "continue" will have the same ID.
        If events are not labeled, is possible to label them automatically into merge, split and continue using the in/out degrees of nodes in the event graph

        Be careful that if your communities in different snapshots already have similar names, it can add confusion
        :param typedEvents: True if continue labels have already been set.
        :param rename: True if all communities are renamed. This is useful if, before calling this function, two communities in different steps could have the same name, and we do not want to keep this information
        """

        if rename:
            self._relabel_communities_to_avoid_conflict_between_steps()
        if typedEvents:
            changedIDs = {}
            for (u,v,d) in sorted(list(self.events.edges(data=True)), key=lambda x: x[2]["time"][0]):
                if d["type"]=="continue":

                    #update com ID in self
                    timeEnd = d["time"][1]
                    idComToChange = v[1]
                    idComToKeep = u[1]
                    if u in changedIDs:
                        idComToKeep = changedIDs[u]
                    changedIDs[v]=idComToKeep

                    #print(timeEnd,idComToChange,idComToKeep)
                    self._change_com_id(timeEnd,idComToChange,idComToKeep)

        if not typedEvents:
            #if events are not typed, we infer what we can, i.e one input and one output is a continue, otherwise we change label of edges accordingly
            for t in self.snapshots:
                coms = list(self.snapshots[t].items())
                for (cID,nodes) in coms:
                    node_current=(t,cID)

                    succ = self.events.out_degree([node_current])

                    if isinstance(node_current[1], frozenset): # If there are communities in the previous steps that consider this one similar
                        com_predecessors = node_current[1] #node_current[1] contains the list of similar predecessors, instead of a single ID
                        if len(com_predecessors)==1:
                            main_pred = list(com_predecessors)[0]
                            self.events[main_pred][node_current]["type"] = "continue"

                        else:
                            main_pred_match = -1
                            main_pred = None
                            for merged in com_predecessors:
                                 self.events[merged][node_current]["type"] = "merge"
                                 if self.events[merged][node_current]["fraction"]>main_pred_match:
                                    main_pred_match = self.events[merged][node_current]["fraction"]
                                    main_pred = merged

                        self._change_com_id(node_current[0], node_current[1], main_pred[1])
                        node_current = (node_current[0], main_pred[1])


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




    def _to_DynCommunitiesIG_fast(self):
        """
        Work only in the standard represntation: all sn have duration 1, no missing snapshot
        :return:
        """
        dyn_com_local = {}
        for t,part in self.snapshot_communities().items():
            for id,nodes in part.items():
                for n in nodes:
                    name = id
                    dyn_com_local.setdefault(name,{}).setdefault(n,[])
                    if len(dyn_com_local[name][n]) > 0 and dyn_com_local[name][n][-1][-1] == t:
                        dyn_com_local[name][n][-1] = (dyn_com_local[name][n][-1][0], t + 1)
                    else:
                        dyn_com_local[name][n].append((t, t + 1))

        to_return_com = tn.DynCommunitiesIG()

        for c in dyn_com_local:
            for n in dyn_com_local[c]:
                dyn_com_local[c][n]=Intervals(dyn_com_local[c][n])

        to_return_com._fast_set_affiliations(dyn_com_local)
        return to_return_com

    def to_DynCommunitiesIG(self, sn_duration, convertTimeToInteger=False):
        """
        Convert to SG communities

        :param sn_duration: time of a snapshot, or None for automatic: each snapshot last until start of the next
        :param convertTimeToInteger: if True, communities IDs will be forgottent and replaced by consecutive integers
        :return: DynamicCommunitiesIG
        """

        dynComTN= tn.DynCommunitiesIG()
        for i in range(len(self.snapshots)):
            if convertTimeToInteger:
                t=i
                tNext=i+1
            else:
                current_t = self.snapshots.peekitem(i)[0]

                if sn_duration != None:
                    tNext = current_t + sn_duration

                else:
                    if i < len(self.snapshots) - 1:
                        tNext = self.snapshots.peekitem(i + 1)[0]
                    else:
                        # computing the min duration to choose as duration of the last period
                        dates = list(self.snapshots.keys())
                        minDuration = min([dates[i + 1] - dates[i] for i in range(len(dates) - 1)])
                        tNext = current_t + minDuration


            for (cID,nodes) in self.snapshots.peekitem(i)[1].items(): #for each community for this timestep
                dynComTN.add_affiliation(nodes,cID,Intervals((current_t,tNext)))


        #convert also events
        for (u,v,d) in self.events.edges(data=True):
            if d["type"]!="continue": #if communities have different IDs
                dynComTN.events.add_event(u[1],v[1],d["time"][0],d["time"][1],d["type"])
        return dynComTN


    def resample(self, bin_size=None, t_start=None, t_end=None):
        """
        reseampling a dynamic community at higher frequency

        :param bin_size: desired size of bins, in the internal time unit
        :param t_start: time step to start the binning (default: first)
        :param t_end: time step (not included) to stop the binning (default: last)
        :return: a DynCommunitiesSN object
        """



        if t_start==None:
            t_start = self.snapshots()[0]
        if t_end==None:
            t_end=self.snapshots()[-1]

        if bin_size == None:
            bin_size=t_end-t_start


        bins = []
        for t in range(t_start, t_end, bin_size):
            bins.append((t, t + bin_size))

        toReturn = DynCommunitiesSN()
        for (binStart,binEnd) in bins:
            key = self.snapshots().bisect_left(binStart)
            toReturn.add_snapshot(binStart,self.snapshots[key])
        return toReturn




    def communities_duration(self):
        """
        Duration of each community

        :return:  {id:duration}
        """
        to_return = {}
        all_coms = self.communities_sn_by_sn()
        for com_ID, evol in all_coms.items():
            to_return[com_ID]=len(evol)
        return to_return

    def automatic_node_order(self):
        """
        Return an order of nodes optimized for longitudinal plotting

        Note: code is not optimized, could be improved!
        :return: list of nodes names
        """
        affil_durations = self.affiliations_durations()
        nodes_indices = sorted(list(self.affiliations().keys()))
        coms_indices = sorted(list(self.communities().keys()))
        features = np.full((len(nodes_indices),len(coms_indices)),0)
        for (n,c),duration in affil_durations.items():
                node_position = nodes_indices.index(n)
                com_position = coms_indices.index(c)
                features[node_position,com_position]=duration

        model = PCA(n_components=1)#,dissimilarity="precomputed")
        positions = model.fit_transform(features)
        return [x for _,x in sorted(zip(positions,nodes_indices))]
