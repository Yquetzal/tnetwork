import tnetwork as dn
import networkx as nx
import numpy as np
import random
import operator
import math

##################### Parameters ##########
#parameter to define how fast communities are loosing in density when they grow
alpha_comDensity = 0.75

############### Function to determine density (could be replaced by custom one) ######
def computeNbEdgesForACommunitySize(comSize):
    """
    Given the number of nodes in a community, return the desired number of edges
    :param comSize: number of nodes
    :return: desired number of edges
    """
    nbNodes = comSize
    if nbNodes<=1:
        return 0
    alpha = 0.75
    return math.ceil((math.pow(nbNodes - 1, alpha) * nbNodes) / 2)





class abstractStructure():
    """
    this class can be instanciated as a community or an ongoing operation (class operation)
    Be careful, structures have NAMES and IDS.
    Name is a "label" that is used to decide which community is "the same" as another one, in term of identity (search "ship of theseus paradox" if unclear)
    ID is a unique identifier created automatically after each modification. The "same" community before and after an event has different IDs.
    An ID corresponds to a particular "state" of a community (note that a community keeps the same ID as long as it is not modified)
    """

    def getInternPairsAffinity(self):
        """
        Return all pairs of nodes inside the structure as a dictionary, key: frozenset of two nodes (extremities). value: Latent affinity of the pair
        :return:
        :rtype: {frozenset((str,str)):float}
        """
        pass

    def getInternEdges(self,variant="deterministic"):
        """
        Return edges present inside the structure. If the structure is an ongoing operation, also increment in the ongoing process by adding/removing an edge,
        i.e. the next call to this function will give a different result.
        :param variant: used to chose how edges are drawn. Currently, only "deterministic" is fully supported, (see article)
        :return: [frozenset((str,str))]
        """
        pass

    def getID(self):
        """
        Get the unique ID of this structure
        :rtype: str
        :return: unique ID
        """
        pass

    #Get the name of the structure
    def getName(self):
        """
        Get the name (label) of this structure
        :return: name
        :rtype: str
        """
        pass

    def memorizeAllInternalPairs(self):
        temp = set()
        for n in self._nodes:
            for n2 in self._nodes:
                if n != n2:
                    temp.add(frozenset((n, n2)))
        self._internPairs = {k: self._comScenar._pairsImportance[k] for k in temp}


class community(abstractStructure):

    def __init__(self,comScenario,name=None):
        """
        Initialize a community
        :param comScenario: current Scenario class this community will belong to.
        :param name: the name of the community. If None, the ID is used as name
        """

        #generate a unique ID
        id = comScenario._get_new_ID(prefix="COM")

        self._id = id
        self._name=name
        self._comScenar = comScenario

        if self._name==None:
            self._name=self._id

        self._nodes = set() #type: {str}

        #For optimization purpose, the internPairs are recomputed only when needed, memorized in this variable
        self._internPairs = None #type: {frozenset((str,str)):float}


    def _addNode(self, n):
        """
        add a node to the community
        :param n: str
        """
        self._nodes.add(n)
        self._internPairs=None #for optimization

    def addNodes(self, nodes):
        """
        :param nodes: {str}
        """
        for n in nodes:
             self._addNode(n)


    def getNodes(self):
        return self._nodes


    def getInternPairsAffinity(self):
        """
        optimized to compute anew only in case of change
        :return:
        """
        if self._internPairs==None:
            self.memorizeAllInternalPairs()
        return self._internPairs

    def getNbInternEdges(self):
        """
        return the number of edges expected in this community
        :return:
        """
        if len(self._nodes) == 1:
            return 0

        nbNodes = len(self._nodes)

        return computeNbEdgesForACommunitySize(nbNodes)

    def getID(self):
        return self._id

    def getName(self):
        return self._name

    def getInternEdges(self, variant="deterministic"):
        """
        Return edges that we consider should exist in this community.
        In the default behavior ("deterministic"), return a fix number of edges, and pick that number at the top of the
        list of node pairs sorted by affinity score
        :param variant: only "deterministic" (default parameter) is fully supported and tested
        :return: list of edges
        :rtype: [frozenset((str,str))]
        """
        sortedPairs = sorted(self.getInternPairsAffinity().items(), key=operator.itemgetter(1), reverse=True)
        if (variant == "deterministic" or len(sortedPairs) == 0):
            chosenEdges = sortedPairs[:math.ceil(self.getNbInternEdges())]

        # or random variant
        if (variant == "random"):
            chosenEdges = random.sample(sortedPairs, int(self.getNbInternEdges()))

        chosenEdges = [x[0] for x in chosenEdges]
        return chosenEdges

    def __repr__(self):
        return self.getName()


    def __str__(self):
        return self.getName()

