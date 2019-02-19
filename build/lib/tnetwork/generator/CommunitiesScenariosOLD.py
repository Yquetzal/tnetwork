import tnetwork as dn
import networkx as nx
import numpy as np
import random
import operator
import math
import matplotlib.pyplot as plt

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
    alpha = 0.75
    return math.ceil((math.pow(nbNodes - 1, alpha) * nbNodes) / 2)


















class abstractStructure():
    """
    this interface can be instanciated as a community or an ongoing operation
    Be careful, structures have NAMES and IDS.
    Name is a "label" that is used to decide which community is "the same" as another one, in term of identity (search "ship of theseus paradox" if unclear)
    ID is a unique identifer created automatically after each modification. The "same" community before and after an even has different ID.
    An ID corresponds to a particular "state" of a community (note that a community keeps the same ID as long as it is not modified)
    """


    #Return all pairs of nodes inside the structure, and their Latent Affinity
    def getInternPairsAffinity(self):
        pass

    #Return the edges inside the structure (at the end of the process for an ongoing operation
    def getInternEdges(self,variant="best"):
        pass

    #Get the unique ID of this structure
    def getID(self):
        pass

    #Get the name of the structure
    def getName(self):
        pass


class community(abstractStructure):

    #Initialize a community
    def __init__(self,comScenario,name=None):
        """

        :param comScenario: current Scenario class
        :param name: the name of the community
        """
        #generate a unique ID
        id = comScenario._getNewID(prefix="COM")

        self.id = id
        self.name=name

        if self.name==None:
            self.name=self.id


        self._nodes = set()
        self._internPairs = None #will be a dictionary of {set of nodes:pair importance}
        self.comScenar = comScenario

        #
        self.lockedBy = None

        #comScenario.comName2ID.setdefault(self.name,[]).append(self.id)

    def _addNode(self, n):
        self._nodes.add(n)
        self._internPairs=None #for optimization

    def addNodes(self, nodes):
        """
        Add nodes to a community
        :param nodes:
        :return:
        """
        for n in nodes:
             self._addNode(n)


    def getNodes(self):
        """
        Return the list of nodes in this community
        :return: [str]
        """
        return self._nodes


    def getInternPairsAffinity(self):
        """
        Optimized to compute anew only in case of change
        :return:
        """
        if self._internPairs==None:
            temp = set()
            for n in self._nodes:
                for n2 in self._nodes:
                    if n!=n2:
                        temp.add(frozenset((n, n2)))
            self._internPairs = {k:self.comScenar.pairsImportance[k] for k in temp}
        return self._internPairs


    def getNbInternEdges(self):
        """
        return the number of edges expected in this community
        :return:
        """
        if len(self._nodes)==1:
            return 0

        nbNodes = len(self._nodes)

        return computeNbEdgesForACommunitySize(nbNodes)


    def getID(self):
        return self.id

    def getName(self):
        return self.name



    def getInternEdges(self,variant="best"):
        """
        Return edges that we consider should exist in this community.
        In the default behavior ("best")
        :param variant:
        :return:
        """
        sortedPairs = sorted(self.getInternPairsAffinity().items(), key=operator.itemgetter(1), reverse=True)
        if(variant=="best" or len(sortedPairs)==0):
            chosenEdges = sortedPairs[:math.ceil(self.getNbInternEdges())]

        #or random variant
        if(variant=="random"):
            chosenEdges = random.sample(sortedPairs,int(self.getNbInternEdges()))

        chosenEdges = [x[0] for x in chosenEdges]
        return chosenEdges






