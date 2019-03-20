from tnetwork.DCD.pure_python.static_cd.louvain import *
from tnetwork.dyn_community.communities_dyn_sn import DynCommunitiesSN
from tnetwork.utils.community_utils import *
import tnetwork as tn


def CD_each_step(dynNetSN:tn.DynGraphSN,method=None):
    """
    Apply a community detection at each step

    Compute snapshot_affiliations at each snapshot and return a dynamic community object with those.

    :param dynNetSN: a dynamic network as a DynGraphSN
    :param method: a function, the community detection algorithm to use. Default: the louvain algorithm. must return a list of set of nodes, or a dictionary comname:set of node
    :return: a DynCommunitiesSN object
    """
    if method==None:
        method = best_partition

    coms = DynCommunitiesSN()
    for SNt in dynNetSN.snapshots():
        coms.add_empty_sn(SNt)
        if len(dynNetSN.snapshots(SNt).edges())>0:
            partition = method(dynNetSN.snapshots(SNt))
            if isinstance(partition,dict): #louvain is returning a different format
                asNodeSets = affiliations2nodesets(partition)
                partition = [asNodeSets[c] for c in asNodeSets]
            #for c in asNodeSets:
            for nodes in partition:
                coms.add_community(SNt, nodes)
    return coms


def smoothed_louvain(dyn_graph):
    """
    Apply the smoothed louvain method

    Compute snapshot_affiliations iteratively by starting a louvain algorithm at each step with the previous snapshot_affiliations as seeds

    :param dyn_graph: DynGraphSN
    :return:a DynCommunitiesSN
    """
    coms = DynCommunitiesSN()
    previousPartition = None
    for SNt in dyn_graph.snapshots():
        currentSN = dyn_graph.snapshots(SNt)
        if len(currentSN.edges())==0:
            coms.add_empty_sn(SNt)
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


            partition = best_partition(currentSN,   partition=previousPartition)
            asNodeSets = {}

            for n,c in partition.items():
                asNodeSets.setdefault(c,set()).add(n)

            for c in asNodeSets:
                coms.add_community(SNt, asNodeSets[c])
            previousPartition=partition

    return coms