class operation(abstractStructure):
    """
    This class corresponds to an ongoing operation between snapshots.
    When the operation is finished, it disappears and is replaced by a community object (or nothing if death)
    """

    def __init__(self, action, beforeComs=[], afterNames=[], parameters=None):
        """

        :param action: The type of action, as a string. One of {birth, death, migrate}
        :param beforeComs: the snapshots modified by the event.
        :param afterNames: the name(s) of the snapshots resulting of the event. A unique ID will be created
        :param parameters: a dict(), necessary for migration.
        it can contains 3 parameters: sizesIn, sizesOut,splittingOut
        splittingOut: type:[[str]] fully controlled: list of list, each lower level list corresponds to an output community
        and contains the list of the nodes to have in it. Each node in each of the input community MUST be affected to an output community
        sizesIn: type:[[int]] if only some of the input nodes should move
        splitting:{{n1,n2,...n5},{n6,...,n10},...,{}} , splitSize:[n/3,n/3,n/3]
        """
        self._action=action
        self._beforeCommunities = beforeComs
        self._afterNames = afterNames
        self._comScenar = None
        self._parameters = parameters

        self._afterCommunities=None #type:[community]  communities created with the names given in output


        self._inProgress = [] #list of ordered modifications to do to reach the final community

        self._currentEdges = set() #set of edges currently in the community

        self._internPairs = None #dictionary of intern pairs, will be computed later. Stored for efficiency
        self._nodes = [] #we will memorize the nodes to compute the list of internal pairs of nodes

    #TODO comment properly all function for creation
    @classmethod
    def death(cls, name:str):
        return cls(action="death",afterNames=["|DEATH|"], beforeComs=[name])

    @classmethod
    def birth(cls, name:str, size):
        if name==None:
            afterName = []
        else:
            afterName = [name]
        return cls(action="birth", beforeComs=[], afterNames=afterName, parameters={"size": size})

    @classmethod
    def migrate(cls,beforeIDs,afterNames,splittingOut):
        return cls(action="migrate",beforeComs=beforeIDs,afterNames=afterNames,parameters={"splittingOut":splittingOut})

    def initialise(self,comScen):
        """
        This function is called by the ongoing scenario as soon as it is added.
        It initializes everyhting that should happen (list of modifications to reach objective state)
        but do not actually do it
        :param comScen: the ongoing scenario
        """

        self._comScenar = comScen

        #List communities object corresponding to the names and IDs provided
        self._afterCommunities=[]

        #Create new clusters with zero nodes with appropriate names
        for comName in self._afterNames:
            self._afterCommunities.append(community(comScen, name=comName))


        for com in self._beforeCommunities:
            self._nodes += com.nodes()

        if self._action== "birth":
            self._birth()

        if self._action== "death":
            self._death()

        if self._action== "migrate":
            self._migrate()

        if self._action not in ["birth", "death", "migrate"]:
            raise Exception("UNKNOWN operation: " + self._action)

        self._computeEdgeModificationsToDo()

        self.memorizeAllInternalPairs() #at this point, all nodes involved by the operation are known, we compute and memorize internal edges



    def _computeEdgeModificationsToDo(self):
        """
        This function compute the list of modifications that should be done (progressive change until objective state is reached
        :return:
        """

        currentEdges = set()
        edgesAfter = set()


        for c in self._beforeCommunities:
            currentEdges.update(c._intern_edges())

        for c in self._afterCommunities:
            edgesAfter.update(c._intern_edges())

        toRemove = set(currentEdges) - set(edgesAfter)
        toAdd = set(edgesAfter) - set(currentEdges)

        self._currentEdges = currentEdges
        self._inProgress = self.randomizeActions(toRemove, toAdd)


    def _birth(self):
        """
        This function handle a birth event
        :return:
        """

        #If no community is given, create a community with automatic name
        if len(self._afterCommunities)==0:
            self._afterCommunities.append(community(self._comScenar))
            self._afterNames=[self._afterCommunities[0].name()]

        #If we do not specify the nodes that should be added to this community, create nodes
        if not "nodes" in self._parameters:
            self._parameters["nodes"]=set()
            for i in range(self._parameters["size"]):
                self._parameters["nodes"].add(self._comScenar.create_node())

        self._afterCommunities[0]._add_nodes(self._parameters["nodes"])
        self._nodes += self._parameters["nodes"]

    def _death(self):
        """
        the community is removed automatically because self.before is removed and nothing is added to replace.
        nodes must not be killed now because this code is called during scenario definition.
        """
        pass

    def _migrate(self):
        """
        This function handle all types of migrations, including from all nodes to the same community (merge) or from a single community
        to several (split)
        :return:
        """

        #if there is no parameter, the migration is obvious from the context, i.e. several communities in input, a single one in output
        #so let's define sizesIn accordingly


        #Case where the migration is done by giving the exact list of which node should migrate in each community
        for i in range(len(self._parameters["splittingOut"])):
            self._afterCommunities[i]._add_nodes(self._parameters["splittingOut"][i])

        for com in self._afterCommunities:
            if len(com.nodes())==0:
                print(self._parameters)
                print(self._afterCommunities)


    def randomizeActions(self,notKept,added):
        """
        Function that shuffles edges addition and removal.
        :param notKept: edges to remove
        :param added: edges to keep
        :return: list of edges to modify, as a couple, first element being type of operation (+/-), second being the edge
        :rtype: [(str,frozenset(str,str)]
        """
        toReturn = list()
        for e in notKept:
            toReturn.append(("-",e))

        for e in added:
            toReturn.append(("+",e))

        random.shuffle(toReturn)
        return toReturn



    def getInternEdges(self,variant="ignored"):
        """
             Return edges present inside the structure. If the structure is an ongoing operation, also increment in the ongoing process by adding/removing an edge,
             i.e. the next call to this function will give a different result.
             :param variant: used to chose how edges are drawn. Currently, only "deterministic" is fully supported, (see article)
             :return: [frozenset((str,str))]
             """

        if len(self._inProgress)!=0: #If there are still modification to do, do one
            modif = self._inProgress.pop()
            if modif[0]=="-":
                self._currentEdges.remove(modif[1])
            if modif[0]=="+":
                self._currentEdges.add(modif[1])

        if len(self._inProgress)==0: #if no other modification to do, inform the scenerio class that this operation terminates
            self._comScenar._terminate_operation(self)
        return self._currentEdges

    def getInternPairsAffinity(self):
        return self._internPairs

    def getID(self):
        return str(self._beforeCommunities) + "=>" + str(self._afterNames)

    def getName(self):
        return str(self._beforeCommunities) + "=>" + str(self._afterNames)

    def getNodes(self):
        return self._nodes

    def __repr__(self):
        return self.getName()


    def __str__(self):
        return self.getName()


