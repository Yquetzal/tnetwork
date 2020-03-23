from tnetwork.DCD.pure_python.static_cd.louvain import *
from tnetwork.dyn_community.communities_dyn_sn import DynCommunitiesSN
from tnetwork.utils.community_utils import *
import tnetwork as tn
import multiprocessing as mp


def CD_each_step_non_parallel(dynNetSN: tn.DynGraphSN, method=None):
    """
    Apply a community detection at each step

    Compute snapshot_affiliations at each snapshot and return a dynamic community object with those.

    :param dynNetSN: a dynamic network as a DynGraphSN
    :param method: a function, the community detection algorithm to use. Default: the louvain algorithm. must return a list of set of nodes, or a dictionary comname:set of node
    :return: a DynCommunitiesSN object
    """
    if method == None:
        method = best_partition

    coms = DynCommunitiesSN()

    for SNt in dynNetSN.snapshots():
        coms.set_communities(SNt)
        if len(dynNetSN.snapshots(SNt).edges()) > 0:
            partition = method(dynNetSN.snapshots(SNt))
            if isinstance(partition, dict):  # louvain is returning a different format
                asNodeSets = affiliations2nodesets(partition)
                partition = [asNodeSets[c] for c in asNodeSets]
            # for c in asNodeSets:
            for nodes in partition:
                coms.add_community(SNt, nodes)
    return coms

def __compute_communities(SNt,graph,method):
    #coms.set_communities(SNt)

    if len(graph.edges()) > 0:
        partition = method(graph)

        if isinstance(partition, dict):  # louvain is returning a different format
            asNodeSets = affiliations2nodesets(partition)
            partition = [asNodeSets[c] for c in asNodeSets]
    else:
        partition = []
    return (SNt,partition)


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

    procs_to_use = mp.cpu_count()
    #procs_to_use = 1

    #print("Multi-thread, number of processors: ", procs_to_use)

    pool = mp.Pool(procs_to_use)

    allComs = pool.starmap_async(__compute_communities,[(SNt,dynNetSN.snapshots(SNt),method) for SNt in dynNetSN.snapshots()]).get()
    #print("CD detection done")
    pool.close()

    unique_id=0
    for SNt,partition in allComs:
        coms.set_communities(SNt,{str(unique_id)+"_"+str(i):com for i,com in enumerate(partition)})
        unique_id+=1
    #for nodes in partition:
     #   coms.add_community(SNt, nodes)


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

    return coms