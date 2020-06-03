import networkx as nx
from tnetwork.DCD.computing_coms_by_sn import *
from tnetwork.DCD.algorithm_template import DCD_algorithm


def _match_communities_according_to_com(dynComSN, matchesGraph):
    """

    :param dynComSN:
    :param matchesGraph:
    :return:
    """
    #find snapshot_affiliations in the graph of matching
    node2comID = best_partition(matchesGraph)
    #for each "node" (of this network of snapshot_affiliations)
    for (t,nodes,original_cID),cid_new in node2comID.items():
        #create an ID
        newComID = "DC_"+str(cid_new) #add DC_ to avoid confusion with already assigned com ID
        #if this Id is already present, means that 2 snapshot_affiliations of the SAME timestep are merged, modified the snapshot_affiliations accordingly
        if newComID in dynComSN.snapshot_communities(t):
            dynComSN.snapshots[t][newComID]=dynComSN.snapshots[t][newComID].union(nodes)
        else: #replace the ID of the (local) community by the ID of the (global) community
            dynComSN.snapshots[t][newComID]=nodes
        del dynComSN.snapshots[t][original_cID]






def _build_matches_graph(partitions, match_function, threshold=0.3):
    graph = nx.Graph()
    coms = partitions.snapshot_communities()

    allComs = []
    for t in coms:  # for each date taken in chronological order
        for id,nodes in coms[t].items():
            allComs.append((t,frozenset(nodes),id))

    for i in range(len(allComs)):
        for j in range(i,len(allComs)):
            com1 = allComs[i]
            com2 = allComs[j]
            if com1!=com2: #if not same community
                score = match_function(com1[1], com2[1])
                if score>=threshold:
                    #commonNodes = len(com1[0] & com2[0])
                    #identityPreservation = commonNodes / len(com1[0]) * commonNodes / len(com2[0])

                    graph.add_edge(com1,com2,weight=score)#the weight is used such as the louvain algorihtm applied afterwards uses it (not sure it does)

    return graph

def label_smoothing(dynNetSN, CDalgo="louvain", match_function=jaccard, threshold=0.3,multithread=False, **kwargs):
    """
    Community detection by label smoothing

    This method is based on falkowsky et al.[1]. It first detect communities in each snapshot, then try to match
    any community with any other one in any other snapshot, constituting a survival graph.
    A community detection algorithm is then applied on this survival graph, yielding dynamic snapshot_communities.

    [1]Falkowski, T., Bartelheimer, J., & Spiliopoulou, M. (2006, December).
    Mining and visualizing the evolution of subgroups in social networks.
    In Proceedings of the 2006 IEEE/WIC/ACM International Conference on Web Intelligence (pp. 52-58). IEEE Computer Society.

    :param dynNetSN: a dynamic network
    :param CDalgo: community detection to apply at each step. Can be a function returning a clustering, or the string "louvain" or "smoothedLouvain"
    :param match_function: a function that gives a matching score between two snapshot_communities (two sets of nodes). Default: jaccard
    :param threshold: a threshold for match_function below which snapshot_communities are not matched
    :return: DynCommunitiesSN
    """
    if CDalgo == "louvain":
        CDalgo = None
    cd_method = lambda x: CD_each_step(x, CDalgo,multithread)


    def matching_method(x):
        matchesGraph = _build_matches_graph(x, match_function, threshold)
        _match_communities_according_to_com(x, matchesGraph)
        x.create_standard_event_graph()
        return x

    return DCD_algorithm(dynNetSN,"label_smoothing", detection=cd_method, label_attribution=matching_method, **kwargs)



