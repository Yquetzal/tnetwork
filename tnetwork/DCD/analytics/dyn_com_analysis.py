def computeNetworkStability(dynNet):
    ts = dynNet.snapshot_affiliations().keys()
    sns = dynNet.snapshot_affiliations().values()
    fractionChange = []
    graphBefore = sns[0]
    for i in range(1,len(ts)):
        graphCurrent = sns[i]
        edgesBefore = {frozenset(x) for x in graphBefore.edges}
        edgesCurrent = {frozenset(x) for x in graphCurrent.edges}


        difference = edgesBefore.symmetric_difference(edgesCurrent)

        fractionChange.append(len(difference))
        graphBefore = graphCurrent
    return fractionChange


