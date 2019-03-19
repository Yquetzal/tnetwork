import networkx as nx
from operator import itemgetter
from collections import defaultdict
from tnetwork import DynCommunitiesSN,DynGraphSN

__author__ = "Giulio Rossetti, modif:Remy Cazabet"
__contact__ = "giulio.rossetti@gmail.com"
__website__ = "about.giuliorossetti.net"
__license__ = "BSD"






def rollingCPM(dynNetSN:DynGraphSN,k=3):
    """

    This method is based on Palla et al[1]. It first computes overlapping snapshot_communities in each snapshot based on the
    clique percolation algorithm, and then match snapshot_communities in successive steps using a method based on the
    union graph.

    [1] Palla, G., Barabási, A. L., & Vicsek, T. (2007).
    Quantifying social group evolution.
    Nature, 446(7136), 664.

    :param dynNetSN: a dynamic network (DynGraphSN)
    :param k: the size of cliques used as snapshot_communities building blocks
    :return: DynCommunitiesSN
    """

    DynCom = DynCommunitiesSN()
    old_communities = None
    old_graph = nx.Graph()

    graphs=dynNetSN.snapshots()

    for (date, graph) in graphs.items():
        communitiesAtT = list(_get_percolated_cliques(graph, k)) #get the percolated cliques (snapshot_affiliations) as a list of set of nodes
        for c in communitiesAtT:
            DynCom.add_community(date, c)

        if old_communities == None: #if first snapshot
            old_graph = graph
            dateOld=date
            old_communities = communitiesAtT

        else:
            if len(communitiesAtT)>0: #if there is at least one community
                union_graph = nx.compose(old_graph, graph) #create the union graph of the current and the previous
                communities_union = list(_get_percolated_cliques(union_graph, k)) #get the snapshot_affiliations of the union graph

                jaccardBeforeAndUnion = _included(old_communities, communities_union) #we only care if the value is above 0
                jaccardUnionAndAfter = _included(communitiesAtT,communities_union) #we only care if the value is above 0


                for c in jaccardBeforeAndUnion: #for each community in the union graph
                    matched = []
                    born = []
                    killed = []

                    allJaccards = set()
                    for oldC in jaccardBeforeAndUnion[c]:
                        for newC in jaccardUnionAndAfter[c]:
                            allJaccards.add(((oldC,newC),_singleJaccard(oldC,newC))) #compute jaccard between candidates before and after
                    allJaccards = sorted(allJaccards, key=itemgetter(1), reverse=True)
                    sortedMatches = [k[0] for k in allJaccards]

                    oldCToMatch = dict(jaccardBeforeAndUnion[c]) #get all coms before
                    newCToMatch = dict(jaccardUnionAndAfter[c]) #get all new coms
                    while len(sortedMatches)>0: #as long as there are couples of unmatched snapshot_affiliations
                        matchedKeys = sortedMatches[0] #pair of snapshot_affiliations of highest jaccard
                        matched.append(matchedKeys) #this pair will be matched

                        del oldCToMatch[matchedKeys[0]] #delete chosen com from possible to match
                        del newCToMatch[matchedKeys[1]]
                        sortedMatches = [k for k in sortedMatches if len(set(matchedKeys) & set(k))==0] #keep only pairs of unmatched snapshot_affiliations

                    if len(oldCToMatch)>0:
                        killed.append(list(oldCToMatch.keys())[0])
                    if len(newCToMatch)>0:
                        born.append(list(newCToMatch.keys())[0])

                    for aMatch in matched:
                        DynCom.events.add_event((dateOld, DynCom._com_ID(dateOld, aMatch[0])), (date, DynCom._com_ID(date, aMatch[1])), dateOld, date, "continue")

                    for kil in killed:#these are actual merge (unmatched snapshot_affiliations are "merged" to new ones)
                        for com in jaccardUnionAndAfter[c]:
                            DynCom.events.add_event((dateOld, DynCom._com_ID(dateOld, kil)), (date, DynCom._com_ID(date, com)), dateOld, date, "merged")

                    for b in born:#these are actual merge (unmatched snapshot_affiliations are "merged" to new ones)
                        for com in jaccardBeforeAndUnion[c]:
                            DynCom.events.add_event((dateOld, DynCom._com_ID(dateOld, com)), (date, DynCom._com_ID(date, b)), dateOld, date, "split")

            old_graph = graph
            dateOld=date
            old_communities = communitiesAtT

    DynCom._relabel_coms_from_continue_events()

    return(DynCom)

def _get_percolated_cliques(g, k):
    perc_graph = nx.Graph()
    cliques = [frozenset(c) for c in nx.find_cliques(g) if len(c) >= k]
    perc_graph.add_nodes_from(cliques)

    # First index which nodes are in which cliques
    membership_dict = defaultdict(list)
    for clique in cliques:
        for node in clique:
            membership_dict[node].append(clique)

    # For each clique, see which adjacent cliques percolate
    for clique in cliques:
        for adj_clique in _get_adjacent_cliques(clique, membership_dict):
            if len(clique.intersection(adj_clique)) >= (k - 1):
                perc_graph.add_edge(clique, adj_clique)

    # Connected components of clique graph with perc edges
    # are the percolated cliques
    for component in nx.connected_components(perc_graph):
        yield(frozenset.union(*component))

def _get_adjacent_cliques(clique, membership_dict):
    adjacent_cliques = set()
    for n in clique:
        for adj_clique in membership_dict[n]:
            if clique != adj_clique:
                adjacent_cliques.add(adj_clique)
    return adjacent_cliques

def _singleJaccard(set1,set2):
    return float(len(set1 & set2))/float(len(set1 | set2))
# @todo: check. Deve restituire il secondo dizionario in ingresso con le chiavi coerenti con il primo (intersezione massima)

def _jaccard_similarity( oldc, newc,threashold=0):
    newmapped = {}
    for c in newc:
        newmapped[c]={}
        for cd in oldc:
            jaccard = float(len(c & cd))/float(len(c | cd))
            if jaccard>=threashold:
                newmapped[c][cd]=jaccard
    return newmapped

def _included( smallers, largers):
    newmapped = {}
    for larger in largers:
        newmapped[larger]={}
        for smaller in smallers:
            if len(smaller & larger) == len(smaller):
                newmapped[larger][smaller]=len(smaller)
    return newmapped