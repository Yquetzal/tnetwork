from tnetwork.DCD.computing_coms_by_sn import *
from tnetwork.utils.community_utils import jaccard, affiliations2nodesets
import progressbar
import networkx as nx
import sys
from tnetwork.DCD.algorithm_template import DCD_algorithm


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


def smoothed_graph(dynNetSN, alpha=0.9,match_function=jaccard,threshold=0.3,  **kwargs):
    """
    Smoothed graph approach

    This approach is a naive implementation of the idea proposed in [1].
    To sum up, at each snapshot, a new graph is create which is the combination of the graph at this step and
    a graph in which edges are present between any two nodes belonging to the same community in the previous step.
    Note than in the original paper, a method is proposed to greatly reduce the complexity of the solution, but this
    method is not implemented here.

    Alpha is a parameter to tune how important is the weight of the current topology compared with previous partition.

    The label attribution process is the same described in the paper XXX, see method simple_matching for details.

    Internally, it calls the simple_matching method, the same parameters can be passed to it.

    [1]Guo, C., Wang, J., & Zhang, Z. (2014).
    Evolutionary community structure discovery in dynamic weighted networks.
    Physica A: Statistical Mechanics and its Applications, 413, 565-576.

    :param dynNetSN:
    :param alpha: parameter setting relative importance of past VS current graph. 1: only current, 0: only previous

    :return:
    """
    matching_method = None
    if match_function != None:
        def matching_method(x):
            x.create_standard_event_graph(threshold=threshold, score=match_function)
            x._relabel_coms_from_continue_events(typedEvents=False, rename=False)
            return x

    def detection_method(x):
        return _smoothed_graph(x,alpha)
    return DCD_algorithm(dynNetSN, "smoothed_graph",detection=detection_method, label_attribution=matching_method,**kwargs)