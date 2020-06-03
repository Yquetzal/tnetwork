from tnetwork.DCD.computing_coms_by_sn import *
import progressbar
import sys
from tnetwork.DCD.algorithm_template import DCD_algorithm


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

def smoothed_louvain(dynNetSN,match_function=jaccard,threshold=0.3,**kwargs):
    """
      Community Detection using smoothed louvain

      This algorithm is a naive implementation of the method proposed by [1]. The idea is that for each snapshots,
      the louvain algorithm is ran, but instead of being initialized with each node in its own community as usual, the partition
      obtained in the previous partition is used.

      The label attribution process is the same described in the paper XXX, see method simple_matching for details.

      Internally, it calls the simple_matching method, the same parameters can be passed to it.


      [1]Aynaud, T., & Guillaume, J. L. (2010, May).
      Static community detection algorithms for evolving networks.
      In 8th International symposium on modeling and optimization in mobile, Ad Hoc, and wireless networks (pp. 513-519). IEEE.

      :param dynNetSN: a dynamic network

      :return: DynCommunitiesSN
      """


    matching_method = None
    if match_function != None:
        def matching_method(x):
            x.create_standard_event_graph(threshold=threshold, score=match_function)
            x._relabel_coms_from_continue_events(typedEvents=False, rename=False)
            return x

    return DCD_algorithm(dynNetSN, "smoothed_louvain",detection=_smoothed_louvain, label_attribution=matching_method,**kwargs)