class operation(abstractStructure):
    #This class corresponds to an ongoing operation between communities. When the operation is finished, should disappear and be replaced by a community object (or nothing if death...)
    def __init__(self, action, beforeIDS=[], afterIDS=[],parameters=None):
        """

        :param action: The type of action, as a string. It can be an atomic of simple event (birth, death, migrate, split, merge)
        :param beforeIDS: the unique IDs of the communities involved in the event
        :param afterIDS: the unique IDs of the communities resulting of the event
        :param comScenario:
        :param parameters: dict(), splitting:{{n1,n2,...n5},{n6,...,n10},...,{}} , splitSize:[n/3,n/3,n/3]
        """
        self.action=action
        self.beforeIDS = beforeIDS
        self.afterIDS = afterIDS
        self.comScenario = comScenario
        self.parameters = parameters



        #?
        self.before = None
        self.after=None
        self.finalCommunities = set()



        self.inProgress = [] #list of modifications to do to reach the final community

        self.currentEdges = set()
        self._internPairs = set()


    def initialise(self,comScen):
        """
        This function is called by the ongoing scenario as soon as it is added not when actually doing it. It
        already initialize everyhting that should happen but do not actually do it
        :param comScen: the ongoing scenario
        :return:
        """
        self.comScenario = comScen


        self.after=[]
        self.before=[]
        #Retrive the communities with given names in their current state. Note that we manipulate names instead of IDs because
        # 1) It should be easier for the user
        # 2) ...
        for comName in self.beforeIDS:
            self.before.append(self.comScenario._retrieveLastCommunityWithName(comName))

        #Create new clusters with zero nodes with appropriate names
        for comName in self.afterIDS:
            self.after.append(community(comScen, name=comName))


        #if self.action=="split":
        #    self._split()
        #if self.action=="merge":
        #    self._merge()

        if self.action=="birth":
            self._birth()

        if self.action=="death":
            self._death()

        if self.action=="migrate":
            self._migrate()

        if self.action not in ["birth","death","migrate"]:
            raise Exception("UNKNOWN operation: "+self.action)

        self._computeEdgeModificationsToDo()


    def _computeEdgeModificationsToDo(self):
        """
        This function compute the list of modifications that should be done
        :return:
        """

        currentEdges = set()
        edgesAfter = set()


        for c in self.before:
            currentEdges.update(c.getInternEdges( ))

        for c in self.after:
            edgesAfter.update(c.getInternEdges())

        toRemove = set(currentEdges) - set(edgesAfter)
        toAdd = set(edgesAfter) - set(currentEdges)

        self.currentEdges = currentEdges
        self.inProgress = self.randomizeActions(toRemove,toAdd)


    def _birth(self):
        #If no community is given, create a community with automatic name
        if len(self.after)==0:
            #self.after.append(self.comScenario.createCluster(0, activeCluster=False))
            self.after.append(community(self.comScenario))
            self.afterIDS=[self.after[0].getName()]
        #afterCom = self.comScenario.createCluster(0, list(self.afterIDS)[0], activeCluster=False)

        #If we do not specify the nodes that should be added to this community (?), create nodes
        if not "nodes" in self.parameters:
            self.parameters["nodes"]=set()
            for i in range(self.parameters["size"]):
                self.parameters["nodes"].add(self.comScenario.createNode())

        self.after[0].addNodes(self.parameters["nodes"])

    # def _merge(self):
    #
    #     #afterCom = self.comScenario.createCluster(0,list(self.afterIDS)[0],activeCluster=False)
    #     for c in self.before:
    #         self.after[0].addNodes(c.getNodes())

    def _death(self):
        #the community is removed automatically because self.before is removed and nothing is added to replace.
        #nodes must not be killed now because this code is called during scenario definition.
        pass
        # for c in self.before:
        #     for n in c.getNodes():
        #         self.comScenario.killNode(n)

    def _migrate(self):
        if self.parameters==None:
            self.parameters=dict()


        if not "sizesIn" in self.parameters: # by default, take all nodes in all input coms
            self.parameters["sizesIn"]= [len(c.getNodes()) for c in self.before]

        if not "sizesOut" in self.parameters and not "splittingOut" in self.parameters: #by default, split evenly among outputs
            self.parameters["sizesOut"]=[]
            for i in range(len(self.after)):
                self.parameters["sizesOut"].append(int(sum(self.parameters["sizesIn"])/len(self.after)))
            if sum(self.parameters["sizesOut"])!=sum(self.parameters["sizesIn"]):
                self.parameters["sizesOut"][0]=self.parameters["sizesOut"][0]+1

        listNodes = []
        for i in range(len(self.before)):
            nodesToTake=self.parameters["sizesIn"][i]
            listNodes += list(self.before[i].getNodes())[:nodesToTake]
        #the migration is done by giving the number of nodes that migrate (currently, not random, attribute by natural order)


        if "sizesOut" in self.parameters:
            #get the list of nodes in the community from which the migration start


            #For each of the communities we want to migrate them to
            for i in range(len(self.parameters["sizesOut"])):
                cSize = self.parameters["sizesOut"][i]
                self.after[i].addNodes(listNodes[:cSize])
                listNodes = listNodes[cSize:]

        #the migration is done by giving the exact list of which node should migrate in each community
        if "splittingOut" in self.parameters:
            for i in range(len(self.parameters["splittingOut"])):
                self.after[i].addNodes(self.parameters["splittingOut"][i])

    # def _split(self):
    #
    #
    #     if "sizes" in self.parameters:
    #         listNodes = list(self.before[0].getNodes())
    #         for i in range(len(self.parameters["sizes"])):
    #             cSize = self.parameters["sizes"][i]
    #             self.after[i].addNodes(listNodes[:cSize])
    #             listNodes = listNodes[cSize:]
    #
    #     if "splitting" in self.parameters:
    #         for i in range(len(self.parameters["splitting"])):
    #             self.after[i].addNodes(self.parameters["splitting"][i])



    #function that shuffle edges addition and removal
    def randomizeActions(self,notKept,added):
        toReturn = list()
        for e in notKept:
            toReturn.append(("-",e))

        for e in added:
            toReturn.append(("+",e))

        random.shuffle(toReturn)
        return toReturn


    #Function that is called from outside to get the number of intern edges.
    #This function actually makes the following step of change, and if all steps of change are done, inform the main program that it is finished.
    def getInternEdges(self,variant="ignored"):
        if len(self.inProgress)!=0: #case of a community created without any edge to modify (community with a single node for instance)
            modif = self.inProgress.pop()
            if modif[0]=="-":
                self.currentEdges.remove(modif[1])
            if modif[0]=="+":
                self.currentEdges.add(modif[1])

        if len(self.inProgress)==0:
            self.comScenario._terminateOperation(self)
        return self.currentEdges

    def getInternPairsAffinity(self):
        return self._internPairs

    def getID(self):
        return str(self.beforeIDS)+"=>"+str(self.afterIDS)

    def getName(self):
        return str(self.beforeIDS)+"=>"+str(self.afterIDS)

    def getNodes(self):
        allNodes = set()
        for com in self.after:
            allNodes.update(com.getNodes())
        return allNodes



