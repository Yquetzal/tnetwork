from tnetwork.DCD.pure_python.static_cd.louvain import *
from tnetwork.dyn_community.communities_dyn_sn import DynCommunitiesSN
from tnetwork.utils.community_utils import *


def CD_each_step(dynNetSN,method=None):
    """
    Apply a community detection at each step

    Compute affiliations at each snapshot and return a dynamic community object with those.

    :param dynNetSN: a dynamic network
    :param method: a function, the community detection algorithm to use. Default: the louvain algorithm.
    :return: a DynCommunitiesSN object
    """
    if method==None:
        method = best_partition

    coms = DynCommunitiesSN()
    for SNt in dynNetSN.affiliations():
        coms.add_empty_sn(SNt)
        if len(dynNetSN.affiliations(SNt).edges())>0:
            partition = method(dynNetSN.affiliations(SNt))
            asNodeSets = affiliations2nodesets(partition)
            for c in asNodeSets:
                coms.add_community(SNt, asNodeSets[c])
    return coms


def smoothed_louvain(dynNetSN):
    """
    Apply the smoothed louvain method

    Compute affiliations iteratively by starting a louvain algorithm at each step with the previous affiliations as seeds

    :param dynNetSN:
    :return:a DynCommunitiesSN
    """
    coms = DynCommunitiesSN()
    previousPartition = None
    for SNt in dynNetSN.affiliations():
        currentSN = dynNetSN.affiliations(SNt)

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