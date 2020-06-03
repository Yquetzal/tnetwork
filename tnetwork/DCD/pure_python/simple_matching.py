from tnetwork.DCD.computing_coms_by_sn import *
from tnetwork.utils.community_utils import jaccard
from tnetwork.DCD.algorithm_template import DCD_algorithm


def iterative_match(dynNetSN, CDalgo="louvain", match_function=jaccard, threshold=0.3, elapsed_time=False,multithread=False):
    """
    Community Detection by iterative detection and matching

    This algorithm is inspired by the one proposed by Greene et al., [1] but additionally to the detection of match
    between communities in consecutive snapshots, a post process assign labels to communities, based on the
    following rules:

    * A community "send" its label to the community the most similar in the next snapshot
    * If a community "receives" several labels from communities in the previous snapshot, it selects the one of the community the most similar.


    [1]Greene, Derek, Donal Doyle, and Padraig Cunningham.
    "Tracking the evolution of snapshot_communities in dynamic social networks."
    2010 international conference on advances in social networks analysis and mining. IEEE, 2010.

    :param dynNetSN: a dynamic network
    :param CDalgo: community detection to apply at each step. Can be a function returning a clustering, or the string "louvain" or "smoothedLouvain
    :param match_function: a function that gives a matching score between two communities (two sets of nodes). Default: jaccard. If None, no matching is done
    :param threshold: a threshold for match_function below which snapshot_communities are not matched
    :param multithread: If true, run in parallel. Some bugs in macOs/windows.
    """
    #print("start iterative_match, version: "+ str(CDalgo))
    #if callable(CDalgo):
    #    dynPartitions = CDalgo(dynNetSN)
    #if CDalgo=="smoothedLouvain":
    #    dynPartitions = smoothed_louvain(dynNetSN)
    if CDalgo=="louvain":
        CDalgo=None
    cd_method = lambda x: CD_each_step(x,CDalgo,multithread)

    matching_method=None
    if match_function!=None:
        def matching_method(x):
            x.create_standard_event_graph(threshold=threshold, score=match_function)
            x._relabel_coms_from_continue_events(typedEvents=False,rename=False)
            return x


    return DCD_algorithm(dynNetSN,"no_smoothing",detection=cd_method,label_attribution=matching_method,elapsed_time=elapsed_time)

