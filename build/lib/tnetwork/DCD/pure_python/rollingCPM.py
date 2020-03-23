import networkx as nx
from operator import itemgetter
from collections import defaultdict
from tnetwork import DynCommunitiesSN,DynGraphSN
import time
import multiprocessing as mp


__author__ = "Giulio Rossetti, modif:Remy Cazabet"
__contact__ = "giulio.rossetti@gmail.com"
__website__ = "about.giuliorossetti.net"
__license__ = "BSD"



def __compute_communities( snt,graph,k):
    coms = list(_get_percolated_cliques(graph, k))
    return(snt,coms)


def rollingCPM(dynNetSN:DynGraphSN,k=3,elapsed_time=False):
    """

    This method is based on Palla et al[1]. It first computes overlapping snapshot_communities in each snapshot based on the
    clique percolation algorithm, and then match snapshot_communities in successive steps using a method based on the
    union graph.

    [1] Palla, G., Barabási, A. L., & Vicsek, T. (2007).
    Quantifying social group evolution.
    Nature, 446(7136), 664.

    :param dynNetSN: a dynamic network (DynGraphSN)
    :param k: the size of cliques used as snapshot_communities building blocks
    :param elapsed_time: if True, will return a tuple (communities,time_elapsed)
    :return: DynCommunitiesSN
    """

    DynCom = DynCommunitiesSN()
    old_communities = None
    old_graph = nx.Graph()

    graphs=dynNetSN.snapshots()

    time_Steps = {}
    start = time.time()
    step2 = start

    total_percolation = 0
    total_match = 0


    pool = mp.Pool(mp.cpu_count())

    allComs = pool.starmap_async(__compute_communities,
                                 [(SNt, dynNetSN.snapshots(SNt),k) for SNt in graphs]).get()
    print("CD detection done", len(allComs))
    pool.close()

    com_ids = dict()
    for (date,communitiesAtT) in allComs:
        #print("------------",date)
    #for (date, graph) in graphs.items():

        #communitiesAtT = list(_get_percolated_cliques(graph, k)) #get the percolated cliques (snapshot_affiliations) as a list of set of nodes
        step1 = time.time()
        total_percolation += step1 - step2
        for current_com in communitiesAtT:
            id = DynCom.add_community(date, current_com)
            com_ids[(date,current_com)]=id

        if old_communities == None: #if first snapshot
            old_graph = graphs[date]
            dateOld=date
            old_communities = communitiesAtT

        else:
            if len(communitiesAtT)>0: #if there is at least one community
                union_graph = nx.compose(old_graph, graphs[date]) #create the union graph of the current and the previous
                communities_union = list(_get_percolated_cliques(union_graph, k)) #get the snapshot_affiliations of the union graph


                jaccardBeforeAndUnion = _included(old_communities, communities_union) #we only care if the value is above 0
                jaccardUnionAndAfter = _included(communitiesAtT,communities_union) #we only care if the value is above 0

                already_assigned = set()
                for current_com in jaccardBeforeAndUnion: #for each community in the union graph
                    matched = []
                    born = []
                    killed = []

                    allJaccards = set()
                    for oldC in jaccardBeforeAndUnion[current_com]: #for communities included in it in t-1
                        for newC in jaccardUnionAndAfter[current_com]: # and t+1
                            if not oldC in already_assigned and not newC in already_assigned:
                                allJaccards.add(((oldC,newC),_singleJaccard(oldC,newC))) #compute jaccard between those

                    allJaccards = sorted(allJaccards, key=itemgetter(1), reverse=True)
                    sortedMatches = [k[0] for k in allJaccards] #list of pairs of communities in t-1 and t+1 ordered by decreasing jaccard

                    oldCToMatch = dict(jaccardBeforeAndUnion[current_com]) #get all coms before
                    newCToMatch = dict(jaccardUnionAndAfter[current_com]) #get all new coms
                    while len(sortedMatches)>0: #as long as there are couples of unmatched communities (t-1,t+1)included in the current com
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
                        #print("--",aMatch)
                        already_assigned.add(aMatch[0])
                        already_assigned.add(aMatch[1])

                        DynCom.events.add_event((dateOld, com_ids[(dateOld, aMatch[0])]), (date, com_ids[(date, aMatch[1])]), dateOld, date, "continue")

                    for kil in killed:#these are actual merge (unmatched snapshot_affiliations are "merged" to new ones)
                        for com in jaccardUnionAndAfter[current_com]:
                            DynCom.events.add_event((dateOld, com_ids[(dateOld, kil)]), (date, com_ids[(date, com)]), dateOld, date, "merged")

                    for b in born:#these are actual merge (unmatched snapshot_affiliations are "merged" to new ones)
                        for com in jaccardBeforeAndUnion[current_com]:
                            DynCom.events.add_event((dateOld, com_ids[(dateOld, com)]), (date, com_ids[(date, b)]), dateOld, date, "split")
            step2 = time.time()
            total_match += step2-step1

            old_graph = graphs[date]
            dateOld=date
            old_communities = communitiesAtT

    end = time.time()
    time_Steps["total"]=end-start
    time_Steps["CD"] = total_percolation
    time_Steps["match"] = total_match

    DynCom._relabel_coms_from_continue_events()

    if elapsed_time:
        return (DynCom,time_Steps)
    return(DynCom)