#This class manage the community evolution sceneario
class comScenario():
    def __init__(self,variant="best",verbose=True,coeffCommunity=0.01):
        self.pairsImportance =dict() #List of importance for each pair of nodes in the graph
        self.abstractCommunities = dict()  # type:{str:community} #dictionary containing the list of all currently active communities {name:object}

        self.currentID=0 #To ensure that all community IDs are different

        self.allSeenNodes = set() #list of nodes that appear at least once (to manage pairsimportance
        self.currentT=0 #keep track of time

        self.dynGraph=dn.DynGraphSN() #used to memorize the dynamic graph
        self.dynCom = dn.dynamicCommunitiesSN() #Used to memorize the dynamic communities


        self.variant=variant #the variant of the generator controls the way edges are generated

        self.actions=list() #list of community operations to do
        self.verbose=verbose
        self.coeffCommunity=coeffCommunity


    def _getCurrentNodes(self):
        allNodes=set()
        for name,com in self.abstractCommunities.items():
            allNodes.update(set(com.getNodes()))

        return allNodes

    def _getNbInterEdges(self):
        """
        :return: number edges to have between communities
        """
        nbNodes = len(self._getCurrentNodes())
        coeffReduction=self.coeffCommunity
        alpha=0.75
        return math.ceil(coeffReduction*(math.pow(nbNodes - 1, alpha) * nbNodes) / 2)





    def getNewID(self, prefix=""):
        """
        Fonction to generate a unique ID.
        :param prefix: optional prefix
        :return:
        """
        toR = self.currentID
        self.currentID += 1
        return prefix + "_t_" + str(self.currentT).zfill(4) + "_" + str(toR).zfill(4)


    def _terminateOperation(self, operation):
        """
        Terminate an ongoing operation
        :param operation:
        :return:
        """
        if(self.verbose):
            print("---------END OF OPERATION: ",operation.getName())

        del self.abstractCommunities[operation.getName()]
        for com in operation.after:
            self.abstractCommunities[com.getName()] = com

            #Memorising the states of communities (for random assignment ?)
            ###comSteps.setdefault(com.getName(), []).append(set(com.getInternEdges(variant=self.variant)))
            if len(operation.before)>0:
                #print("nodes:",self.dynCom.events.nodes)
                #update the name of community with the event graph now that we know the time of end of operation
                nx.relabel_nodes(self.dynCom.events,{com.getName():(self.currentT,com.getName())},copy=False)

    def generateCurrentNetwork(self):
        """
        Return a graph generated according to the current community structure
        :return:
        """
        g = nx.Graph()
        currentNodes = self._getCurrentNodes()
        intercomEdges = self.pairsImportance.copy()
        intercomEdges = {k:v for k,v in intercomEdges.items() if len(k & currentNodes)==2}

        #for each community
        for c in list(self.abstractCommunities.values()):

            internPairs = c.getInternPairsAffinity()

            chosenEdges = c.getInternEdges(variant=self.variant)


            ###REMOVE intern pairs from possible pairs for inter-com edges
            for e in internPairs:
                del intercomEdges[e]



            #add the selected edges to the graph
            g.add_edges_from(chosenEdges)


        sortedPairs = sorted(intercomEdges.items(), key=operator.itemgetter(1),reverse=True)
        wantedNbInterEdges = self._getNbInterEdges()
        chosenEdges = sortedPairs[:math.floor(wantedNbInterEdges)]
        chosenEdges = [x[0] for x in chosenEdges]
        #add the selected edges to the graph
        g.add_edges_from(chosenEdges)

        return g


    def createNode(self,id=None):
        """
        This is the only function allowed to create nodes
        :param id:
        :return:
        """

        if id==None:
            id=self.getNewID("n")


        for n in self.allSeenNodes:
            self.pairsImportance[frozenset((n,id))]=np.random.random()
        self.allSeenNodes.add(id)

        if(self.verbose):
            print("----created node ",id)
        return id

    #def killNode(self,id):
       # if (self.verbose):
        #    print("----killing node ", id)
        #pass
        #self.allNodes.remove(id)


    # def createCluster(self, nbNodes=0, nameCl=None, activeCluster=True):
    #     """
    #
    #     :param nbNodes: number of initial nodes
    #     :param nameCl: name
    #     :param activeCluster: If true, the cluster is considered
    #     :return:
    #     """
    #
    #     newcom = community(self, name=nameCl)
    #     if activeCluster:
    #         self.abstractCommunities[nameCl]=newcom
    #     for i in range(nbNodes):
    #         newN = self.createNode()
    #         newcom.addNode(newN)
    #
    #     #self.readyComs.add(newcom.id)
    #     return newcom

    def addAction(self,action,t=0,wait=0,waitFor=None):
        """

        :param action: the action to add
        :param t: the time at which we start to consider the activation of this action
        :param wait: the time we should wait after all conditions are fulfilled for activating it
        :param waitFor: the ID of the event(s) that should be finished before considering activation
        :return: the ID or IDs of communities created by this action
        """
        if (self.verbose):
            print("----request action ", action.action, action.getName())
        action.initialise(self)
        if (self.verbose):
            print("----added action ", action.action, action.getName())

        self.actions.append({"operation": action, "t": t, "wait": wait,"waitFor":waitFor})
        return action.after

    def merge(self,toMerge, merged,t=0,wait=0,waitFor=None):
        """

        :param toMerge: names of communities to merge
        :param merged: name of the merged community
        :param t:
        :return:
        """
        if type(merged) is str:
            merged = [merged]
        mergedCom = self.addAction(operation("migrate",beforeIDS=toMerge,afterIDS=merged,parameters=None),t,wait,waitFor)
        return mergedCom

        #for com in mergedCom: #remove communities that disappeared (all if name is not kept)
         #   if not com.getName() in merged:
          #      self.addAction(operation("death", beforeIDS=com.getID()), t,
           #                    wait=0, waitFor=com.getID())

    def split(self,toSplit, newComs,t=0,wait=0,waitFor=None,parameters=None):
        """

        :param toMerge: names of communities to merge
        :param merged: name of the merged community
        :param t:
        :return:
        """
        if type(toSplit) is str:
            toSplit = [toSplit]
        splittedCom = self.addAction(operation("migrate",beforeIDS=toSplit,afterIDS=newComs,parameters=parameters),t,wait,waitFor)
        return splittedCom
        #if not toSplit in newComs:
         #   self.addAction(operation("death", beforeIDS=toSplit), t, wait=0, waitFor=splittedCom[0].getID())


    def activateAction(self,op):
        if (self.verbose):
            print("---------ACTIVATING: ", op.getName())
        self.abstractCommunities[op.getName()] = op

        #delete the communites involved in the operation from the list of currently existing communities
        for c in op.before:
            del self.abstractCommunities[c.getName()]


    def retrieveLastCommunityWithName(self,anAction):
        for action in reversed(self.actions):
            if anAction in action["operation"].afterIDS:
                return action["operation"].after[action["operation"].afterIDS.index(anAction)]
        raise Exception("OPERATION MISSING to lead to com: ",anAction.getName())


    def run(self):
        #While there is an action to do or there is an operation still going on
        while len(self.actions)>0 or len([x for x in self.abstractCommunities.values() if type(x) is operation])>0:
            if(self.verbose):
                print("TIME : ",self.currentT)
                print("communities start of step: ",self.abstractCommunities.keys())
                #print("action start of step: ",[a["operation"].getName() for a in self.actions])


            #get the list of names and IDs of communities and events currently active
            readycomNames = {c.getName() for c in self.abstractCommunities.values()}
            readycomIDs = {c.com_ID() for c in self.abstractCommunities.values()}


            for action in self.actions: #for each action (could be optimized but unnecessary on small scenarios
                if action["t"]<=self.currentT: #if static time passed

                    op = action["operation"]

                    affectedComs = set(op.beforeIDS) #names of communities affected by this action
                    lockingComsIDs= set() #IDs of events/coms used as triggers

                    if action["waitFor"]!=None: #if there are triggers
                        if type(action["waitFor"]) is str: #(put in right format)
                            action["waitFor"] = {action["waitFor"]}
                        lockingComsIDs.update(action["waitFor"])

                    if len( affectedComs - readycomNames)==0: #if all necessay coms are ready
                        if len (lockingComsIDs - readycomIDs)==0: #and triggers are ready
                            if action["wait"]!=0: #if user wants to wait, wait
                                action["t"]=self.currentT+action["wait"]
                                action["wait"]=0
                            else:
                                self.activateAction(op)
                                self.actions.remove(action)

                                #action activated, store the current event in the eventGraph with placeholders for resulting coms, since we do not know t
                                for before in op.beforeIDS:
                                    for after in op.afterIDS:
                                        lastCommunityPresence = self.currentT-1
                                        self.dynCom.add_event((lastCommunityPresence, before), (after), lastCommunityPresence, lastCommunityPresence, type=op.action, score=-1)

            g=self.generateCurrentNetwork()
            self.dynGraph.add_snaphsot(self.currentT, g)
            #nx.draw_networkx(g,with_labels=True)#,labels={k:k.getName() for k in g.nodes})

            if self.verbose:
                print("communities end of step: ",self.abstractCommunities.keys())

            self.dynCom.add_empy_sn(self.currentT)
            for c in self.abstractCommunities.values():
                if type(c) is community:
                    if (self.verbose):
                        print("list of current com: adding com ",self.currentT," ",c.getName())
                    self.dynCom.addCommunity(self.currentT,c.getNodes(),c.getName())


            plt.show()
            self.currentT+=1

        #print("eventGraph",self.dynCom.events.edges)
        self.dynCom.create_standard_event_graph(keepingPreviousEvents=True)


