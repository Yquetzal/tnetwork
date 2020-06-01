import tnetwork as tn
import sklearn
import sklearn.metrics
import scipy
import statistics
import networkx as nx
from tnetwork.DCD.analytics.onmi import onmi
import numpy as np

__all__ = ["longitudinal_similarity", "consecutive_sn_similarity", "similarity_at_each_step", "entropy_by_node","nb_node_change","quality_at_each_step","SM_N","SM_P","SM_L"]

def longitudinal_similarity(dynamicCommunityReference:tn.DynCommunitiesSN, dynamicCommunityObserved:tn.DynCommunitiesSN, score=None,convert_coms_sklearn_format=True):
    """
    Longitudinal similarity

    The longitudinal similarity between two dynamic clusters is computed by considering each couple (node,time) as an element belong to a cluster, a cluster containing therefore nodes in differnt times
    It takes into account the fact that the reference might by incomplete by removing from the partition to evaluate all (node,time) not present in the reference.

    :param dynamicCommunityReference: the dynamic partition used as reference (ground truth)
    :param dynamicCommunityObserved: the dynamic partition to evaluate (result of an algorithm)
    :param score: community comparison score, by default the adjsted NMI. (sklearn)
    :param convert_coms_sklearn_format: if the score expect in input clusters represented as in sklearn, True. if False, score will receive in input lists of sets of nodes
    :return: score
    """

    if score==None:
        score=lambda x,y : sklearn.metrics.adjusted_mutual_info_score(x,y,average_method="arithmetic")

    affilReference=[]
    affilToEvaluate=[]

    if convert_coms_sklearn_format:

        comsToEvaluate = dynamicCommunityObserved.snapshot_affiliations()

        #for each step
        for t,affils in dynamicCommunityReference.snapshot_affiliations().items():


                #for each node
                for n,comId in affils.items():
                    affilReference.append(str(list(comId)[0]))
                    if n in comsToEvaluate[t]:
                        affilToEvaluate.append(str(list(comsToEvaluate[t][n])[0]))
                    else:
                        print("node not in partition to evaluate: ",str(n)," ",str(t))
                        affilToEvaluate.append("-1")
    else:

        affilReference={}
        affilToEvaluate={}
        for t,coms in dynamicCommunityReference.snapshot_communities().items():
            all_nodes = set()
            for id,nodes in coms.items():
                node_sn = {(n,t) for n in nodes}
                all_nodes.update(node_sn)
                affilReference.setdefault(id,set()).update(node_sn)

            for id,nodes in dynamicCommunityObserved.snapshot_communities(t).items():
                node_sn = {(n,t) for n in nodes}

                affilToEvaluate.setdefault(id,set()).update(node_sn & all_nodes)

        affilReference = list(affilReference.values())
        affilToEvaluate = list(affilToEvaluate.values())


    return score(affilReference,affilToEvaluate)

def consecutive_sn_similarity(dynamicCommunity:tn.DynCommunitiesSN,score=None):
    """
       Similarity between partitions in consecutive snapshots.

        Compute the average of a similarity score between all pair of successive partitions

       :param dynamicCommunity: the dynamic partition to evaluate
       :param score: the score to use for computing the similarity between each pair of snapshots. default: Overlapping NMI
       :return: pair (list of scores, list of partition sizes (avg both partitions))
       """
    if score==None:
        score=onmi #We use onmi because the number of labels can be different
    scores=[]
    sizes=[]


    #for each step
    com_snapshots = list(dynamicCommunity.snapshot_communities().values())
    #print(com_snapshots)
    for i in range(len(com_snapshots)-1):

        partition_before = list(com_snapshots[i].values())
        partition_after = list(com_snapshots[i+1].values())

        elts_before = sum([len(x) for x in partition_before])
        elts_after = sum([len(x) for x in partition_after])

        scores.append(score(partition_before,partition_after))
        sizes.append((elts_after+elts_before)/2)

    return scores,sizes



def similarity_at_each_step(dynamicCommunityReference:tn.DynCommunitiesSN, dynamicCommunityObserved:tn.DynCommunitiesSN, score=None):
    """
    Compute similarity at each step

    It takes into account the fact that the reference might by incomplete. (remove from the observations all nodes/time not present in the reference)

    :param dynamicCommunityReference: the dynamic partition to use as reference
    :param dynamicCommunityObserved: the dynamic partition to evaluate
    :param score: score to use, default adjusted NMI
    :return: pair (list of scores, list of sizes)
    """

    if score==None:
        score=sklearn.metrics.adjusted_mutual_info_score
    scores=[]
    sizes=[]


    comsToEvaluate = dynamicCommunityObserved.snapshot_affiliations()

    #for each step
    for t,affils in dynamicCommunityReference.snapshot_affiliations().items():
        affilReference = []
        affilToEvaluate = []

        #for each node
        for n,comId in affils.items():
            affilReference.append(list(comId)[0])
            if n in comsToEvaluate[t]:
                affilToEvaluate.append(list(comsToEvaluate[t][n])[0])
            else:
                affilToEvaluate.append("-1")
        scores.append(score(affilReference,affilToEvaluate))
        sizes.append(len(affilReference))

    return scores,sizes