class comScenario():
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

    def __init__(self, variant="deterministic", verbose=False, alpha = 0.80, externalDensityPenalty=0.05):
        """

        :param variant: the variant of the generator controls the way edges are generated. Currently, only "deterministic" is fully suported
        :param verbose: If true, print debugging elements
        :param externalDensityPenalty: how smaller the density of outside comuninty is compared to a a community of the same size
        """

        alpha_comDensity = alpha #alpha parameter is defined as a global variable, see beginning of the file

        self._pairsImportance =[] #List of importance for each pair of nodes in the graph

        #dictionary containing the list of all currently active communities (and operations). {name:object}
        self._currentCommunities = dict()  # type:{str:abstractStructure}

        self._currentID=0 #To ensure that all community IDs are different
        self._currentT=0 #keep track of time

        self._dynGraph=dn.DynGraphSN() # Class used to memorize the dynamic graph generated
        self._dynCom = dn.dynamicCommunitiesSN() #Class used to memorize the dynamic communities in the dynamic rerence partition"

        self._variant=variant

        self._actions=list() #list of community operations to do
        self._verbose=verbose
        self._externalDensityPenalty=externalDensityPenalty

        self._allSeenNodes = set() #list of nodes that appear at least once (to manage pairsimportance)
        self._allSeenCommunities = set() #to manage triggers



    def _getCurrentNodes(self):
        """
        Compute list of nodes CURRENTLY active (gives differnt results for different time)
        :return:
        """
        allNodes=set()
        for name,com in self._currentCommunities.items():
            allNodes.update(set(com.nodes()))

        return allNodes






    def _getNewID(self, prefix=""):
        """
        Fonction to generate a unique ID.
        :param prefix: optional prefix, for instance to distinguish nodes from snapshots
        :return:
        """
        toR = self._currentID
        self._currentID += 1
        return prefix + "_t_" + str(self._currentT).zfill(4) + "_" + str(toR).zfill(4)


    def _terminateOperation(self, operation):
        """
        Terminate an ongoing operation
        :param operation: operation to terminate
        :return:
        """
        if(self._verbose):
            print("---------END OF OPERATION: ", operation.name())

        #remove the operation from the list of current communities
        #--- this has importnat implications: one does not need to manage manually the death of communities,
        #--- as any community that has a
        del self._currentCommunities[operation.name()]

        #for each community modifed by the operation
        for com in operation._afterCommunities:
            self._allSeenCommunities.add(com)

            #add this community to the list of active communities
            if "|DEATH|" not in com.name():
                self._currentCommunities[com.name()] = com

                ##### Management of the reference partition as an event graph #####
                if len(operation._beforeCommunities)>0:
                    #update the name of community with the event graph now that we know the time of end of operation
                    nx.relabel_nodes(self._dynCom.events, {com.name():(self._currentT, com.name())}, copy=False)
                ###################################################################

    def _generateCurrentNetwork(self):
        """
        Return a graph generated according to currently active snapshots / operations
        :return:
        """
        g = nx.Graph()
        currentNodes = self._getCurrentNodes()
        intercomEdges = self._pairsImportance.copy()

        #TODO What ?
        intercomEdges = {k:v for k,v in intercomEdges.items() if len(k & currentNodes)==2}

        #for each community
        for c in list(self._currentCommunities.values()):

            chosenEdges = c._intern_edges(variant=self._variant)
            #add the selected edges to the graph
            g.add_edges_from(chosenEdges)

            #REMOVE intern pairs from possible pairs for inter-com edges
            internPairs = c._intern_pairs()
            for e in internPairs:
                del intercomEdges[e]

        #Pick edges outside communities
        sortedPairs = sorted(intercomEdges.items(), key=operator.itemgetter(1),reverse=True)
        wantedNbInterEdges = computeNbEdgesForACommunitySize(len(self._getCurrentNodes()))*self._externalDensityPenalty

        chosenEdges = sortedPairs[:math.floor(wantedNbInterEdges)]
        chosenEdges = [x[0] for x in chosenEdges]


        #add the selected edges to the graph
        g.add_edges_from(chosenEdges)

        return g


    def createNode(self, id=None):
        """
        This is the only function allowed to create nodes. Most nodes are created automatically by a community birth,
        but in some cases, it could be useful to create it manually and manage its integration manually, for instance
        in the scneario of a new node appearing and being immediately integrated into an existing community, it does
        not make sense to first make it appear in a community of its own which is then merged
        :param id: a name to recognize that node (a unique ID will be created by adding a postfix)
        :return: unique ID of the node. Nodes do not have existance (instanciation) appart from this name
        """

        if id==None:
            id=self._getNewID("n")

        for n in self._allSeenNodes:
            self._pairsImportance[frozenset((n, id))]=np.random.random()
        self._allSeenNodes.add(id)

        if(self._verbose):
            print("----created node ",id)
        return id



    def _addAction(self, action, t=0, wait=0, waitFor=None):
        """
        Generic function to add an action to execute, with temporal parameters. Note the difference between t and wait:
        we can say that we want an event to occur not before a time t, but if the comunities we are "waitfor" are not ready,
        we wait until they are. But when they are, we might want to wait a little before triggering this event
        :param action: the action to add
        :param t: the time at which we start to consider the activation of this action
        :param wait: the time we should wait after all conditions are fulfilled for activating it
        :param waitFor: the ID of the event(s) that should be finished before considering activation
        :return: the ID(s) of snapshots created by this action (always a list)
        """
        if (self._verbose):
            print("----request action ", action._action, action.name())
        action.initialise(self)

        if (self._verbose):
            print("----added action ", action._action, action.name())

        self._actions.append({"operation": action, "t": t, "wait": wait, "waitFor":waitFor})
        return action._afterCommunities


    def BIRTH(self,size:int, name:str=None,**kwargs):
        """
        Creates a new community
        :param size: number of nodes to create
        :param name: name of the community (default will create a random name)
        :return: the community created (community object)
        """
        return self._addAction(operation.birth(name,size),**kwargs)[0]

    def DEATH(self,com:community,**kwargs):
        """
        kill a community
        :param name: name of the community to kill
        :return: empty list
        """
        died = self._addAction(operation.death(com), **kwargs)

        return died

    def MERGE(self,toMerge: [community], merged:str,**kwargs):
        """
        Merge the snapshots in input into a single community with the name (label) provided in output
        :param toMerge: names of snapshots to merge
        :param merged: name of the merged community (can be same as one of the input or not
        :return:
        """
        allNodes = set()
        for com in toMerge:
            allNodes.update(com.nodes())
        return self._addAction(operation.migrate(toMerge,[merged],[allNodes]),**kwargs)[0]

    def SPLIT(self,toSplit:community, newComs:[str], sizes:[int], **kwargs):
        """
        Split a single community into several ones. Note that to control exactly which nodes are moved, one should use migrate instead
        :param toSplit: name of the community to split
        :param newComs: names to give to the new snapshots (list). The name of the community before split can be or not
        among them
        :param sizes: sizes of the new snapshots, in number of nodes. In the same order as names.
        :return:
        """
        splittingOut= []
        listNodes = toSplit.getNodes()

        for i, nbNodes in enumerate(sizes):
            chosenNodes = set(np.random.choice(list(listNodes), nbNodes, replace=False))
            splittingOut.append(chosenNodes)
            listNodes = listNodes - chosenNodes

        return self._addAction(operation.migrate([toSplit],newComs,splittingOut),**kwargs)

    def THESEUS(self,theComTh: community, nbNodes=None, wait=1):
        name = theComTh.getName()

        initialNodes = list(theComTh.getNodes())

        if nbNodes == None:
            nbNodes = len(initialNodes)

        currentShip = theComTh

        planksInStoreHouse = []
        for i in range(nbNodes):
            newNode = self.createNode()
            nodeToRemove = initialNodes[i]

            [currentShip] = self.ASSIGN([currentShip], [name], splittingOut=[
                set(currentShip.getNodes()) - {nodeToRemove} | set([newNode])],
                                            wait=wait)

            planksInStoreHouse.append(nodeToRemove)

        [newShip] = self.ASSIGN([], [self._getNewID(name)], splittingOut=[planksInStoreHouse], waitFor=currentShip)
        return [currentShip,newShip]

    def ASSIGN(self,comsBefore:[community], comsAfter:[str], splittingOut:[{str}], **kwargs):
        """
        Migrate nodes from a set of snapshots to another set of snapshots. Can be used to move a set of nodes from a community to
        another or any other more complex scenario.
        :param comBefore: name(s) of the snapshots in input
        :param comsAfter: name(s) to give to the resulting snapshots
        :param splittingOut: How to distribute nodes in output. It is a list of same lenght than comsAfter, and each element of the
        list is a set of names of nodes. Note that if some nodes present in input does not appear in output, they are considered "killed"
        :return:
        """
        return self._addAction(operation.migrate(comsBefore,comsAfter,splittingOut),**kwargs)

    def _activateAction(self, op):
        """
        Function called when it is time to execute an action (conditions fulfilled.
        :param op: opeartion to activate
        :return:
        """
        if (self._verbose):
            print("---------ACTIVATING: ", op.name())

        #add the operation to the list of currently existing communities
        self._currentCommunities[op.name()] = op

        #delete the snapshots involved in the operation from the list of currently existing snapshots
        for c in op._beforeCommunities:
            del self._currentCommunities[c.name()]


    def _retrieveLastCommunityWithName(self, anAction):
        """
        Given the name of a community, return the last community object created under that name.
        :param anAction:
        :return:
        """
        for action in reversed(self._actions):
            if anAction in action["operation"]._afterNames:
                return action["operation"]._afterCommunities[action["operation"]._afterNames.index(anAction)]
        raise Exception("OPERATION MISSING to lead to com: "+anAction)



    def INITIALIZE(self,sizes:[int],names:[str]=None):
        """
        function to initialize the dynamic networks with snapshots that already exist at the beginning
        :param sizes: list of the snapshots sizes (same order as names
        :param names: list of the snapshots names
        """
        if names==None:
            names=[None]*len(sizes)
        toReturn=[]
        for i,size in enumerate(sizes):
            name = names[i]
            newCommunity = community(self,name)
            newCommunity.addNodes([self.createNode() for j in range(size)])
            self._currentCommunities[newCommunity.getName()]=newCommunity
            self._allSeenCommunities.add(newCommunity)
            toReturn.append(newCommunity)
        self.memorizeCurrentConfiguration()
        return toReturn



    def memorizeCurrentConfiguration(self):
        g = self._generateCurrentNetwork()

        # memorize the current step of the graph in the dynamic network
        self._dynGraph.add_snapshot(self._currentT, g)

        if self._verbose:
            print("snapshots end of step: ", self._currentCommunities.keys())

        # Memorize the current partition in the dynamic partition
        self._dynCom.add_empy_sn(self._currentT)
        for c in self._currentCommunities.values():
            if type(c) is community:
                if (self._verbose):
                    print("list of current com: adding com ", self._currentT, " ", c.name())
                self._dynCom.add_community(self._currentT, c.nodes(), c.name())

        self._currentT += 1

    def run(self):
        """
        Function to call when the scenario has been defined to actually execute it.
        Return a dynamic network and the corresponding dynamic partition
        :return: a couple, first element is the dynamic network, second element is the dynamic partition
        """

        #While there is an action to do or there is an operation still going on
        while len(self._actions)>0 or len([x for x in self._currentCommunities.values() if type(x) is operation])>0:
            if(self._verbose):
                print("TIME : ", self._currentT)
                print("snapshots start of step: ", self._currentCommunities.keys())


            #get the list of communities and events currently active
            readycoms =  set(self._allSeenCommunities)


            for action in self._actions: #for each action (could be optimized but unnecessary on small scenarios
                if action["t"]<=self._currentT: #if static time passed

                    op = action["operation"]

                    affectedComs = set(op._beforeCommunities) #communities affected by this action
                    lockingComs= set() #IDs of events/coms used as triggers

                    if action["waitFor"]!=None: #if there are triggers
                        if type(action["waitFor"]) is community: #(put in right format)
                            action["waitFor"] = {action["waitFor"]}
                        lockingComs.update(action["waitFor"])

                    if len( affectedComs - readycoms)==0: #if all necessay coms are ready
                        if len (lockingComs - readycoms)==0: #and triggers are ready
                            if action["wait"]!=0: #if user wants to wait, wait
                                action["t"]= self._currentT + action["wait"]
                                action["wait"]=0
                            else:
                                self._activateAction(op)
                                self._actions.remove(action)

                                ### Section only to manage the representation of the reference partition as an event graph ####
                                #action activated, store the current event in the eventGraph with placeholders for resulting coms, since we do not know when
                                #the operation will be ended
                                for before in op._beforeCommunities:
                                    for after in op._afterNames:
                                        if "|DEATH|" not in after:
                                            lastCommunityPresence = self._currentT - 1
                                            self._dynCom.add_event((lastCommunityPresence, before.name()), (after), lastCommunityPresence, lastCommunityPresence, type=op._action, score=-1)

                                ################################################################################################

            self.memorizeCurrentConfiguration()


        ######Managing the event graph reference partition ####
        self._dynCom.create_standard_event_graph(keepingPreviousEvents=True)

        return(self._dynGraph, self._dynCom)