################### COMPOSED OPERATIONS ####################

def theseusBoat(theComTh, wait=3):
    initialNodes = list(theComTh.getNodes())
    name = theComTh.getName()
    currentID = theComTh.com_ID()
    size = len(initialNodes)
    comScen = theComTh.comScenar

    planksInStoreHouse = []
    for i in range(size):
        xCom = comScen._addAction(operation("birth", parameters={"size": 1}), waitFor=currentID,
                                  wait=wait)
        comPlus1 = comScen.merge([name, xCom[0].getName()], [name])
        nodeToRemove = initialNodes[i]
        currentID = comPlus1[0].com_ID()

        [killed, comMinus1] = comScen.split([name], ["toKill" + str(i), name], parameters={
            "splittingOut": [{nodeToRemove}, set(comPlus1[0].getNodes()) - {nodeToRemove}]},
                                            wait=wait, waitFor=currentID)


        #comScen.addAction(operation("death", [killed.getName()]))
        planksInStoreHouse.append(killed.getName())


        currentID = comMinus1.com_ID()

    comScen.merge(planksInStoreHouse,"newShip", waitFor=[comMinus1.com_ID()])



def migration(comFrom, comTo, nbNodes, wait=0):
    comScen = comFrom.comScenar

    currentFrom = comFrom
    for i in range(nbNodes):
        [switched, currentFrom] = comScen.split([comFrom.getName()], ["toSwitch" + str(i), comFrom.getName()],
                                                parameters={"sizesOut": [1, len(currentFrom.getNodes()) - 1]},
                                                wait=wait, waitFor=currentFrom.getID())
        comScen.merge([comTo.getName(), switched.getName()], [comTo.getName()], waitFor=switched.com_ID())


