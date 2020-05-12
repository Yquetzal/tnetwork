from tnetwork.DCD.computing_coms_by_sn import *
from tnetwork.utils.community_utils import jaccard, affiliations2nodesets
from tnetwork.DCD import iterative_match
import time
import progressbar
import networkx as nx
import sys


def _smoothed_graph(dyn_graph,alpha):
    """


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
            mitigated_graph= currentSN

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

                mitigated_graph = currentSN.copy()
                nx.set_edge_attributes(mitigated_graph,alpha,"weight")
                previousPartition = affiliations2nodesets(previousPartition)
                for c,nodes in previousPartition.items():
                    nodelist = list(nodes)
                    for i in range(len(nodelist)):
                        for j in range(i+1,len(nodelist)):
                            if mitigated_graph.has_edge(nodelist[i],nodelist[j]):
                                mitigated_graph[nodelist[i]][nodelist[j]]["weight"]+=(1-alpha)
                            else:
                                mitigated_graph.add_edge(nodelist[i],nodelist[j],weight=(1-alpha))


            partition = best_partition(mitigated_graph)
            #partitions = generate_dendrogram(currentSN, part_init = previousPartition)
            #partition = partition_at_level(partitions, len(partitions) - 1)

            asNodeSets = {}
            for n,c in partition.items():
                asNodeSets.setdefault(c,set()).add(n)

            for c in asNodeSets:
                coms.add_community(SNt, asNodeSets[c])
            previousPartition=partition
        bar.update(count)
        sys.stdout.flush()
        count += 1
    bar.update(count)
    sys.stdout.flush()
    return coms


def smoothed_graph(dynNetSN, match_function=jaccard, threshold=0.3, alpha=0.9,labels=True,elapsed_time=False):
    """
    Smoothed graph approach
    :param dynNetSN:
    :param match_function:
    :param threshold:
    :param alpha: parameter setting relative importance of past VS current graph. 1: only current, 0: only previous
    :param labels:
    :param elapsed_time:
    :return:
    """
    print("start smoothed graph")
    sys.stdout.flush()

    def temp_func(x):
        return _smoothed_graph(x,alpha)
    return iterative_match(dynNetSN,temp_func,match_function,threshold,labels,elapsed_time)