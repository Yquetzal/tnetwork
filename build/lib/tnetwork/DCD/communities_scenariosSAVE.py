import tnetwork as dn
import networkx as nx
import numpy as np
import math
import progressbar
from tnetwork.utils.intervals import Intervals
from .community import _Operation,Community








class ComScenario():
    """
    This class manages the community evolution scenario

    Behavior to keep in mind:
    1) Any node that does not belong to a community is condered "dead". Note that it can reappear later
    if it belongs to a community again.
    As a consequence, a node alive but not belonging to any community must be represented as a node belonging to a community of size 1

    2)There are not really persistent community, every time a community is modified in any way, a new community is created,
    and it is only because they have the same name (label) that they are considered part of the same dynamic community
    As a consequence, to kill a dynamic community, one simply needs to stop using its name.

    """

    def __init__(self, variant="deterministic",  alpha = 0.80, externalDensityPenalty=0.05, verbose=False):
        """

        :param variant: the variant of the generator controls the way edges are generated. Currently, only "deterministic" is fully suported
        :param alpha: alpha parameter that determines how
        :param externalDensityPenalty: how smaller the density of outside comuninty is compared to a a community of the same size
        :param verbose: If true, print debugging information

        """

        ##################### Parameters ##########
        # parameter to define how fast snapshot_affiliations are loosing in density when they grow
        self.alpha_com_density = 0.75

        self.alpha_com_density = alpha #alpha parameter is defined as a global variable, see beginning of the file

        self._pairsImportance =[] #List of importance for each pair of nodes in the graph

        #dictionary containing the list of all currently active snapshot_affiliations (and operations). {name:object}
        self._currentCommunities = dict()  # type:{str:_AbstractStructure}

        self._currentID=0 #To ensure that all community IDs are different
        self._currentT=0 #keep track of time

        #self._dynGraph=dn.DynGraphSN() # Class used to memorize the dynamic graph generated
        ##self._dynGraph=dn.DynGraphSG()
        self._dyn_graph_edges=dict()
        self._dyn_graph_nodes=dict()

        #self._dynCom = dn.DynamicCommunitiesSN() #Class used to memorize the dynamic snapshot_affiliations in the dynamic rerence partition"
        self._dynCom = dn.DynCommunitiesIG()

        self._variant=variant

        self._actions=list() #list of community operations to do
        self._verbose=verbose
        self._externalDensityPenalty=externalDensityPenalty

        self._allSeenNodes = set() #list of nodes that appear at least once (to manage pairsimportance)
        self._allSeenCommunities = set() #to manage triggers

    ############### Function to determine density (could be replaced by custom one) ######
    def nb_edges_for_a_community_size(self, comSize):
        """
        Given the number of nodes in a community, return the desired number of edges

        :param comSize: number of nodes
        :return: desired number of edges
        """
        nbNodes = comSize
        if nbNodes <= 1:
            return 0
        self.alpha_com_density = 0.75
        return math.ceil((math.pow(nbNodes - 1, self.alpha_com_density) * nbNodes) / 2)

    def _get_current_nodes(self):
        """
        Compute list of nodes CURRENTLY active (gives differnt results for different time)
        :return:
        """
        allNodes=set()
        for name,com in self._currentCommunities.items():
            allNodes.update(set(com.nodes()))

        return allNodes






    def _get_new_ID(self, prefix=""):
        """
        Fonction to generate a unique ID.
        :param prefix: optional prefix, for instance to distinguish nodes from snapshot_affiliations
        :return:
        """
        toR = self._currentID
        self._currentID += 1
        return prefix + "_t_" + str(self._currentT).zfill(4) + "_" + str(toR).zfill(4)


    def _terminate_operation(self, operation):
        """
        Terminate an ongoing operation
        :param operation: operation to terminate
        :return:
        """
        if(self._verbose):
            print("---------END OF OPERATION: ", operation.label())

        #remove the operation from the list of current snapshot_affiliations
        #--- this has importnat implications: one does not need to manage manually the death of snapshot_affiliations,
        #--- as any community that has a
        del self._currentCommunities[operation.label()]

        #for each community modifed by the operation
        for com in operation._afterCommunities:
            self._allSeenCommunities.add(com)

            #add this community to the list of active snapshot_affiliations
            if "|DEATH|" not in com.label():
                self._currentCommunities[com.label()] = com

                ##### Management of the reference partition as an event graph #####
                if len(operation._beforeCommunities)>0:
                    #update the name of community with the event graph now that we know the time of end of operation
                    nx.relabel_nodes(self._dynCom.events, {com.label():(self._currentT, com.label())}, copy=False)
                ###################################################################

    def _generate_current_network(self):
        """
        Return a graph generated according to currently active snapshot_affiliations / operations
        :return:
        """
        g = nx.Graph()
        currentNodes = self._get_current_nodes()
        #intercomEdges = self._pairsImportance.copy()

        #keep only pairs between current nodes
        #intercomEdges = {k:v for k,v in intercomEdges.items() if len(k & currentNodes)==2}

        to_skip = {}
        #for each community
        for c in list(self._currentCommunities.values()):

            chosenEdges = c._intern_edges(variant=self._variant)
            #add the selected edges to the graph
            g.add_edges_from(chosenEdges)
            #REMOVE intern pairs from possible pairs for inter-com edges
            internPairs = c._intern_pairs()
            to_skip.update(internPairs)


        #Pick edges outside snapshot_affiliations
        #sortedPairs = sorted(intercomEdges.items(), key=operator.itemgetter(1),reverse=True)
        wantedNbInterEdges = self.nb_edges_for_a_community_size(len(self._get_current_nodes())) * self._externalDensityPenalty
        chosenEdges=[]
        i=0
        while len(chosenEdges)<wantedNbInterEdges:
            candidate = self._pairsImportance[i]
            if not candidate in to_skip:
                if len(candidate & currentNodes)==2:
                    chosenEdges.append(candidate)
            i+=1
        #chosenEdges = sortedPairs[:math.floor(wantedNbInterEdges)]
        #chosenEdges = [x[0] for x in chosenEdges]


        #add the selected edges to the graph
        g.add_edges_from(chosenEdges)
        return g


    def create_node(self, id=None):
        """
        This is the only function allowed to create nodes. Most nodes are created automatically by a community birth,
        but in some cases, it could be useful to create it manually and manage its integration manually, for instance
        in the scneario of a new node appearing and being immediately integrated into an existing community, it does
        not make sense to first make it appear in a community of its own which is then merged

        :param id: a name to recognize that node (a unique ID will be created by adding a postfix)
        :return: unique ID of the node. Nodes do not have existance (instanciation) appart from this name
        """

        if id==None:
            id=self._get_new_ID("n")

        for n in self._allSeenNodes:
            if len(self._pairsImportance)==0:
                self._pairsImportance.append(frozenset((n, id)))
            else:
                self._pairsImportance.insert(np.random.randint(len(self._pairsImportance)),frozenset((n, id)))

        self._allSeenNodes.add(id)

        if(self._verbose):
            print("----created node ",id)
        return id



    def _add_action(self, action, t=0, wait=0, waitFor=None):
        """
        Generic function to add an action to execute, with temporal parameters. Note the difference between t and delay:
        we can say that we want an event to occur not before a time t, but if the comunities we are "waitfor" are not ready,
        we delay until they are. But when they are, we might want to delay a little before triggering this event.

        :param action: the action to add
        :param t: the time at which we start to consider the activation of this action
        :param wait: the time we should delay after all conditions are fulfilled for activating it
        :param waitFor: the ID of the event(s) that should be finished before considering activation
        :return: the ID(s) of snapshot_affiliations created by this action (always a list)
        """
        if (self._verbose):
            print("----request action ", action._action, action.label())
        action.initialise(self)

        if (self._verbose):
            print("----added action ", action._action, action.label())

        self._actions.append({"operation": action, "t": t, "delay": wait, "triggers":waitFor})
        return action._afterCommunities


    def _activate_action(self, op):
        """
        Function called when it is time to execute an action (conditions fulfilled).

        :param op: opeartion to activate
        :return:
        """
        if (self._verbose):
            print("---------ACTIVATING: ", op.label())

        #add the operation to the list of currently existing snapshot_affiliations
        self._currentCommunities[op.label()] = op

        #delete the snapshot_affiliations involved in the operation from the list of currently existing snapshot_affiliations
        for c in op._beforeCommunities:
            del self._currentCommunities[c.label()]


    def _retrieve_last_community_with_name(self, anAction):
        """
        Given the name of a community, return the last community object created under that name.
        :param anAction:
        :return:
        """
        for action in reversed(self._actions):
            if anAction in action["operation"]._afterNames:
                return action["operation"]._afterCommunities[action["operation"]._afterNames.index(anAction)]
        raise Exception("OPERATION MISSING to lead to com: "+anAction)






    def _memorize_current_configuration(self):
        """
        function to memorize in the dynamic graphs and dynamic snapshot_affiliations the current configuration
        :return:
        """
        g = self._generate_current_network()

        # memorize the current step of the graph in the dynamic network
        #self._dynGraph.set_snapshot(self._currentT, g)
        #self._dynGraph.add_interactions_from(list(g.edges()),(self._currentT,self._currentT+1))
        for (n1,n2) in g.edges():
            e = frozenset([n1,n2])
            self._dyn_graph_edges.setdefault(e, [])
            if len(self._dyn_graph_edges[e])>0 and self._dyn_graph_edges[e][-1][-1]==self._currentT:
                self._dyn_graph_edges[e][-1]=(self._dyn_graph_edges[e][-1][0], self._currentT + 1)
            else:
                self._dyn_graph_edges[e].append((self._currentT, self._currentT + 1))

        for n in g.nodes():
            self._dyn_graph_nodes.setdefault(n, [])
            if len(self._dyn_graph_nodes[n]) > 0 and self._dyn_graph_nodes[n][-1][-1] == self._currentT:
                self._dyn_graph_nodes[n][-1] = (self._dyn_graph_nodes[n][-1][0], self._currentT + 1)
            else:
                self._dyn_graph_nodes[n].append((self._currentT, self._currentT + 1))



        if self._verbose:
            print("snapshot_affiliations end of step: ", self._currentCommunities.keys())

        # Memorize the current partition in the dynamic partition
        #self._dynCom.set_snapshot(self._currentT)
        for c in self._currentCommunities.values():
            if type(c) is Community:
                if (self._verbose):
                    print("list of current com: adding com ", self._currentT, " ", c.label())
                #self._dynCom.add_community(self._currentT, c.nodes(), c.name())
                self._dynCom.add_affiliations_from({c.label():set(c.nodes())}, (self._currentT, self._currentT + 1))
        self._currentT += 1


    def local_format_to_dyn_graph(self):
        to_return = dn.DynGraphIG()
        print(self._dyn_graph_nodes)
        for n in self._dyn_graph_nodes:
            intv = Intervals(self._dyn_graph_nodes[n])
            print(n,intv)
            to_return.add_node_presence(n,intv)
        print(nx.get_node_attributes(to_return._graph,"t"))


        for e in self._dyn_graph_edges:
            [n1,n2] = list(e)
            intv = Intervals(self._dyn_graph_edges[e])
            to_return._add_interaction_safe(n1,n2,intv)
        print(to_return.node_presence())
        return to_return

    def run(self):
        """
        Function to call when the scenario has been defined to actually execute it.
        Return a dynamic network and the corresponding dynamic partition

        :return: a couple, first element is the dynamic network, second element is the dynamic partition
        """
        nb_events = len(self._actions)
        bar = progressbar.ProgressBar(max_value=nb_events)
        #While there is an action to do or there is an operation still going on
        while len(self._actions)>0 or len([x for x in self._currentCommunities.values() if type(x) is _Operation])>0:
            if(self._verbose):
                print("TIME : ", self._currentT)
                print("snapshot_affiliations start of step: ", self._currentCommunities.keys())


            #get the list of snapshot_affiliations and events currently active
            readycoms =  self._allSeenCommunities

            for action in self._actions: #for each action (could be optimized but unnecessary on small scenarios

                if action["t"]<=self._currentT: #if static time passed

                    op = action["operation"]

                    affectedComs = set(op._beforeCommunities) #snapshot_affiliations affected by this action
                    lockingComs= set() #IDs of events/coms used as triggers

                    if action["triggers"]!=None: #if there are triggers
                        if type(action["triggers"]) is Community: #(put in right format)
                            action["triggers"] = {action["triggers"]}
                        lockingComs.update(action["triggers"])

                    if len( affectedComs - readycoms)==0: #if all necessay coms are ready
                        if len (lockingComs - readycoms)==0: #and triggers are ready
                            if action["delay"]!=0: #if user wants to delay, delay
                                action["t"]= self._currentT + action["delay"]
                                action["delay"]=0
                            else:
                                self._activate_action(op)
                                self._actions.remove(action)
                                bar.update(nb_events-len(self._actions))


                                ### Section only to manage the representation of the reference partition as an event graph ####
                                #action activated, store the current event in the eventGraph with placeholders for resulting coms, since we do not know when
                                #the operation will be ended
                                for before in op._beforeCommunities:
                                    for after in op._afterNames:
                                        if "|DEATH|" not in after:
                                            lastCommunityPresence = self._currentT - 1
                                            self._dynCom.events.add_event((lastCommunityPresence, before.label()), (after), lastCommunityPresence, lastCommunityPresence, type=op._action, fraction=-1)

            self._memorize_current_configuration()

        ######Managing the event graph reference partition ####
        #self._dynCom.create_standard_event_graph(keepingPreviousEvents=True)
        dyn_graph = self.local_format_to_dyn_graph()
        bar.update(nb_events)
        return(dyn_graph, self._dynCom)

    def INITIALIZE(self,sizes:[int],names:[str]=None):
        """
        Function to initialize the dynamic networks with snapshot_affiliations that already exist at the beginning

        :param sizes: list of the snapshot_affiliations sizes (same order as names)
        :param names: list of the snapshot_affiliations names (if None, unique names are given automatically)
        """
        if names==None:
            names=[None]*len(sizes)
        if len(sizes)!= len(names):
            raise Exception("nb sizes do not match nb names")

        toReturn=[]
        for i,size in enumerate(sizes):
            name = names[i]
            newCommunity = Community(self, name)
            newCommunity._add_nodes([self.create_node() for j in range(size)])
            self._currentCommunities[newCommunity.name()]=newCommunity
            self._allSeenCommunities.add(newCommunity)
            toReturn.append(newCommunity)

        self._memorize_current_configuration()

        return toReturn



    def BIRTH(self,size:int, name:str=None,**kwargs):
        """
        Creates a new community

        :param size: number of nodes to create
        :param name: name of the community (default will create a random name)
        :return: the community created (community object)
        """
        return self._add_action(_Operation.birth(name, size), **kwargs)[0]

    def DEATH(self, com:Community, **kwargs):
        """
        Kill a community

        :param name: name of the community to kill
        :return: empty list
        """
        died = self._add_action(_Operation.death(com), **kwargs)

        return died

    def MERGE(self, toMerge: [Community], merged:str, **kwargs):
        """
        Merge the snapshot_affiliations in input into a single community with the name (label) provided in output

        :param toMerge: names of snapshot_affiliations to merge
        :param merged: name of the merged community (can be same as one of the input or not
        :return: the merged community (community object)
        """
        allNodes = set()
        for com in toMerge:
            allNodes.update(com.nodes())
        return self._add_action(_Operation.migrate(toMerge, [merged], [allNodes]), **kwargs)[0]

    def SPLIT(self, toSplit:Community, newComs:[str], sizes:[int], **kwargs):
        """
        Split a single community into several ones. Note that to control exactly which nodes are moved, one should use migrate instead

        :param toSplit: name of the community to split
        :param newComs: names to give to the new snapshot_affiliations (list). The name of the community before split can be or not
        among them
        :param sizes: sizes of the new snapshot_affiliations, in number of nodes. In the same order as names.
        :return: a list of snapshot_affiliations resulting from the split.
        """
        if sum(sizes)!=len(toSplit.nodes()):
            raise Exception("The number of nodes in resulting snapshot_affiliations does not match the number of nodes in the initial one")
            return
        splittingOut= []
        listNodes = toSplit.nodes()

        for i, nbNodes in enumerate(sizes):
            chosenNodes = set(np.random.choice(list(listNodes), nbNodes, replace=False))
            splittingOut.append(chosenNodes)
            listNodes = listNodes - chosenNodes

        return self._add_action(_Operation.migrate([toSplit], newComs, splittingOut), **kwargs)

    def THESEUS(self, theComTh: Community, nbNodes=None, wait=1):
        """
        Create a theseus ship operation.

        :param theComTh: the community to modify
        :param nbNodes: the number of nodes to be replaced
        :param wait: the waiting time between each node replacement
        :return: a tuple of snapshot_affiliations, current ship, new ship
        """

        name = theComTh.name()

        initialNodes = list(theComTh.nodes())

        if nbNodes == None:
            nbNodes = len(initialNodes)

        currentShip = theComTh

        planksInStoreHouse = []
        for i in range(nbNodes):
            newNode = self.create_node()
            nodeToRemove = initialNodes[i]

            [currentShip] = self.ASSIGN([currentShip], [name], splittingOut=[
                set(currentShip.nodes()) - {nodeToRemove} | set([newNode])],
                                        wait=wait)

            planksInStoreHouse.append(nodeToRemove)

        [newShip] = self.ASSIGN([], [self._get_new_ID(name)], splittingOut=[planksInStoreHouse], waitFor=currentShip)
        return (currentShip,newShip)

    def GROW_ITERATIVE(self, com, nodes2Add, wait=1):

        for i in range(nodes2Add):
            newNode = self.create_node()
            print(com)
            [com] = self.ASSIGN(
                [com],
                [com.label()],
                [com.nodes() | set([newNode])],
                wait=wait
            )
        return com

    def ASSIGN(self, comsBefore:[Community], comsAfter:[str], splittingOut:[{str}], **kwargs):
        """
        Migrate nodes from a set of snapshot_affiliations to another set of snapshot_affiliations. Can be used to move a set of nodes from a community to
        another or any other more complex scenario.

        :param comBefore: Ccommunities in input
        :param comsAfter: name(s) to give to the resulting snapshot_affiliations
        :param splittingOut: How to distribute nodes in output. It is a list of same lenght than comsAfter, and each element of the
        list is a set of names of nodes. Note that if some nodes present in input does not appear in output, they are considered "killed"
        :return: the snapshot_affiliations resulting from the operation (list of snapshot_affiliations objects)
        """
        return self._add_action(_Operation.migrate(comsBefore, comsAfter, splittingOut), **kwargs)


    def __repr__(self):
        coms = "current_com: " + str(self._currentCommunities)
        events = "events: " + str(self._actions)
        return coms + "\n" + events


    def __str__(self):
        return self.__repr__()

def migrate_iterative(comFrom, comTo, nbNodes, wait=1):
    comScen = comFrom._comScenar
    currentFrom = comFrom
    currentTo = comTo
    for i in range(nbNodes):
        migratingNode = np.random.choice(list(currentFrom.getNodes()),1)[0]
        [currentFrom,currentTo] = comScen.migrate(
            [currentFrom,currentTo],
            [currentFrom.getName(), currentTo.label()],
            [currentFrom.getNodes() - set([migratingNode]), currentTo.nodes() | set([migratingNode])],
            wait=wait
        )




def shrinkIterative(com, nbNodes2Remove, waitInitial=0,waitStep=1):
    comScen = com._comScenar
    currentCom = com

    for i in range(nbNodes2Remove):
        waitToConsider = waitStep
        if i==0:
            waitToConsider = waitInitial

        currentNbNodes = len(currentCom.getNodes())
        nodesToKeep = np.random.choice(list(currentCom.getNodes()),currentNbNodes-1,replace=False)
        [currentCom] = comScen.migrate([currentCom], [currentCom.getName()], [nodesToKeep], wait=waitToConsider)
    return currentCom