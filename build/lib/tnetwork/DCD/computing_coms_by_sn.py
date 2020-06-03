from tnetwork.DCD.pure_python.static_cd.louvain import *
from tnetwork.dyn_community.communities_dyn_sn import DynCommunitiesSN
from tnetwork.utils.community_utils import *
import tnetwork as tn
import multiprocessing as mp
import progressbar
import sys

# def CD_each_step_non_parallel(dynNetSN: tn.DynGraphSN, method=None):
#     """
#     Apply a community detection at each step
#
#     Compute snapshot_affiliations at each snapshot and return a dynamic community object with those.
#
#     :param dynNetSN: a dynamic network as a DynGraphSN
#     :param method: a function, the community detection algorithm to use. Default: the louvain algorithm. must return a list of set of nodes, or a dictionary comname:set of node
#     :return: a DynCommunitiesSN object
#     """
#     if method == None:
#         method = best_partition
#
#     coms = DynCommunitiesSN()
#
#     for SNt in dynNetSN.snapshots():
#         coms.set_communities(SNt)
#         if len(dynNetSN.snapshots(SNt).edges()) > 0:
#             partition = method(dynNetSN.snapshots(SNt))
#             if isinstance(partition, dict):  # louvain is returning a different format
#                 asNodeSets = affiliations2nodesets(partition)
#                 partition = [asNodeSets[c] for c in asNodeSets]
#             # for c in asNodeSets:
#             for nodes in partition:
#                 coms.add_community(SNt, nodes)
#     return coms

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


def CD_each_step(dynNetSN:tn.DynGraphSN,method=None,multithread=False):
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

    if multithread:
        procs_to_use = int(mp.cpu_count())
        print("Multi-thread, number of processors: ", procs_to_use)

        pool = mp.Pool(procs_to_use)

        allComs = pool.starmap_async(__compute_communities,[(SNt,dynNetSN.snapshots(SNt),method) for SNt in dynNetSN.snapshots()]).get()
        pool.close()
    else:
        bar = progressbar.ProgressBar(max_value=len(dynNetSN.snapshots()))
        count = 0
        bar.update(0)
        allComs = []
        for SNt in dynNetSN.snapshots():
            allComs.append(__compute_communities(SNt,dynNetSN.snapshots(SNt),method))
            bar.update(count)
            sys.stdout.flush()
            count += 1
        bar.update(count)
        sys.stdout.flush()

    unique_id=0
    for SNt,partition in allComs:
        coms.set_communities(SNt,{str(unique_id)+"_"+str(i):com for i,com in enumerate(partition)})
        unique_id+=1
    #for nodes in partition:
     #   coms.add_community(SNt, nodes)


    return coms


