from tnetwork.DCD.computing_coms_by_sn import *
from tnetwork.utils.community_utils import jaccard



def iterative_match(dynNetSN, CDalgo="louvain", match_function=jaccard, threshold=0.3, labels=True):
    """
    Community Detection by iterative detection and matching

    This algorithm is inspired by the one proposed by Greene et al., [1] but additionally to the detection of match
    between communities in consecutive snapshots, a post process assign labels to communities, based on the
    following rules:

    * A community "send" its label to the community the most similar in the next snapshot
    * If a community "receives" several labels from communities in the previous snapshot, it selects the one of the community the most similar.


    [1]Greene, Derek, Donal Doyle, and Padraig Cunningham.
    "Tracking the evolution of communities in dynamic social networks."
    2010 international conference on advances in social networks analysis and mining. IEEE, 2010.

    :param dynNetSN: a dynamic network
    :param CDalgo: community detection to apply at each step. Can be a function returning a clustering, or the string "louvain" or "smoothedLouvain
    :param match_function: a function that gives a matching score between two communities (two sets of nodes). Default: jaccard
    :param threshold: a threshold for match_function below which communities are not matched
    :param labels: if True, the matching of affiliations is done using labels. If False, using an event graph.
    :return: DynCommunitiesSN
    """

    if CDalgo=="smoothedLouvain":
        dynPartitions = smoothed_louvain(dynNetSN)
    elif CDalgo=="louvain":
        dynPartitions = CD_each_step(dynNetSN,best_partition)
    else:
        dynPartitions = CD_each_step(dynNetSN, CDalgo)


    dynPartitions.create_standard_event_graph(threshold=threshold, score=match_function)

    if labels:
        dynPartitions._relabel_coms_from_continue_events(typedEvents=False)



    return dynPartitions

