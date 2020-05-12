from tnetwork.DCD.computing_coms_by_sn import *
from tnetwork.utils.community_utils import jaccard
from tnetwork.DCD import iterative_match
import time
import progressbar
import sys

def _smoothed_louvain(dyn_graph):
    """
    Apply the smoothed louvain method

    Compute snapshot_affiliations iteratively by starting a louvain algorithm at each step with the previous snapshot_affiliations as seeds

    :param dyn_graph: DynGraphSN
    :return:a DynCommunitiesSN
    """
    coms = DynCommunitiesSN()
    previousPartition = None
    bar = progressbar.ProgressBar(max_value=len(dyn_graph.snapshots()))
    count = 0
    bar.update(0)
    for SNt in dyn_graph.snapshots():
        currentSN = dyn_graph.snapshots(SNt)
        if len(currentSN.edges())==0:
            coms.set_communities(SNt)
            previousPartition=None
        else:
            if previousPartition!=None:
                #remove from the partition nodes that disappeared
                disappearedNodes = set(previousPartition.keys())-set(currentSN.nodes())
                for n in disappearedNodes:
                    previousPartition.pop(n)

                #add to the partition nodes that appeared
                addedNodes = set(currentSN.nodes())-set(previousPartition.keys())
                if len(previousPartition.values())==0:
                    maxCom=-1
                else:
                    maxCom = max(previousPartition.values())
                for n in addedNodes:
                    maxCom+=1
                    previousPartition[n]=maxCom


            #partition = best_partition(currentSN,   partition=previousPartition)
            partitions = generate_dendrogram(currentSN, part_init = previousPartition)
            partition = partition_at_level(partitions, len(partitions) - 1)
            asNodeSets = {}

            for n,c in partition.items():
                asNodeSets.setdefault(c,set()).add(n)

            for c in asNodeSets:
                coms.add_community(SNt, asNodeSets[c])
            previousPartition=partition_at_level(partitions, len(partitions) - 1)
        bar.update(count)
        sys.stdout.flush()
        count += 1
    bar.update(count)
    sys.stdout.flush()
    return coms

def smoothed_louvain(dynNetSN,match_function=jaccard, threshold=0.3, labels=True,elapsed_time=False):
    """
      Community Detection using smoothed louvain

      This algorithm is inspired by [1], ...

      :param dynNetSN: a dynamic network
      :param match_function: a function that gives a matching score between two snapshot_communities (two sets of nodes). Default: jaccard. If None, no matching is done
      :param threshold: a threshold for match_function below which snapshot_communities are not matched
      :param labels: if True, the matching of snapshot_affiliations is done using labels. If False, using an event graph.
      :return: DynCommunitiesSN
      """
    print("start smoothed louvain")
    sys.stdout.flush()

    return iterative_match(dynNetSN,_smoothed_louvain,match_function,threshold,labels,elapsed_time)