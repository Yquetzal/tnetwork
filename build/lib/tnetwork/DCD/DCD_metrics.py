import tnetwork as dn
import sklearn as sk


def computeByStep(dynamicCommunityReference:dn.dynamicCommunitiesSN,dynamicCommunityObserved:dn.dynamicCommunitiesSN):
    """
    :param dynamicCommunityReference:
    :param dynamicCommunityObserved:
    :return:
    """

    nodeIds=[]
    affilReference=[]


    comsToEvaluate = dynamicCommunityObserved.snapshot_affiliations()
    for t,(comNodes,comId) in dynamicCommunityReference.snapshot_affiliations().items():
        for n in comNodes:
            affilReference.append(comId)
            nodeIds.append(n)

        affilToEvaluate = [-1] * len(affilReference)

        for (comNodes,comId) in comsToEvaluate[t]:
            for n in comNodes:
                affilToEvaluate[nodeIds.index(n)]=comId


        sk.metrics.normalized_mutual_info_score(affilReference,affilToEvaluate)


