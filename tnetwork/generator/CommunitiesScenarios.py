import tnetwork as dn
import networkx as nx
from sortedcontainers import *
from numpy.random import choice
import numpy as np
import random


class nodeAgent():
    def __init__(self,id,community,graph):#,desiredIntern=0,desiredExtern=0):
        self.id = id
        self.community = community
        self.graph=graph
        #self._desiredInternEdges = desiredIntern
        #self._desiredExternEdges = desiredExtern

    def addCommunity(self,id,mixCoeff):
        self._desiredMixingCoeff=mixCoeff
        self.comID=id

    def setNewDegree(self,degree):
        self._desiredDegree=degree

    #def removeCommunity(self,community):
    #    self.community.remove(community)
    def getDesiredDegree(self):
        return self.community.desiredDensity*len(self.community.nodes)

    def getWantIn(self):
        return self.community.getDesiredDegree()- nx.degree(self.graph,self)

    def satisfied(self):
        return abs(self.getWant())<=1


class communityAgent():
    def __init__(self,id,graph,desiredDensity):
        self.id = id
        self.nodes = {}
        self.graph=graph
        self.desiredDensity = desiredDensity
        self.tolerance=0.1

    def addNode(self,n):
        self.nodes.append(n)

    def addNodes(self, nodes):
        for n in nodes:
            self.addNode(n)

    def satisfied(self):
        if self.density()< self.desiredDensity*(1-self.tolerance) or  self.density()> self.desiredDensity*(1+self.tolerance):
            print("com unsatisfied",self.id,self.density,self.desiredDensity)
            return False
        for n in self.nodes:
            if not n.satisfied():
                print("node unsatisfied",n.id," com: ",self.id,n.getWantIn())
                return False
        return True

    def randomUpdate(self): #rate = 0.1
        if (len(self.nodes) >= 3):
            # introduce random intern modification
            # removal
            n1 = random.sample(self.nodes, 1)
            internNeighb = self.graph[n1].keys() & self.nodes  # ta
            n2 = random.sample(internNeighb, 1)
            eToRemove = {n1, n2}

            # addition
            n1 = random.sample(self.nodes, 1)
            internNotNeighb = self.nodes - self.graph[n1].keys()  # ta
            n2 = random.sample(internNotNeighb, 1)
            eToAdd = {n1, n2}
            return (([eToRemove],[eToAdd]))
        return (([],[]))
            # # introduce random extern modification
            # # removal
            # n1 = random.sample(self.nodes, 1)
            # externNeighb = self.graph[n1].keys() - self.nodes  # ta
            # n2 = random.sample(externNeighb, 1)
            # eToRemove = {n1, n2}
            #
            # # addition
            # n1 = random.sample(self.nodes, 1)
            # externNotNeighb = self.graph.nodes.keys() - self.graph[n1].keys() - self.nodes  # ta
            # n2 = random.sample(externNotNeighb, 1)
            # eToAdd = {n1, n2}


    def updateConvergence(self): #speed = 1
        if (len(self.nodes) >= 2):
            #ask nodes want
            listWant = [(n,n.getWant()) for n in self.nodes]
            #listWant.sort(key=lambda x:x[1].wantIntern())

            candidateEdgesAdd=[]
            candidateEdgesRemove=[]

            for i in range(len(listWant)):
                (n1, val1) = listWant[i]
                for j in range(i+1,len(listWant)):
                    (n2, val2) = listWant[j]
                    if val1>=0 and val2>=0 and val1+val2>0:
                        candidateEdgesAdd.append({n1,n2},val1+val2)

                    if val1<=0 and val2<=0 and val1+val2<0:
                        candidateEdgesRemove.append({n1,n2},val1+val2)

            toAdd = []
            toRemove = []
            if len(candidateEdgesAdd)>0:
                toAdd.append(choice([x[0] for x in candidateEdgesAdd],size=1,replace=False,p=[x[1] for x in candidateEdgesAdd]))
            if len(candidateEdgesRemove)>0:
                toRemove.append(choice([x[0] for x in candidateEdgesRemove],size=1,replace=False,p=[abs(x[1]) for x in candidateEdgesAdd]))

            return ((toRemove,toAdd))
        return (([],[]))





