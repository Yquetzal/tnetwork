import tnetwork as tn
import sklearn.metrics
import scipy
import statistics
from tnetwork.utils.community_utils import jaccard
import networkx as nx


def computeNetworkStability(dynNet):
    """

    :param dynNet:
    :return:
    """
    ts = dynNet.snapshot_affiliations().keys()
    sns = dynNet.snapshot_affiliations().values()
    fractionChange = []
    graphBefore = sns[0]
    for i in range(1, len(ts)):
        graphCurrent = sns[i]
        edgesBefore = {frozenset(x) for x in graphBefore.edges}
        edgesCurrent = {frozenset(x) for x in graphCurrent.edges}

        difference = edgesBefore.symmetric_difference(edgesCurrent)

        fractionChange.append(len(difference))
        graphBefore = graphCurrent
    return fractionChange