def _get_percolated_cliques(g,k):
    cliques = set(nx.algorithms.community.k_clique_communities(g,k))

    inclusions = _included_self(list(cliques))
    for including in inclusions:
        for included in inclusions[including].keys():
            cliques.remove(included)


    return cliques
# def _get_percolated_cliques(g,k):
#     perc_graph = nx.Graph()
#     cliques = [frozenset(c) for c in nx.find_cliques(g) if len(c) >= k]
#     perc_graph.add_nodes_from(cliques)
#     membership_dict = defaultdict(list)
#     for clique in cliques:
#         for node in clique:
#             membership_dict[node].append(clique)
#     for node in membership_dict:
#         print(node, len(membership_dict[node]))
#         if len(membership_dict[node])>2:
#             for i in range(len(membership_dict[node])):
#                 clique = membership_dict[node][i]
#                 for j in range(i,len(membership_dict[node])):
#                     adj_clique = membership_dict[node][j]
#                     if len(clique.intersection(adj_clique)) >= (k - 1):
#                         perc_graph.add_edge(clique, adj_clique)
#     for component in nx.connected_components(perc_graph):
#         yield (frozenset.union(*component))
# def _get_percolated_cliques(g, k):
#     perc_graph = nx.Graph()
#     cliques = [frozenset(c) for c in nx.find_cliques(g) if len(c) >= k]
#     print("found")
#     perc_graph.add_nodes_from(cliques)
#
#     # First index which nodes are in which cliques
#     membership_dict = defaultdict(list)
#     for clique in cliques:
#         for node in clique:
#             membership_dict[node].append(clique)
#
#     # For each clique, see which adjacent cliques percolate
#     print(len(cliques))
#     for clique in cliques:
#         print("pouet")
#         for adj_clique in _get_adjacent_cliques(clique, membership_dict):
#             if len(clique.intersection(adj_clique)) >= (k - 1):
#                 perc_graph.add_edge(clique, adj_clique)
#
#     # Connected components of clique graph with perc edges
#     # are the percolated cliques
#     for component in nx.connected_components(perc_graph):
#         yield(frozenset.union(*component))
#     print("done")

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

def _included_self( com_list):
    newmapped = {}
    for i in range(len(com_list)):
        c1 = com_list[i]
        for j in range(i+1,len(com_list)):
            c2 = com_list[j]
            if len(c1 & c2) == min(len(c1),len(c2)):
                if len(c1)>len(c2):
                    larger = c1
                    smaller=c2
                else:
                    larger = c2
                    smaller = c1
                newmapped.setdefault(larger,{})
                newmapped[larger][smaller]=len(smaller)
    return newmapped