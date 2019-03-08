from tnetwork.DCD.pure_python.static_cd.louvain import *
from tnetwork.dyn_community.communities_dyn_sn import DynamicCommunitiesSN
from tnetwork.utils.community_utils import *


def iterative_louvain(dynNetSN):
    """
    Compute snapshots according to the louvain algorithm at each step
    :param dynNetSN: a dynamic network
    :return: a dynamic community object
    """
    coms = DynamicCommunitiesSN()
    for SNt in dynNetSN.snapshots():
        coms.add_empy_sn(SNt)
        if len(dynNetSN.snapshots(SNt).edges())>0:
            partition = best_partition(dynNetSN.snapshots(SNt))
            asNodeSets = affiliations2nodesets(partition)
            for c in asNodeSets:
                coms.add_community(SNt, asNodeSets[c])
    return coms


def smoothed_louvain(dynNetSN):
    """
    Compute snapshots iteratively by starting a louvain algorithm at each step with the previous snapshots as seeds
    :param dynNetSN:
    :return:a dynamic community object
    """
    coms = DynamicCommunitiesSN()
    previousPartition = None
    for SNt in dynNetSN.snapshots():
        currentSN = dynNetSN.snapshots(SNt)

        if previousPartition!=None:
            #remove from the partition nodes that disappeared
            disappearedNodes = set(previousPartition.keys())-set(currentSN.nodes())
            for n in disappearedNodes:
                previousPartition.pop(n)

            #add to the partition nodes that appeared
            addedNodes = set(currentSN.nodes())-set(previousPartition.keys())
            maxCom = max(previousPartition.values())
            for n in addedNodes:
                maxCom+=1
                previousPartition[n]=maxCom



        partition = best_partition(currentSN,   partition=previousPartition)
        asNodeSets = {}

        for n,c in partition.items():
            asNodeSets.setdefault(c,set()).add(n)

        for c in asNodeSets:
            coms.add_community(SNt, asNodeSets[c])
        previousPartition=partition

    return coms