from tnetwork.DCD.computing_coms_by_sn import *
import time
from tnetwork.utils.community_utils import _jaccard



# def _matchAll(oldc, newc, mt):
#     """
#
#     :param oldc:  list of communities defined as dic {cID:set of nodesID}
#     :param newc:  list of communities defined as dic {cID:set of nodesID}
#     :param mt:
#     :return: dic {newC:oldC} communities not matched are missing
#     """
#     coms_matched = set()
#     for c in oldc:  # for each of the new communities
#         for cd in newc:  # for each of the old communities
#             jaccard = _jaccard(oldc[c],newc[cd])
#
#             if jaccard >= mt:  # check if this jaccard is above threashold
#                 coms_matched.add((c,cd))
#     return coms_matched  # return dic {newC:oldC} communities not matched are missing
#
#
# def _build_matches(partitions, mt):
#     coms = partitions.communities()
#
#     for i in range(len(coms) - 1):  # for each date taken in chronological order
#         tOfSN = coms.iloc[i]
#         nextTOfSN = coms.iloc[i + 1]
#
#         oldc = partitions.communities(tOfSN)
#         newc = partitions.communities(nextTOfSN)
#         matched = _matchAll(oldc.inv, newc.inv, mt)  # find the best match for each new commmunity
#
#         for c in matched:  # c is the oldest community
#             partitions.events.add_event((tOfSN, c[0]), (nextTOfSN, c[1]), tOfSN, nextTOfSN, type="unknown")

def simple_matching(dynNetSN, mt=0.3, CDalgo="louvain", labels=True):
    """
    This algorithm is based on the one by Greene et al. using the louvain algorithm for detection at each step and the Jaccard coefficent to evaluate the similarity
    of snapshots.
    :param dynNetSN: a dynamic network
    :param mt: a minimum threashold for jaccard
    :param CDalgo: can be "louvain" or "smoothedLouvain"
    :param runningTime:
    :param labels: if True, the matching of snapshots is done using labels. If False, using an event graph.
    :return:
    """


    if CDalgo=="louvain":
        dynPartitions = iterative_louvain(dynNetSN)
    if CDalgo=="smoothedLouvain":
        dynPartitions = smoothed_louvain(dynNetSN)




    #_build_matches(dynPartitions, mt)
    dynPartitions.create_standard_event_graph(threshold=mt,score=_jaccard)

    if labels:
        dynPartitions.relabel_coms_from_continue_events(typedEvents=False)
    else:
        dynPartitions.create_standard_event_graph()



    return dynPartitions

