import tnetwork as dn
import networkx as nx
import numpy as np
import math
import progressbar
from tnetwork.utils.intervals import Intervals
from tnetwork.DCD.community import _Operation,Community
import time
import sys






class ComScenario():
    """
    This class manages the community evolution scenario

    It implements the benchmark described in XXX

    Behavior to keep in mind:

    1) Any node that does not belong to a community is condered "dead". Note that it can reappear later
    if it belongs to a community again.
    As a consequence, a node alive but not belonging to any community must be represented as a node belonging to a community of size 1

    2)There are not really persistent community, every time a community is modified in any way, a new community is created,
    and it is only because they have the same name (label) that they are considered part of the same dynamic community.

    As a consequence, to kill a dynamic community, one simply needs to stop using its label.

    """

    def __init__(self,  alpha = 0.80, external_density_penalty=0.05, random_noise=0, verbose=False, variant="deterministic"):
        """
        Initialize the community generation class

        When initializing, we can set the parameters of the link generation

        :param alpha: alpha parameter that determines the density of communities decrease with size
        :param external_density_penalty: beta, how smaller the density of outside community is compared to a a community of the same size
        :param random_noise: beta_r, fraction of existing edges that are randomly rewired at each step
        :param verbose: If true, print debugging information
        :param variant: the variant of the generator controls the way edges are generated. Currently, only "deterministic" is fully suported

        """

        ##################### Parameters ##########
        # parameter to define how fast snapshot_affiliations are loosing in density when they grow
        self.random_noise=random_noise

        self.alpha_com_density = alpha

        self._pairsImportance =[] #List of importance for each pair of nodes in the graph

        #dictionary containing the list of all currently active snapshot_affiliations (and operations). {name:object}
        self._currentCommunities = set()  # type:{_AbstractStructure}

        self._currentID=0 #To ensure that all community IDs are different
        self._currentT=0 #keep track of time

        # For optimization, memorize communities and graphs in a local format
        self._dyn_graph_local_edges=dict()
        self._dyn_graph_local_nodes=dict()
        self._dyn_com_local=dict()

        #self._dynCom = dn.DynamicCommunitiesSN() #Class used to memorize the dynamic snapshot_affiliations in the dynamic rerence partition"
        self._dynCom = dn.DynCommunitiesIG()

        self._variant=variant

        self._actions=list() #list of community operations to do
        self._verbose=verbose
        self._externalDensityPenalty=external_density_penalty

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
        ##self.alpha_com_density = 0.75
        return math.ceil((math.pow(nbNodes - 1, self.alpha_com_density) * nbNodes) / 2)

    def _get_current_nodes(self):
        """
        Compute list of nodes CURRENTLY active (gives differnt results for different time)
        :return:
        """
        allNodes=set()
        for com in self._currentCommunities:
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
        self._currentCommunities.remove(operation)

        #for each community modifed by the operation
        for com in operation._afterCommunities:
            self._allSeenCommunities.add(com)

            #add this community to the list of active snapshot_affiliations
            if "|DEATH|" not in com.label():
                self._currentCommunities.add(com)

                ##### Management of the reference partition as an event graph #####
                if len(operation._beforeCommunities)>0:
                    #update the label of community with the event graph now that we know the time of end of operation
                    nx.relabel_nodes(self._dynCom.events, {com.label():(self._currentT, com.label())}, copy=False)
                ###################################################################

    def _generate_current_network(self):
        """
        Return a graph generated according to currently active snapshot_affiliations / operations
        :return:
        """
        #g = nx.Graph()
        currentNodes = self._get_current_nodes()
        #intercomEdges = self._pairsImportance.copy()

        #keep only pairs between current nodes
        #intercomEdges = {k:v for k,v in intercomEdges.items() if len(k & currentNodes)==2}

        to_skip = {}
        #for each community
        chosen_intern_edges = set()
        for c in list(self._currentCommunities):

            chosen_intern_edges.update(c._intern_edges())

            #add the selected edges to the graph
            #g.add_edges_from(chosenEdges)
            #REMOVE intern pairs from possible pairs for inter-com edges
            internPairs = c._intern_pairs()
            to_skip.update(internPairs)


        #Pick edges outside snapshot_affiliations
        #sortedPairs = sorted(intercomEdges.items(), key=operator.itemgetter(1),reverse=True)
        wantedNbInterEdges = self.nb_edges_for_a_community_size(len(self._get_current_nodes())) * self._externalDensityPenalty
        ###wantedNbInterEdges=len(chosen_intern_edges)*self._externalDensityPenalty
        chosen_extern_edges=set()
        i=0
        while len(chosen_extern_edges)<wantedNbInterEdges:
            candidate = self._pairsImportance[i]
            if not candidate in to_skip:
                if len(candidate & currentNodes)==2:
                    chosen_extern_edges.add(candidate)
            i+=1
        #chosenEdges = sortedPairs[:math.floor(wantedNbInterEdges)]
        #chosenEdges = [x[0] for x in chosenEdges]

        chosen_edges = chosen_intern_edges | chosen_extern_edges
        #add the selected edges to the graph
        #g.add_edges_from(chosenEdges)
        return chosen_edges


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



    def _add_action(self, action, t=0, delay=0, triggers=None):
        """
        Generic function to add an action to execute, with temporal parameters. Note the difference between t and delay:
        we can say that we want an event to occur not before a time t, but if the comunities we are "waitfor" are not ready,
        we delay until they are. But when they are, we might want to delay a little before triggering this event.

        :param action: the action to add
        :param t: the time at which we start to consider the activation of this action
        :param delay: the time we should delay after all conditions are fulfilled for activating it
        :param triggers: the ID of the event(s) that should be finished before considering activation
        :return: the ID(s) of snapshot_affiliations created by this action (always a list)
        """
        if (self._verbose):
            print("----request action ", action._action, action.label())
        action.initialise(self)

        if (self._verbose):
            print("----added action ", action._action, action.label())

        self._actions.append({"operation": action, "t": t, "delay": delay, "triggers":triggers})
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
        self._currentCommunities.add(op)

        #delete the snapshot_affiliations involved in the operation from the list of currently existing snapshot_affiliations
        for c in op._beforeCommunities:
            self._currentCommunities.remove(c)


    def _retrieve_last_community_with_name(self, anAction):
        """
        Given the label of a community, return the last community object created under that name.
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
        edges = self._generate_current_network()
        nodes = {list(x)[0] for x in edges} | {list(x)[1] for x in edges}
        # nodes=g.nodes

        if self.random_noise>0:
            nb_edges_original = len(edges)

            edges_to_randomize = int(self.random_noise*nb_edges_original)
            if edges_to_randomize > 0:
                idx = np.random.choice(nb_edges_original, edges_to_randomize)

                #ee = np.array(edges)
                #to_remove_random = set(ee[idx])
                to_remove_random = {list(edges)[i] for i in idx}
                edges = edges - to_remove_random
                #g.remove_edges_from(to_remove_random)
                #nb_nodes =  g.number_of_nodes()
                nb_nodes=len(nodes)
                to_adds_source = np.random.choice(nb_nodes, edges_to_randomize)
                to_adds_dest = np.random.choice(nb_nodes, edges_to_randomize)
                #to_adds_source = np.array(nodes)[to_adds_source]
                #to_adds_dest = np.array(nodes)[to_adds_dest]

                to_adds_source = [list(nodes)[i] for i in to_adds_source]
                to_adds_dest = [list(nodes)[i] for i in to_adds_dest]


                edges = edges | {(to_adds_source[i],to_adds_dest[i]) for i in range(edges_to_randomize) if to_adds_source[i]!= to_adds_dest[i]}
                #g.add_edges_from([(to_adds_source[i],to_adds_dest[i]) for i in range(edges_to_randomize) if to_adds_source[i]!= to_adds_dest[i]])



        # memorize the current step of the graph in the dynamic network
        #self._dynGraph.set_snapshot(self._currentT, g)
        #self._dynGraph.add_interactions_from(list(g.edges()),(self._currentT,self._currentT+1))

        #edges = g.edges()
        for (n1,n2) in edges:
            e = frozenset([n1,n2])
            self._dyn_graph_local_edges.setdefault(e, [])
            if len(self._dyn_graph_local_edges[e])>0 and self._dyn_graph_local_edges[e][-1][-1]==self._currentT:
                self._dyn_graph_local_edges[e][-1]=(self._dyn_graph_local_edges[e][-1][0], self._currentT + 1)
            else:
                self._dyn_graph_local_edges[e].append((self._currentT, self._currentT + 1))

        for n in nodes:
            self._dyn_graph_local_nodes.setdefault(n, [])
            if len(self._dyn_graph_local_nodes[n]) > 0 and self._dyn_graph_local_nodes[n][-1][-1] == self._currentT:
                self._dyn_graph_local_nodes[n][-1] = (self._dyn_graph_local_nodes[n][-1][0], self._currentT + 1)
            else:
                self._dyn_graph_local_nodes[n].append((self._currentT, self._currentT + 1))



        if self._verbose:
            print("snapshot_affiliations end of step: ", self._currentCommunities)

        # Memorize the current partition in the dynamic partition
        for c in self._currentCommunities:
            if type(c) is Community:
                for n in c.nodes():
                    label = c.label()
                    self._dyn_com_local.setdefault(label,{}).setdefault(n,[])
                    if len(self._dyn_com_local[label][n]) > 0 and self._dyn_com_local[label][n][-1][-1] == self._currentT:
                        self._dyn_com_local[label][n][-1] = (self._dyn_com_local[label][n][-1][0], self._currentT + 1)
                    else:
                        self._dyn_com_local[label][n].append((self._currentT, self._currentT + 1))

        self._currentT += 1


    def _local_formats_to_dyn_structures(self):
        to_return_graph = dn.DynGraphIG()
        for n in self._dyn_graph_local_nodes:
            intv = Intervals(self._dyn_graph_local_nodes[n])
            to_return_graph.add_node_presence(n,intv)


        for e in self._dyn_graph_local_edges:
            [n1,n2] = list(e)
            intv = Intervals(self._dyn_graph_local_edges[e])
            to_return_graph._add_interaction_safe(n1,n2,intv)

        for c in self._dyn_com_local:
            for n in self._dyn_com_local[c]:
                self._dyn_com_local[c][n]=Intervals(self._dyn_com_local[c][n])
        to_return_com = dn.DynCommunitiesIG()
        to_return_com._fast_set_affiliations(self._dyn_com_local)
        return to_return_graph,to_return_com

    def run(self):
        """
        Function to call when the scenario has been defined to actually execute it.
        Return a dynamic network and the corresponding dynamic partition

        :return: a couple, first element is the dynamic network, second element is the dynamic partition
        """
        nb_events = len(self._actions)
        bar = progressbar.ProgressBar(max_value=nb_events)
        #While there is an action to do or there is an operation still going on
        while len(self._actions)>0 or len([x for x in self._currentCommunities if type(x) is _Operation])>0:
            if(self._verbose):
                print("TIME : ", self._currentT)
                print("snapshot_affiliations start of step: ", self._currentCommunities)


            #get the list of snapshot_affiliations and events currently active
            readycoms =  self._allSeenCommunities

            for action in self._actions: #for each action (could be optimized but unnecessary on small scenarios

                if action["t"]<=self._currentT: #if static time passed

                    op = action["operation"]

                    affectedComs = set(op._beforeCommunities) #snapshot_affiliations affected by this action
                    lockingComs= set() #IDs of events/coms used as triggers

                    if action["triggers"]!=None: #if there are triggers
                        if isinstance(action["triggers"],Community): #(put in right format)
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
                                sys.stdout.flush()

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
        dyn_graph,dyn_com = self._local_formats_to_dyn_structures()
        time.sleep(0.1)
        bar.update(nb_events)
        return(dyn_graph, dyn_com)

    def INITIALIZE(self, sizes:[int], labels:[str]=None):
        """
        Function to initialize the dynamic networks with communities that already exist at the beginning

        :param sizes: list of the communities sizes (same order as names)
        :param labels: list of the communities labels (if None, unique labels are given automatically)
        """
        if labels==None:
            labels= [None] * len(sizes)
        if len(sizes)!= len(labels):
            raise Exception("nb sizes do not match nb names")

        toReturn=[]
        for i,size in enumerate(sizes):
            label = labels[i]
            newCommunity = Community(self, label)
            newCommunity._add_nodes([self.create_node() for j in range(size)])
            self._currentCommunities.add(newCommunity)
            self._allSeenCommunities.add(newCommunity)
            toReturn.append(newCommunity)

        self._memorize_current_configuration()

        return toReturn



    def BIRTH(self, size:int, label:str=None, **kwargs):
        """
        Creates a new community

        :param size: number of nodes to create
        :param label: label of the community (default will create a random label)
        :return: the community created (community object)
        """
        return self._add_action(_Operation.birth(label, size), **kwargs)[0]

    def DEATH(self, com:Community, **kwargs):
        """
        Kill a community

        :return: empty list
        """
        died = self._add_action(_Operation.death(com), **kwargs)

        return died

    def MERGE(self, toMerge: [Community], merged:str, **kwargs):
        """
        Merge the communities in input into a single community with the name (label) provided in output

        :param toMerge: labels of snapshot_affiliations to merge
        :param merged: label of the merged community (can be same as one of the input or not
        :return: the merged community (community object)
        """
        allNodes = set()
        for com in toMerge:
            allNodes.update(com.nodes())
        return self._add_action(_Operation.migrate(toMerge, [merged], [allNodes]), **kwargs)[0]

    def SPLIT(self, toSplit:Community, newComs:[str], sizes:[int], **kwargs):
        """
        Split a single community into several ones. Note that to control exactly which nodes are moved, one should use migrate instead

        :param toSplit: label of the community to split
        :param newComs: labels to give to the new snapshot_affiliations (list). The label of the community before split can be or not among them
        :param sizes: sizes of the new snapshot_affiliations, in number of nodes. In the same order as newComs.
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

    def THESEUS(self, theComTh: Community, nbNodes=None, wait_step=1, delay=1, **kwargs):
        """
        Create a theseus ship operation.

        :param theComTh: the community to modify
        :param nbNodes: the number of nodes to be replaced
        :param delay: the waiting time before the first change
        :param wait_step: the waiting time between each node replacement
        :return: a tuple of snapshot_affiliations, current ship, new ship
        """

        label = theComTh.label()

        initialNodes = list(theComTh.nodes())

        if nbNodes == None:
            nbNodes = len(initialNodes)

        currentShip = theComTh

        planksInStoreHouse = []
        for i in range(nbNodes):
            wait_this_step =wait_step
            if i==0 and delay>wait_step:
                wait_this_step=delay


            newNode = self.create_node()
            nodeToRemove = initialNodes[i]

            [currentShip] = self.ASSIGN([currentShip], [label], splittingOut=[
                set(currentShip.nodes()) - {nodeToRemove} | set([newNode])],
                                        delay=wait_this_step, **kwargs)

            planksInStoreHouse.append(nodeToRemove)

        [newShip] = self.ASSIGN([], [self._get_new_ID(label)], splittingOut=[planksInStoreHouse], triggers=currentShip)
        return (currentShip,newShip)

    def RESURGENCE(self, theComTh: Community, death_period=20, **kwargs):
        """
        Create a resurgence operation.

        :param theComTh: the community to modify
        :param death_period: time to remain dead
        :return: a tuple of snapshot_affiliations, current ship, new ship
        """

        label = theComTh.label()

        initialNodes = list(theComTh.nodes())

        death = self.DEATH(theComTh,**kwargs)

        [theComTh] = self.ASSIGN([], [label], splittingOut=[initialNodes], triggers=death,delay=death_period)

        return theComTh

    def GROW_ITERATIVE(self, com, nb_nodes2Add, wait_step=1, delay=1, **kwargs):
        """
        Make a community grow node by node

        The community com add nodes2add nodes one by one, with an interval delay between each
        :param com: community to grow
        :param nodes2Add: nb nodes to add
        :param delay: the waiting time before the first change
        :param wait_step: the waiting time between each node addition
        :return:
        """

        for i in range(nb_nodes2Add):
            wait_this_step = wait_step
            if i == 0 and delay > wait_step:
                wait_this_step = delay
            newNode = self.create_node()
            [com] = self.ASSIGN(
                [com],
                [com.label()],
                [com.nodes() | set([newNode])],
                delay=wait_this_step,**kwargs
            )
        return com

    def SHRINK_ITERATIVE(self, com, nb_nodes2remove, wait_step=1, delay=1, **kwargs):
        """
        Make a community shrink node by node

        The community com lose nodes2add nodes one by one, with an interval delay between each
        :param com: community to shrink
        :param nodes2remove: nb nodes to remove
        :param delay: the waiting time before the first change
        :param wait_step: the waiting time between each node removal
        :return:
        """
        currentCom = com

        for i in range(nb_nodes2remove):
            wait_this_step = wait_step
            if i == 0 and delay > wait_step:
                wait_this_step = delay

            currentNbNodes = len(currentCom.nodes())
            nodesToKeep = np.random.choice(list(currentCom.nodes()), currentNbNodes - 1, replace=False)
            [currentCom] = self.ASSIGN([currentCom], [currentCom.label()], [nodesToKeep], delay=wait_this_step, **kwargs)
        return currentCom

    def MIGRATE_ITERATIVE(self, comFrom, comTo, nbNodes, wait_step=1, delay=1, **kwargs):
        """
        Make nodes of a community migrate to another one

        The community comFrom lose nodes2add nodes one by one, that join the community comTo,
        with an interval delay between each migration

        :param comFrom: community to shrink
        :param comTo: community to grow
        :param nbNodes: nb nodes to move
        :param delay: the waiting time before the first change
        :param wait_step: the waiting time between each node change
        :return:
        """
        currentFrom = comFrom
        currentTo = comTo
        for i in range(nbNodes):
            wait_this_step = wait_step
            if i == 0 and delay > wait_step:
                wait_this_step = delay
            migratingNode = np.random.choice(list(currentFrom.nodes()), 1)[0]
            [currentFrom, currentTo] = self.ASSIGN(
                [currentFrom, currentTo],
                [currentFrom.label(), currentTo.label()],
                [currentFrom.nodes() - set([migratingNode]), currentTo.nodes() | set([migratingNode])],
                delay=wait_this_step, **kwargs
            )

    def ASSIGN(self, comsBefore:[Community], comsAfter:[str], splittingOut:[{str}], **kwargs):
        """
        Define a custom event

        Migrate nodes from a set of snapshot_affiliations to another set of snapshot_affiliations. Can be used to move a set of nodes from a community to
        another or any other more complex scenario.

        :param comBefore: Ccommunities in input
        :param comsAfter: label(s) to give to the resulting communities
        :param splittingOut: How to distribute nodes in output. It is a list of same lenght than comsAfter, and each element of the list is a set of names of nodes. Note that if some nodes present in input does not appear in output, they are considered "killed"
        :return: the communities resulting from the operation (list)
        """
        return self._add_action(_Operation.migrate(comsBefore, comsAfter, splittingOut), **kwargs)


    def CONTINUE(self, com, **kwargs):
        """
        Keep a community unchanged

        By using parameters delay and/or triggers, CONTINUE makes the community com_before to stay unchanged for some time.

        :param com: the community to keep unchanged
        :return: the same community
        """
        return self.ASSIGN([com], [com.label()], [com.nodes()], **kwargs)

    def __repr__(self):
        coms = "current_com: " + str(self._currentCommunities)
        events = "events: " + str(self._actions)
        return coms + "\n" + events


    def __str__(self):
        return self.__repr__()

def generate_toy_random_network(**kwargs):
    """
    Generate a small, toy dynamic graph

    Generate a toy dynamic graph with evolving communities, following scenario described in XXX
    Optional parameters are the same as those passed to the ComScenario class to generate custom scenarios

    :return: pair, (dynamic graph, dynamic reference partition) (as snapshots)
    """
    my_scenario = ComScenario(**kwargs)

    # Initialization with 4 communities of different sizes
    [A, B, C, T] = my_scenario.INITIALIZE([5, 8, 20, 8],
                                                                ["A", "B", "C", "T"])
    # Create a theseus ship after 20 steps
    (T,U)=my_scenario.THESEUS(T, delay=20)

    # Merge two of the original communities after 30 steps
    B = my_scenario.MERGE([A, B], B.label(), delay=30)

    # Split a community of size 20 in 2 communities of size 15 and 5
    (C, C1) = my_scenario.SPLIT(C, ["C", "C1"], [15, 5], delay=75)

    # Split again the largest one, 40 steps after the end of the first split
    (C1, C2) = my_scenario.SPLIT(C, ["C", "C2"], [10, 5], delay=40)

    # Merge the smallest community created by the split, and the one created by the first merge
    my_scenario.MERGE([C2, B], B.label(), delay=20)

    # Make a new community appear with 5 nodes, disappear and reappear twice, grow by 5 nodes and disappear
    R = my_scenario.BIRTH(5, t=25, label="R")
    R = my_scenario.RESURGENCE(R, delay=10)
    R = my_scenario.RESURGENCE(R, delay=10)
    R = my_scenario.RESURGENCE(R, delay=10)

    # Make the resurgent community grow by 5 nodes 4 timesteps after being ready
    R = my_scenario.GROW_ITERATIVE(R, 5, delay=4)

    # Kill the community grown above, 10 steps after the end of the addition of the last node
    my_scenario.DEATH(R, delay=10)

    (dyn_graph, dyn_com) = my_scenario.run()
    dyn_graph_sn = dyn_graph.to_DynGraphSN(slices=1)
    GT_as_sn = dyn_com.to_DynCommunitiesSN(slices=1)
    return dyn_graph_sn, GT_as_sn


def generate_simple_random_graph(nb_com =10, min_size=5, max_size=15, operations=20, mu=0, mu_noise=0.01):
    """
    Generate a simple random dynamic graph with community structure

    This is the generator described in XXX. It generates a graph with dynamic community structure which is a combination
    of successive merge and splits.

    :param nb_com: number of initial communities
    :param min_size: size below which communities cannot be split
    :param max_size: size above which community split
    :param operations: number of operations (merge/split) to execute (involves random communities)
    :param mu: parameter to set how well defined is the community structure (0=>perfect community structure) more precisely, it defines: alpha=1-mu, beta=mu
    :param mu_noise: set the mu_r, i.e., fraction of edges randomly rewired at each snapshot
    :return: pair (graph, communities)
    """
    print("generating graph with nb_com = ",nb_com)
    prog_scenario = ComScenario(verbose=False, alpha=1-mu, external_density_penalty=mu,random_noise=mu_noise)

    #prog_scenario = tn.ComScenario(verbose=False, alpha=0.9, external_density_penalty=mu,random_noise=mu_noise)
    all_communities = set(prog_scenario.INITIALIZE(np.random.randint(min_size,max_size,size=nb_com)))

    for i in range(operations):
        [com1] = np.random.choice(list(all_communities),1,replace=False)
        all_communities.remove(com1)

        if len(com1.nodes())<max_size and len(all_communities)>0: #merge
            [com2] = np.random.choice(list(all_communities),1,replace=False)
            largest_com = max([com1,com2],key=lambda x: len(x.nodes()))
            merged = prog_scenario.MERGE([com1,com2], largest_com.label(), delay=20)
            all_communities.remove(com2)
            all_communities.add(merged)
        else: #split
            smallest_size = int(len(com1.nodes())/3)
            (com2,com3) = prog_scenario.SPLIT(com1, [prog_scenario._get_new_ID("CUSTOM"), com1.label()], [smallest_size, len(com1.nodes()) - smallest_size], delay=20)
            all_communities|= set([com2,com3])

    (dyn_graph,dyn_com) = prog_scenario.run()


    return(dyn_graph,dyn_com)