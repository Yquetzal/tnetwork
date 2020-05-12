from tnetwork.DCD.computing_coms_by_sn import *
from tnetwork.utils.community_utils import jaccard
import time


def iterative_match(dynNetSN, CDalgo="louvain", match_function=jaccard, threshold=0.3, labels=True,elapsed_time=False):
    """
    Community Detection by iterative detection and matching

    This algorithm is inspired by the one proposed by Greene et al., [1] but additionally to the detection of match
    between snapshot_communities in consecutive snapshots, a post process assign labels to snapshot_communities, based on the
    following rules:

    * A community "send" its label to the community the most similar in the next snapshot
    * If a community "receives" several labels from snapshot_communities in the previous snapshot, it selects the one of the community the most similar.


    [1]Greene, Derek, Donal Doyle, and Padraig Cunningham.
    "Tracking the evolution of snapshot_communities in dynamic social networks."
    2010 international conference on advances in social networks analysis and mining. IEEE, 2010.

    :param dynNetSN: a dynamic network
    :param CDalgo: community detection to apply at each step. Can be a function returning a clustering, or the string "louvain" or "smoothedLouvain
    :param match_function: a function that gives a matching score between two snapshot_communities (two sets of nodes). Default: jaccard. If None, no matching is done
    :param threshold: a threshold for match_function below which snapshot_communities are not matched
    :param labels: if True, the matching of snapshot_affiliations is done using labels. If False, using an event graph.
    :return: DynCommunitiesSN
    """
    #print("start iterative_match, version: "+ str(CDalgo))
    time_Steps = {}
    start = time.time()
    if callable(CDalgo):
        dynPartitions = CDalgo(dynNetSN)
    #if CDalgo=="smoothedLouvain":
    #    dynPartitions = smoothed_louvain(dynNetSN)
    elif CDalgo=="louvain":
        dynPartitions = CD_each_step(dynNetSN,None)
    else:
        dynPartitions = CD_each_step(dynNetSN, CDalgo)

    step = time.time()
    time_Steps["CD"]=step-start
    if match_function!=None:
        dynPartitions.create_standard_event_graph(threshold=threshold, score=match_function)

        if labels:
            dynPartitions._relabel_coms_from_continue_events(typedEvents=False,rename=False)

    time_Steps["match"]=time.time()-step
    end = time.time()
    time_Steps["total"]=end-start

    #print("end iterative_match")

    if elapsed_time:
        return (dynPartitions,time_Steps)
    return dynPartitions

