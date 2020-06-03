import random
import math


class _AbstractStructure():
    """
    This class can be instanciated as a community or an ongoing operation (class operation)
    Be careful, structures have NAMES and IDS.
    Name is a "label" that is used to decide which community is "the same" as another one, in term of identity (search "ship of theseus paradox" if unclear)
    ID is a unique identifier created automatically after each modification. The "same" community before and after an event has different IDs.
    An ID corresponds to a particular "state" of a community (note that a community keeps the same ID as long as it is not modified)
    """

    def _intern_pairs(self):
        """
        Return all pairs of nodes inside the structure as a dictionary, key: frozenset of two nodes (extremities). value: Latent affinity of the pair
        :return:
        :rtype: {frozenset((str,str)):float}
        """
        pass

    def _intern_edges(self, variant="deterministic"):
        """
        Return edges present inside the structure. If the structure is an ongoing operation, also increment in the ongoing process by adding/removing an edge,
        i.e. the next call to this function will give a different result.
        :param variant: used to chose how edges are drawn. Currently, only "deterministic" is fully supported, (see article)
        :return: [frozenset((str,str))]
        """
        pass

    def label(self):
        """
        Get the name (label) of this structure
        :return: name
        :rtype: str
        """
        pass

    def nodes(self):
        """
        Get the nodes of this structure
        :return: list of nodes
        :rtype: [str]
        """
        pass

    def _memorize_all_internal_pairs(self):
        temp = set()
        for n in self._nodes:
            for n2 in self._nodes:
                if n != n2:
                    temp.add(frozenset((n, n2)))
        self._internPairs = [e for e in self._comScenar._pairsImportance if e in temp]


class Community(_AbstractStructure):
    """
    Class representing communities in a benchmark scenario

    When generating a benchmark using the scenerio generator, communities returned by event definition functions are instances
    of this class.

    This class has some public functions to check the names, the nodes, and the number of edges of the community.
    The edges themselves cannot be checked during the scenario description, since they are generated when calling the run function
    of the ComScenario class.

    """

    def __init__(self, comScenario, label=None):
        """
        Initialize a community
        :param comScenario: current Scenario class this community will belong to.
        :param label: the name of the community. If None, the ID is used as name
        """

        self._label=label
        self._comScenar = comScenario

        if self._label==None:
            # generate a unique name
            self._label=comScenario._get_new_ID(prefix="COM")

        self._nodes = set() #type: {str}

        #For optimization purpose, the internPairs are recomputed only when needed, memorized in this variable
        self._internPairs = None #type: {frozenset((str,str)):float}


    def _add_node(self, n):
        """
        add a node to the community
        :param n: str
        """
        self._nodes.add(n)
        self._internPairs=None #for optimization

    def _add_nodes(self, nodes):
        """
        :param nodes: {str}
        """
        for n in nodes:
             self._add_node(n)


    def nodes(self):
        return self._nodes


    def _intern_pairs(self):
        """
        optimized to compute anew only in case of change
        :return:
        """
        if self._internPairs==None:
            self._memorize_all_internal_pairs()
        return self._internPairs

    def nb_intern_edges(self):
        """
        return the number of edges expected in this community
        :return:
        """
        if len(self._nodes) == 1:
            return 0

        nbNodes = len(self._nodes)

        return self._comScenar.nb_edges_for_a_community_size(nbNodes)

    def label(self):
        return self._label

    def _intern_edges(self, variant="deterministic"):
        """
        Return edges that we consider should exist in this community.
        In the default behavior ("deterministic"), return a fix number of edges, and pick that number at the top of the
        list of node pairs sorted by affinity score
        :param variant: only "deterministic" (default parameter) is fully supported and tested
        :return: list of edges
        :rtype: [frozenset((str,str))]
        """
        #sortedPairs = sorted(self._intern_pairs().items(), key=operator.itemgetter(1), reverse=True)
        if (variant == "deterministic" or len(self._intern_pairs()) == 0):
            chosenEdges = self._intern_pairs()[:math.ceil(self.nb_intern_edges())]

        # or random variant
        if (variant == "random"):
            chosenEdges = random.sample(self._intern_pairs(), int(self.nb_intern_edges()))

        #chosenEdges = [x[0] for x in chosenEdges]
        return chosenEdges

    def __repr__(self):
        return "(" + self.label() + ":n=" + str(len(self._nodes)) + ",m=" + str(len(self._intern_edges())) + ")"#+str(id(self))


    def __str__(self):
        return self.__repr__()

class _Operation(_AbstractStructure):
    """
    This class corresponds to an ongoing operation between snapshot_affiliations.
    When the operation is finished, it disappears and is replaced by a community object (or nothing if death)
    """

    def __init__(self, action, beforeComs=[], afterNames=[], parameters=None):
        """

        :param action: The type of action, as a string. One of {birth, death, migrate}
        :param beforeComs: the snapshot_affiliations modified by the event.
        :param afterNames: the name(s) of the snapshot_affiliations resulting of the event. A unique ID will be created
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

        self._afterCommunities=None #type:[Community]  communities created with the names given in output


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

        #List snapshot_affiliations object corresponding to the names and IDs provided
        self._afterCommunities=[]

        #Create new clusters with zero nodes with appropriate names
        for comName in self._afterNames:
            self._afterCommunities.append(Community(comScen, label=comName))


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

        self._memorize_all_internal_pairs() #at this point, all nodes involved by the operation are known, we compute and memorize internal edges



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
        self._inProgress = self._randomize_actions(toRemove, toAdd)


    def _birth(self):
        """
        This function handle a birth event
        :return:
        """

        #If no community is given, create a community with automatic name
        if len(self._afterCommunities)==0:
            self._afterCommunities.append(Community(self._comScenar))
            self._afterNames=[self._afterCommunities[0].label()]

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

        #if there is no parameter, the migration is obvious from the context, i.e. several snapshot_affiliations in input, a single one in output
        #so let's define sizesIn accordingly


        #Case where the migration is done by giving the exact list of which node should migrate in each community
        for i in range(len(self._parameters["splittingOut"])):
            self._afterCommunities[i]._add_nodes(self._parameters["splittingOut"][i])



    def _randomize_actions(self, notKept, added):
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



    def _intern_edges(self):
        """
             Return edges present inside the structure. If the structure is an ongoing operation, also increment in the ongoing process by adding/removing an edge,
             i.e. the next call to this function will give a different result.
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

    def _intern_pairs(self):
        return self._internPairs

    def label(self):
        return str([c.label() for c in self._beforeCommunities]) + "=>" + str(self._afterNames)

    def nodes(self):
        return self._nodes

    def __repr__(self):
        return self.label()


    def __str__(self):
        return self.label()
