from tnetwork.DCD.computing_coms_by_sn import *
from tnetwork.utils.community_utils import jaccard
from tnetwork.DCD import iterative_match
import time

def smoothed_louvain(dynNetSN, match_function=jaccard, threshold=0.3, labels=True,elapsed_time=False):
    """
      Community Detection using smoothed louvain

      This algorithm is inspired by [1], ...

      :param dynNetSN: a dynamic network
      :param match_function: a function that gives a matching score between two snapshot_communities (two sets of nodes). Default: jaccard. If None, no matching is done
      :param threshold: a threshold for match_function below which snapshot_communities are not matched
      :param labels: if True, the matching of snapshot_affiliations is done using labels. If False, using an event graph.
      :return: DynCommunitiesSN
      """

    return iterative_match(dynNetSN,"smoothedLouvain",match_function,threshold,labels,elapsed_time)