################### COMPOSED OPERATIONS ####################

# def theseusBoat(theComTh, wait=3):
#     initialNodes = list(theComTh.nodes())
#     name = theComTh.name()
#     currentID = theComTh.get_ID()
#     size = len(initialNodes)
#     comScen = theComTh.comScenar
#
#     planksInStoreHouse = []
#     for i in range(size):
#         xCom = comScen.birth(size=1,waitFor=currentID,wait=wait)
#         comPlus1 = comScen.merge([name, xCom.name()], name)
#         nodeToRemove = initialNodes[i]
#         currentID = comPlus1.get_ID()
#
#         [killed, comMinus1] = comScen.migrate([name], ["toKill" + str(i), name], splittingOut= [{nodeToRemove}, set(comPlus1.nodes()) - {nodeToRemove}],
#                                             wait=wait, waitFor=currentID)
#
#
#         #comScen.addAction(operation("death", [killed.name()]))
#         planksInStoreHouse.append(killed.name())
#
#
#         currentID = comMinus1.get_ID()
#
#     comScen.merge(planksInStoreHouse,"newShip",waitFor=[comMinus1.get_ID()])







def migrateIterative(comFrom, comTo, nbNodes, wait=1):
    comScen = comFrom._comScenar
    currentFrom = comFrom
    currentTo = comTo
    for i in range(nbNodes):
        migratingNode = np.random.choice(list(currentFrom.getNodes()),1)[0]
        [currentFrom,currentTo] = comScen.migrate(
            [currentFrom,currentTo],
            [currentFrom.getName(), currentTo.name()],
            [currentFrom.getNodes() - set([migratingNode]), currentTo.nodes() | set([migratingNode])],
            wait=wait
        )


def growIterative(com, nodes2Add, wait=1):
    comScen = com._comScenar

    currentCom = com
    for i in range(nodes2Add):
        newNode = comScen.create_node()
        [currentCom] = comScen.migrate(
            [currentCom],
            [currentCom.getName()],
            [currentCom.getNodes() | set([newNode])],
            wait=wait
            )
        print(currentCom.name())
    return currentCom

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