def quality_at_each_step(dynamicCommunities:tn.DynCommunitiesSN,dynamicGraph:tn.DynGraphSN, score=None):
    """
    Compute a community quality at each step

    :param dynamicCommunities: dynamic communities as SN
    :param score: score to use, default: Modularity
    :return: pair(scores, sizes)
    """

    if score==None:
        score=nx.algorithms.community.modularity
    scores=[]
    sizes=[]


    #for each step
    for t,affils in dynamicCommunities.snapshot_communities().items():
        g = dynamicGraph.snapshots(t)
        partition = list(affils.values())
        try:
            sc = score(g,partition)
            scores.append(sc)
        except:
            #print("problem to compute with partition: ",partition," nodes",g.nodes())
            scores.append(None)
        sizes.append(len(g.nodes))

    return scores,sizes

def nb_node_change(dyn_com:tn.DynCommunitiesSN):
    """
    Compute the total number of node changes

    Measure of smoothness at the level of nodes, adapated to evaluate glitches

    :param dyn_com: The dynamic community
    :return: total number of node changes
    """
    coms_by_nodes={}
    for t,coms in dyn_com.snapshot_communities().items():
        #print(t,coms)
        for com,nodes in coms.items():
            #print(n,com)
            for n in nodes:
                coms_by_nodes.setdefault(n,[com])
                if coms_by_nodes[n][-1]!=com:
                    coms_by_nodes[n].append(com)
    nb_changes = 0
    for n in coms_by_nodes:
        #print(n,coms_by_nodes[n])
        nb_changes+=len(coms_by_nodes[n])-1
    return nb_changes


# def entropy(dyn_com,sn_duration=1):
#     """
#     Compute the entropy.
#
#     Consider each community label as a data value. The probability of observing this data value is the frequency of a random node to belong to the corresponding community.
#
#     Interpretation: The less communities, the lower the score. The less homogeneous the community sizes, the lower the score.
#
#     This score does not take into account the order of the community changes.
#
#     Be careful, convert SN graph into IG.
#
#
#     :param dyn_com: dynamic community to evaluate, can be SN or IG
#     :param sn_duration: if graph is SN, used to
#     :return:
#     """
#     dc2 = dyn_com
#     fractions = []
#     if isinstance(dc2,tn.DynCommunitiesSN):
#         dc2 = dc2.to_DynCommunitiesIG(sn_duration=sn_duration)
#     for com,nodes in dc2.communities().items():
#         this_com_cumulated = 0
#         for n,times in nodes.items():
#             this_com_cumulated += times.duration()
#         fractions.append(this_com_cumulated)
#     sum_durations = sum(fractions)
#     fractions = [x/sum_durations for x in fractions]
#
#     return scipy.stats.entropy(fractions)

def entropy_by_node(dyn_com,sn_duration=1,fast_on_sn=False):
    """
    Compute the entropy by node.

    For each node, compute the shannon entropy of its labels. (always same label=min entropy, every step a new label=max entropy)
    return the average value for all nodes


    :param dyn_com: dynamic community to evaluate, can be SN or IG
    :param sn_duration: if graph is SN, used to discretize
    :return:
    """
    dc2 = dyn_com

    if not fast_on_sn:
        if isinstance(dc2,tn.DynCommunitiesSN):
            if sn_duration==1:
                dc2 = dc2._to_DynCommunitiesIG_fast()
            else:
                dc2 = dc2.to_DynCommunitiesIG(sn_duration=sn_duration)
    all_entropies = []
    for n,coms in dc2.affiliations().items():
        fractions = []

        for com,times in coms.items():
            fractions.append(times.duration())
        sum_durations = sum(fractions)
        fractions = [x/sum_durations for x in fractions]
        ent_this_node = scipy.stats.entropy(fractions)
        all_entropies.append(ent_this_node)

    return statistics.mean(all_entropies)

def SM_N(dyn_com):
    """
    Smoothness for nodes

    Inverse of the number of node changes
    :param dyn_com: dynamic partition
    :return: SM-N score
    """
    return 1/nb_node_change(dyn_com)

def SM_P(dyn_com):
    """
    Smoothness for partitions

    Averge of the NMI between successive snapshots
    :param dyn_com: dynamic partition
    :return: SM-P score
    """
    consecutive_NMIs = consecutive_sn_similarity(dyn_com)
    return np.average(consecutive_NMIs[0], weights=consecutive_NMIs[1])

def SM_L(dyn_com,sn_duration=1):
    """
    Smoothness for labels

    Inverse of the entropy by node
    :param dyn_com: dyanamic partition
    :param sn_duration: used to indicate the duration of snapshots if provided graph is a snapshot graph
    :return:  SM-L score
    """
    return 1/entropy_by_node(dyn_com,sn_duration=sn_duration)
