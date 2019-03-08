import networkx as nx
from tnetwork.utils.community_utils import _jaccard
from tnetwork.DCD.computing_coms_by_sn import *

#coming from falkowsky : Mining and Visualizing the Evolution of Subgroups in Social Networks


def _match_communities_according_to_com(dynComSN, matchesGraph):
    """

    :param dynComSN:
    :param matchesGraph:
    :return:
    """
    #find snapshots in the graph of matching
    node2comID = best_partition(matchesGraph)
    #for each "node" (of this network of snapshots)
    for (t,c),cID in node2comID.items():
        #create an ID
        newComID = "DC_"+str(cID)
        #if this Id is already present, means that 2 snapshots of the SAME timestep are merged, modified the snapshots accordingly
        if newComID in dynComSN._snapshots[t].inv:
            dynComSN._snapshots[t].inv[newComID]=dynComSN._snapshots[t].inv[newComID].union(c)
            del dynComSN._snapshots[t][c]
        else: #replace the ID of the (local) community by the ID of the (global) community
            dynComSN._snapshots[t][c]=newComID #add DC_ to avoid confusion with already assigned com ID






def _build_matches_graph(partitions, mt):
    graph = nx.Graph()
    coms = partitions.communities()

    allComs = set()
    for t in coms:  # for each date taken in chronological order
       for c in coms[t]:
           allComs.add((t,c))


    for com1 in allComs:
        for com2 in allComs:
            if com1!=com2: #if not same community
                jac = _jaccard(com1[1], com2[1])
                if jac>=mt:
                    commonNodes = len(com1[1] & com2[1])
                    identityPreservation = commonNodes / len(com1[1]) * commonNodes / len(com2[1])

                    graph.add_edge(com1,com2,weight=jac)#the weight is used such as the louvain algorihtm applied afterwards uses it (not sure it does)

    return graph

def matching_survival_graph(dynNetSN, mt=0.3): #mt is the merge threashold. Algo can be either a networkx function returning snapshots of the string "louvain" to use louvain algorithm


    dynComSN = iterative_louvain(dynNetSN)

    matchesGraph = _build_matches_graph(dynComSN, mt)

    _match_communities_according_to_com(dynComSN, matchesGraph)

    dynComSN.create_standard_event_graph()

    return dynComSN

