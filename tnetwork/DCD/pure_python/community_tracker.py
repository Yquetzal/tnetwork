from tnetwork.utils.community_utils import jaccard
from tnetwork.DCD import iterative_match
import tnetwork as tn
import networkx as nx

def node_threashold(nodes, network):
    if len(nodes)>=3:
        return True
    return False

def score_conductance(nodes,graph):
    if len(nodes)<4:
        return 1

    #optim
    if len(graph.edges)==0:
        return 1

    nodes_in_graph = nodes & set(graph.nodes())
    if len(nodes_in_graph)<4:
         return 1

    #graph_com = graph.subgraph(nodes_in_graph)
    #if not nx.is_connected(graph_com):
    #    return 1

    try:
        return nx.conductance(graph,nodes_in_graph)
    except:
        return 1

def _track_one_community(tracked_nodes, t, dyn_graph,score, t_quality,backward =False):
    to_return = []
    ts = list(dyn_graph.snapshots().keys())
    i = ts.index(t)
    similar_com = True

    limit = len(ts)
    if backward:
        limit = -1

    while (similar_com):
        similar_com = False
        next = i+1
        if backward:
            next = i-1
        if next == limit:
            return to_return
        current_t = ts[next]
        current_g = dyn_graph.snapshots(current_t)
        the_score = score(tracked_nodes, current_g)
        if the_score <= t_quality:
            to_return.append((current_t, the_score))
            similar_com = True
        if backward:
            i = i - 1
        else:
            i = i + 1

    return to_return

def _track_all_of_one_community(tracked_nodes, dyn_graph,score, t_quality,t_persistance):
    # VARIANT WITH ADDING ALL OTHER STABLE PERIODS
    # similars = _track_all_of_one_community(current_com[2], s_graph_current_granularity,score=good_community,t_quality=t_quality,t_persistance=t_persistance)

    to_return = []

    temp_sn = []
    for current_t,current_g in dyn_graph.snapshots().items():
        the_score = score(tracked_nodes, current_g)
        if the_score <= t_quality:
            temp_sn.append((current_t, the_score))
        else:
            if len(temp_sn)>=t_persistance:
                to_return.append(temp_sn)
            temp_sn =[]
    if len(temp_sn)>=t_persistance:
        to_return.append(temp_sn)

    return to_return


def seed_contained_in_persistent_com(seed_nodes, persistent_com_nodes, seed_time, persistent_com_period, similarity, t_similarity):
    return persistent_com_period.contains_t(seed_time) and similarity(seed_nodes,persistent_com_nodes) > t_similarity

def track_communities(dyn_graph, granularity, start_time=0, similarity=jaccard, good_community=score_conductance, t_persistance=3, t_quality=0.3, t_similarity=0.2,weighted_aggregation=False):
    """
    Proposed method to track communities
    :param dyn_graph:
    :param granularity: list of granularites at which we will search for communities
    :param start_time:
    :param similarity: function that give a score of similarity between communities
    :param good_community: function to determine what is a good community
    :param t_persistance: minimum number of successive occurences for the community to be persistant
    :param t_quality: threashold of quality
    :param t_similarity: threashold of similarity
    :return:
    """
    if isinstance(granularity,int):
        granularity = [granularity]

    persistant_coms = []
    all_graphs = {}
    all_coms = {}

    granularity = sorted(granularity,reverse=True)

    #for each granularity level
    for current_granularity in granularity:
        print("-------", current_granularity)
        seeds = []

        print("aggregating graph")

        #Aggregate the graph WITH or WITHOUT weights (on real data I checked, give better results without weights due to some very stronger weights between a small subset of nodes)
        s_graph_current_granularity = dyn_graph.aggregate_sliding_window(t_start=start_time, bin_size=current_granularity,weighted=weighted_aggregation)
        all_graphs[current_granularity]=s_graph_current_granularity

        print("computing communities")

        dyn_coms = iterative_match(s_graph_current_granularity)#,CDalgo=infomap_communities)
        all_coms[current_granularity] = dyn_coms

        print("computing quality for each com")

        for t,coms in dyn_coms.snapshots.items():
            current_graph = s_graph_current_granularity.snapshots(t)
            for cID,nodes in coms.items():
                quality = good_community(nodes,current_graph)
                seeds.append((t,cID,frozenset(nodes),quality,current_granularity)) ##structure of items in coms_and_qualities:  (t,cID,frozenset(nodes),quality,granularity)

        seeds.sort(key=lambda x: x[3],reverse=False)

        print("#nb seeds total",len(seeds))

        seeds = [c for c in seeds if c[3]<=t_quality]
        print("#nb good seeds",len(seeds))

        #filter out similar communities (same nodes in same period)
        for nodes,period,gran,score in persistant_coms: #for each already save community
             # keep in the list of seeds those that are in a different period or that are sufficiently different, compared with the current one
             #seeds = [c for c in seeds if not period.contains_t(c[0]) or similarity(c[2],current_com[2])<t_no_overlap]
            seeds = [c for c in seeds if not seed_contained_in_persistent_com(nodes, c[2], c[0], period, similarity=similarity,
                                                                              t_similarity=t_similarity)]
        print("#nb different seeds", len(seeds))

        print("tracking")

        #for every good seed in order of their quality score
        while len(seeds)>0:
            current_com = seeds.pop(0)

            #Find recursively snapshots in which this community still makes sense
            similars=[]

            similars += _track_one_community(current_com[2], current_com[0], s_graph_current_granularity,score=good_community,t_quality=t_quality,backward=True)
            similars +=[(current_com[0],current_com[3])]
            similars += _track_one_community(current_com[2],current_com[0],s_graph_current_granularity,score=good_community,t_quality=t_quality)

            #If the duration of the com is long enough, keep the community
            if len(similars)>=t_persistance:
                similars = [similars]  #for genericity, we want to be able to deal with non-continuous intervals
                inter_presence = tn.Intervals([(sim[0][0],sim[-1][0]+current_granularity) for sim in similars])

                #check that a similar community has not already been found
                redundant = False
                for nodes,period,gran,score in persistant_coms:

                    #if the communities are similar and one of them has at least half of its duration included in the other
                    if similarity(current_com[2],nodes)>t_similarity and inter_presence.intersection(period).duration()>0.5*min([inter_presence.duration(), period.duration()]):
                        redundant = True
                        break

                if not redundant:
                    #persistant_coms[current_com]=(inter_presence,sum([x[1] for x in similars]))
                    sum_quality = 0
                    for stable in similars:
                        sum_quality+= sum([1 - (x[1]) for x in stable])

                    persistant_coms.append((current_com[2],inter_presence,current_granularity,sum_quality))

                    #keep in the list of seeds those that are in a different period or that are sufficiently different, compared with the current one
                    seeds = [c for c in seeds if not seed_contained_in_persistent_com(current_com[2], c[2], c[0], inter_presence, similarity,
                                                                                      t_similarity)]

        print("# persistent communities", len(persistant_coms))

    persistant_coms = sorted(persistant_coms,key=lambda x: x[3],reverse=True)
    return (persistant_coms,all_graphs,all_coms)