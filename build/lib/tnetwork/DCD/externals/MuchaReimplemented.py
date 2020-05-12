import networkx as nx

from tnetwork.DCD.pure_python.static_cd.louvainModified import best_partition
from tnetwork import dynamicCommunitiesSN


def mucha(dynNetSN, om=0.5,form="local"):
    #print("INITIALISING MUCHA ")

    #needs to remove singleton otherwise bugs with louvain
    dynNetSN.remove_nodes_from(dynNetSN.isolates())


    graphs = dynNetSN.snapshot_affiliations()

    #unify all slices in a single network
    multiSliceGraph = nx.Graph()

    #print("Merging all graphs in one")
    for SNt in graphs:
        tOfSN = SNt
        edges = graphs[SNt].edges()
        edgesToAdd=[((tOfSN,e[0]),(tOfSN,e[1])) for e in edges]
        multiSliceGraph.add_edges_from(edgesToAdd)

    #print("Adding interSlice edges")
    for i in range(len(graphs)-1):

        currentNodes = set(graphs.peekitem(i)[1].nodes())
        currentT = graphs.peekitem(i)[0]

        edgesToAdd = []
        if form=="local":
            nextNodes = set(graphs.peekitem(i+1)[1].nodes())
            nextT = graphs.peekitem(i+1)[0]

            commonNodes = currentNodes & nextNodes

            for nc in commonNodes:
                edgesToAdd.append(((currentT,nc),(nextT,nc),om))
        elif form=="meso":
            for j in range(i+1,len(graphs)):
                nextNodes = set(graphs.peekitem(j)[1].nodes())
                nextT = graphs.peekitem(j)[0]

                commonNodes = currentNodes & nextNodes

                for nc in commonNodes:
                    val = om/(j-i)
                    if val>0.05:
                        edgesToAdd.append(((currentT, nc), (nextT, nc),val))

        elif form == "global":
            for j in range(i, len(graphs)):
                nextNodes = set(graphs.peekitem(j)[1].nodes())
                nextT = graphs.peekitem(j)[0]

                commonNodes = currentNodes & nextNodes

                for nc in commonNodes:
                    edgesToAdd.append(((currentT, nc), (nextT, nc), om))
        multiSliceGraph.add_weighted_edges_from(edgesToAdd)


    #print("Creating the multislice null model")

    multiSliceNullModel = nx.Graph()
    edgesToAdd=[]
    for tOfSN in graphs:
        degrees = dict(graphs[tOfSN].degree())
        sumDegrees = sum(degrees.values())
        for n1 in degrees:
            for n2 in degrees:
                edgesToAdd.append(((tOfSN,n1),(tOfSN,n2),degrees[n1]*degrees[n2]/sumDegrees))
    multiSliceNullModel.add_weighted_edges_from(edgesToAdd)

    partitions = best_partition(multiSliceGraph,multiSliceNullModel)

    communities = dynamicCommunitiesSN()
    for node in partitions:
        affilCom = partitions[node]
        affilT = node[0]
        affilNode = node[1]
        #affilT = timesList[affilTi]
        communities.add_affiliation(affilNode, affilCom, affilT)
        #addNodeComRelationship(node[1],affilCom,affilTi,affilTi,self.discretisation)

    return communities