def growIterative(com, nodes2Add, wait=1):
    comScen = com.comScenar

    currentCom = com
    # currentID = com.getID()
    # name = com.getName()
    for i in range(nodes2Add):
        xCom = comScen._addAction(operation("birth", parameters={"size": 1}), waitFor=currentCom.getID(),
                                  wait=wait)
        [comPlus1] = comScen.merge([currentCom.getName(), xCom[0].getName()], [currentCom.getName()])
        currentCom = comPlus1
    return currentCom

def shrinkIterative(com, nodes2Remove, waitInitial=1,waitStep=1):
    comScen = com.comScenar
    currentCom = com
    # currentID = com.getID()
    # name = com.getName()

    for i in range(nodes2Remove):
        waitToConsider = waitStep
        if i==0:
            waitToConsider = waitInitial
        currentNbNodes = len(currentCom.getNodes())
        print("----",i,currentCom.getID(),currentNbNodes,currentCom.getName())
        [killed, comMinus1] = comScen.split([currentCom.getName()], ["toDisappear" + str(i), currentCom.getName()], parameters={"sizesOut":[1,currentNbNodes-1]}, wait=waitToConsider, waitFor=currentCom.getID())
        comScen._addAction(operation("death", [killed.getName()]))
        currentCom = comMinus1
    return currentCom