class comScenario():
    def __init__(self):
        self.dynGraph = dn.DynGraphSG()
        self.dynCom = dn.dynamicCommunitiesSN()
        self.currentT = 0
        self.currentNetwork=nx.Graph()
        self.communities=dict() #type:{str:communityAgent}
        self.currentID=0
        self.listOfActions = []
        self.indegrees = 0.5
        self.outdegrees = 0.1
        self.interComEdges=set()

    def run(self):
        for i in range(100):
            for k, c in self.communities.items():
                self.updateCom(c)
            self.checkNextActions()
            self.updateGTcommunities()
            self.currentT += 1

    def updateCom(self,c):
        (toRemove, toAdd) = c.randomUpdate()
        self.applyModifs(toRemove, toAdd)  # modify current graph, historical graph
        (toRemove, toAdd) = c.updateConvergence()
        self.applyModifs(toRemove, toAdd)

    def updateInterCom(self):
        if (len(self.interComEdges) >0):
            toRemove = random.sample(self.interComEdges,1)
        toAdd=[]
        while(len(toAdd)==0):
            (c1,c2) = choice(self.communities,2,replace=False)
            n1 = choice(c1.nodes())
            n2 = choice(c2.nodes())
            if not set(n1,n2) in self.interComEdges():
                toAdd.append(set(n1,n2))
        self.interComEdges = self.interComEdges-toRemove+toAdd



        self.applyModifs(toRemove,toAdd)

    def getNewID(self,prefix=""):
        toR = self.currentID
        self.currentID+=1
        return prefix+"_"+str(self.currentT)+"_"+str(toR)

    def createCommunity(self,nodesDegree,t=0):

        newcom = communityAgent(self.getNewID("BORN"),self.currentNetwork)
        self.communities[newcom.id]=newcom
        for d in nodesDegree:
            self.addNodeAgent(d,self)







    def addNodeAgent(self,community=None):
        """
        Create the node, add to graph, attribute com and attribute node to com
        :param community:
        :return:
        """
        if community==None:
            community = communityAgent(self.getNewID())
        nA = nodeAgent(self.getNewID(),community,self.currentNetwork,self.indegrees,self.outdegrees)
        community.addNode(nA)
        self.currentNetwork.add_node(nA)
        return nA



    def checkNextActions(self):
        comReadies = {x for x in self.communities if x.satisfied()}
        for (t,action,comsBefore,comsAfter,parameters) in self.listOfActions:
            if t<=self.currentT:
                if len(comsBefore-comReadies)==0:
                    action(comsBefore,comsAfter,parameters)



    def applyModifs(self,edgeRemoval,edgeAddition):
        for edge in edgeRemoval:
            (n1,n2) = list(edge)
            self.dynGraph.remove_edge(n1,n2,self.currentT)
            self.currentNetwork.remove_edge(n1,n2)
        for edge in edgeAddition:
            (n1,n2) = list(edge)
            self.dynGraph.add_edge(n1,n2,self.currentT)
            self.currentNetwork.add_edge(n1,n2)

    def updateGTcommunities(self):
        for c in self.communities:
            if c.satisfied():
                self.dynCom.add_belonging(c.nodes, self.currentT, c.id)



















    def mergeClusters(self, originalClustersID, finalID,internDensity=None):
        """
        Merge two clusters. finalID can be equal to ID1 or ID2, or different from them
        :param ID1: name of the first community to merge
        :param finalID: name of the merged community
        :param initialT: date of the beginning of the merge
        :param density: intern density of the merge cluster
        :returns: date of the last modification
        """

        print("merging ", str(originalClustersID))
        if internDensity==None:
            internDensity = self.indegrees

        comAgentToDisappear = [self.communities[c] for c in originalClustersID if not c==finalID]


        for cID in originalClustersID:
            if cID!=finalID:
                self.communities.pop(cID, None)

        if not finalID in self.communities:
            self.communities.append(communityAgent(finalID,self.currentNetwork,self.internDensity))

        mergedCom = self.communities[finalID] #type:communityAgent
        for c in comAgentToDisappear:
            mergedCom.addNodes(c.nodes)

    def createCluster(self, IDcl, nbNodes, internDensity):
        """
        This function creates a cluster with given intern density
        Note that all nodes and edges are created at time t, this is not a pogressive modification of the network
        :param IDcl: the ID assigned to the cluster
        :param t: the apparition of the cluster
        :param nbNodes: number of nodes in the cluster
        :param interDensity: proba of edge between intern nodes
        """

        newCom = communityAgent(IDcl,self.currentNetwork,internDensity)

        for i in range(nbNodes):
            self.addNodeAgent(community=newCom)

            while not newCom.satisfied():
                self.updateCom(newCom)
            while not self.interComSatisfied():
                self.updateInterCom()




    # def addIterativelyNodes(self, ID, nodesCom, t, internDensity, externDensity):
    #     """
    #     add iteratively a list of clusters. Usually, these clusters contain only one node, (nodeCom). The idea is to add a
    #     node to the cluster, then when it is finished add another one, etc.
    #
    #     :param ID: cluster to which to add nodes
    #     :param nodesCom: list of clusters nodecom to add (clusters of a single node)
    #     :param t: time of first operation
    #     :param internDensity: final intern desnity
    #     :param externDensity: final extern desnity
    #     :returns: time of last operation
    #     """
    #
    #     for nc in nodesCom:
    #         t = self.mergeClusters([ID, nc], ID, t, internDensity, externDensity)
    #     return t

comScenar = comScenario()


#iniitlisation
setParam = {"tt":0, "action":"BIRTH", "comsBefore":[], "comsAfter":["a"], "parameters":{"nbNodes":5} }
comScenar.listOfActions.append(setParam)

comToCreate=comScenar.add
comToCreate.run()

# # ---------------------------
# # create the "node migration" scenarios
# # ---------------------------
# def nodeMigration(size1,size2):
#
#     aGenNet.createCluster("NMshrink_" + str(ii) + "_", tStart, size2, internDensity, externDensity)
#     aGenNet.createCluster("NMgrow_" + str(ii) + "_", tStart, size1, internDensity, externDensity)
#     t = 1
#     for i in range(7):
#         oldT = t
#         (t, createdComNode) = aGenNet.removeIterativelyNodes("NMshrink_" + str(ii) + "_", 1, t, internDensity,
#                                                              externDensity)
#
#         t = aGenNet.mergeClusters(["NMgrow_" + str(ii) + "_", createdComNode[0]], "NMgrow_" + str(ii) + "_", t + 1,
#                                   internDensity, externDensity)
#     endOperationsList.append(t)

#dn.show(comToCreate.dynCom, comToCreate.dynGraph)
#com1Nodes=[]
# for i in range(6):
#     comNode = comScenar.addNodeAgent(degrees)
#     #com1Nodes.append(comScenar.addNodeAgent(6))
# comScenar.addDesiredCommunity(nodes=com1Nodes,mixingCoeff=0.4)
#
# com2Nodes=[]
# for i in range(10):
#     com2Nodes.append(comScenar.addNodeAgent(10))
# comScenar.addDesiredCommunity(nodes=com2Nodes,mixingCoeff=0.4)

#initialize

#comScenar.initialize()