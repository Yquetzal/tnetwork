from tnetwork.utils.community_utils import jaccard
from tnetwork.DCD import iterative_match
import tnetwork as tn
import networkx as nx
import numpy as np
import multiprocessing as mp
import time


def convert_stable_communities(persistant_coms,nb_coms=None,duration_min=0,duration_max=10000000):
    visu_blocks = tn.DynCommunitiesIG()
    if nb_coms==None:
        nb_coms = len(persistant_coms)
    for nodes,period,current_granularity,score in persistant_coms[:nb_coms]:
        if period.duration()>duration_min and period.duration()<duration_max:
            #we give a unique name to each community, since colors are attributed according to community names
            name = str(period.start()).zfill(5)+","+str(nodes)+","+str(current_granularity)
            visu_blocks.add_affiliation(nodes,name,period)
    return visu_blocks


def score_conductance(nodes,graph):
    weight="weight"

    if len(nodes)<4:
        return 0

    #optim
    if len(graph.edges)==0:
        return 0


    nodes_in_graph = nodes & set(graph.nodes())
    if len(nodes_in_graph)<4:
         return 0

    total_degree = nx.volume(graph, nodes_in_graph)
    threashold = np.sqrt(len(nodes_in_graph))
    if total_degree/len(nodes_in_graph)<threashold:
        return 0

    subgraph = nx.subgraph(graph, nodes_in_graph)
    avg_deg = np.average([val for (node, val) in subgraph.degree()])

    if avg_deg<np.sqrt(len(nodes_in_graph)):
        return 0

    try:

        inverse_cond = inverse_conductance(graph,nodes_in_graph,total_degree)
        return inverse_cond
    except:
        return 0


def MSSCD(dyn_graph, t_granularity = 1, t_persistance=3, t_quality=0.7, t_similarity=0.3, similarity=jaccard, CD="louvain", QC=score_conductance, weighted_aggregation=True, Granularity=None, start_time=None, elapsed_time=False,as_dyn_com=True):
    """
    Multi Scale Stable Community Detection

    Method described in [1].
    This method allows to find stable communities accross multiple temporal scales.
    In summary, it creates new snapshots by aggregating the existing ones. At each granularity level, it discover stabel communities by

    * 1) applying a community detection algorithm at each step
    * 2) keeping communities with the highest quality score as seeds
    * 3) Expand those seeds to neighbor snashots as long as they remain relevant accordin to the quality score
    * 4) keep as stable only communities that are present in several successive snapshots

    [1] Boudebza, S., Cazabet, R., Nouali, O., & Azouaou, F. (2019).
    Detecting Stable Communities in Link Streams at Multiple Temporal Scales.
    LEG workshop, @ECML-PKDD 2019

    :param dyn_graph: a dynamic graph
    :param t_granularity: (:math:`\\theta_\\gamma` min temporal granularity,scale to analyze
    :param t_persistance: :math:`\\theta_p` minimum number of successive occurences for the community to be persistant
    :param t_quality: :math:`\\theta_q` threashold of community quality
    :param t_similarity: :math:`\\theta_s` threashold of similarity between communities
    :param similarity: (CSS)function that give a score of similarity between communities. Default: jaccard
    :param CD: CD community detection algorithm. A function returning a set of set of nodes. By default, louvain algorithm
    :param QC: (QC)function to determine the quality of communities. Default: inverse of conductance
    :param weighted_aggregation: if true, the aggregation over time periods is done using weighted networks
    :param Granularity: (:math:`\Gamma`) can be used to replace the default scales. List of int.
    :param start_time: the date at which to start the analysis. Can be useful, for instance, to start analysis at 00:00
    :param as_dyn_com: if true, return a dynamic community object. If False, a custom format with quadruplets (nodes, duration, granularity, quality)
    :return: a dynamic community object (default) or a list of quadruplets, see parameter as_dyn_com
    """


    #set up the list of granularity/temporal scales to analyze
    if Granularity==None:
        Granularity = _studied_scales(dyn_graph, t_granularity, t_persistance)

    if isinstance(Granularity, int):
        Granularity = [Granularity]

    if start_time==None:
        start_time = dyn_graph.snapshots_timesteps()[0]

    persistant_coms = [] #C

    times={}
    start_timer = time.time()

    #for each granularity level
    for current_granularity in Granularity:


        #Aggregate the graph WITH or WITHOUT weights
        pre_computed_snapshots = dyn_graph.aggregate_sliding_window(t_start=start_time, bin_size=current_granularity,weighted=weighted_aggregation)

        seeds = _seed_discovery(pre_computed_snapshots, current_granularity, CD, QC, t_quality)
        nb_good_seeds = len(seeds)

        seeds = _seed_pruning(seeds, similarity, t_similarity, persistant_coms)

        while len(seeds)>0:
            seed_expansion(seeds.pop(0),current_granularity,t_quality,t_persistance,t_similarity,QC,similarity,pre_computed_snapshots,persistant_coms)


        print("------- granularity (gamma): ", current_granularity," | ","# good seeds: ",nb_good_seeds,"# persistent communities found (total): ",len(persistant_coms))

        duration = time.time() - start_timer
        start_timer = time.time()
        times[current_granularity]=duration
        #print(duration)

    times["total"] = sum([v for x,v in times.items()])
    persistant_coms = sorted(persistant_coms,key=lambda x: x[3],reverse=True)

    if as_dyn_com:
        persistant_coms = convert_stable_communities(persistant_coms)
    if elapsed_time:
        return (persistant_coms,times)
    return persistant_coms




def inverse_conductance(G,S,volume_S=None):
    weight="weight"
    T = set(G) - set(S)
    if len(T) == 0: #if all nodes in the commmunity, bad conductance (avoid /0)
        return 0

    num_cut_edges = nx.cut_size(G, S, T, weight=weight)
    if volume_S==None:
        volume_S = nx.volume(G, S, weight=weight)


    volume_T = nx.volume(G, T, weight=weight)
    volume_T = volume_T+len(T) #If only a few nodes outside the community, poor score (trivial solution),
    #but if many nodes outside the community, return good score. And avoid /0

    return 1- num_cut_edges / min(volume_T,volume_S)

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
        #if interesting_node in tracked_nodes:
         #   print("-",t,current_t, "score ", the_score)
        if the_score >= t_quality:
            #print("mm ",t_quality,the_score,current_t,t,backward)
            to_return.append((current_t, the_score))
            similar_com = True
        if backward:
            i = i - 1
        else:
            i = i + 1
    return to_return


def seed_contained_in_persistent_com(seed_nodes, persistent_com_nodes, seed_time, persistent_com_period, similarity, t_similarity):
    return persistent_com_period.contains_t(seed_time) and similarity(seed_nodes,persistent_com_nodes) > t_similarity

def _studied_scales(dyn_graph, t_granularity, t_persistance):
    G_duration = dyn_graph.snapshots_timesteps()[-1] - dyn_graph.snapshots_timesteps()[0]
    a_temporal_scale = int(G_duration / t_persistance)  # \gamma
    all_scales = []  # \Gamma
    while a_temporal_scale > t_granularity:
        all_scales.append(a_temporal_scale)
        a_temporal_scale = int(a_temporal_scale / 2)
    return all_scales


def __find_interesting_CC(t,g):
    interesting_connected_com = nx.connected_components(g)
    interesting_connected_com = [x for x in interesting_connected_com if len(x) >= 3]
    return (t,interesting_connected_com)

def __compute_quality(QC,cID, nodes,current_graph):
    quality = QC(nodes, current_graph)
    return(cID,nodes,quality)

def _seed_discovery(pre_computed_snapshots, current_granularity, CD, QC, t_quality):

    seeds = []

    #compute communities at each step
    dyn_coms = iterative_match(pre_computed_snapshots, CDalgo=CD,match_function=None)  # ,CDalgo=infomap_communities)

    #We add connected components, avoid degenerated results because of louvain who always split in communities,
    #even when there is an obvious community

    procs_to_use = mp.cpu_count()
    #procs_to_use = 1
    pool = mp.Pool(procs_to_use)
    all_CC = pool.starmap_async(__find_interesting_CC,[(t,g) for t,g in pre_computed_snapshots.snapshots().items()]).get()
    pool.close()

    #print("CC detection done")

    for t,cs in all_CC:
        for c in cs:
            dyn_coms.add_community(t, c)

    # for t, g in pre_computed_snapshots.snapshots().items():
    #     interesting_connected_com = nx.connected_components(g)
    #     interesting_connected_com = [x for x in interesting_connected_com if len(x) >= 3]
    #     for c in interesting_connected_com:
    #         dyn_coms.add_community(t, c)


    # computing quality for each com





    for t, coms in dyn_coms.snapshots.items():
        current_graph = pre_computed_snapshots.snapshots(t)

        # pool = mp.Pool(procs_to_use)
        # all_qualities = pool.starmap_async(__compute_quality,
        #                                    [(QC,cID, nodes, current_graph) for cID, nodes in coms.items()]).get()
        # pool.close()
        #
        # for cID, nodes,quality in all_qualities:
        #     seeds.append((t, cID, frozenset(nodes), quality,
        #               current_granularity))  ##structure of items in coms_and_qualities:  (t,cID,frozenset(nodes),quality,granularity)
        for cID, nodes in coms.items():
            quality = QC(nodes, current_graph)
            if quality>=t_quality:
                seeds.append((t, cID, frozenset(nodes), quality,
                          current_granularity))  ##structure of items in coms_and_qualities:  (t,cID,frozenset(nodes),quality,granularity)
    #print("quality computation done")

    seeds.sort(key=lambda x: x[3], reverse=True)

    return seeds

def _seed_pruning(S, CSS, t_similarity, C):
    for nodes, period, gran, score in C:  # for each already save community
        # keep in the list of seeds those that are in a different period or that are sufficiently different, compared with the current one
        S = [s for s in S if
                 not seed_contained_in_persistent_com(nodes, s[2], s[0], period, similarity=CSS,
                                                      t_similarity=t_similarity)]
    return S

def seed_expansion(seed,granularity,t_quality,t_persistance,t_similarity,QC,CSS,pre_computed_snapshots,C):
    # Find recursively snapshots in which this community still makes sense
    similars = []
    this_seed_nodes = seed[2]

    similars += _track_one_community(this_seed_nodes, seed[0], pre_computed_snapshots, score=QC,
                                     t_quality=t_quality, backward=True)
    similars.reverse()
    similars += [(seed[0], seed[3])]
    similars += _track_one_community(this_seed_nodes, seed[0], pre_computed_snapshots, score=QC,
                                     t_quality=t_quality)

    #if the community is stable, i.e., makes sense more than t_persistance steps
    if len(similars) >= t_persistance:
        #print("----------------")
        similars = [similars]  # for genericity, we want to be able to deal with non-continuous intervals
        inter_presence = tn.Intervals([(sim[0][0], sim[-1][0] + granularity) for sim in similars])

        # check that a similar community has not already been found
        redundant = False
        for nodes, period, gran, score in C:

            # if the communities are similar and one of them has at least half of its duration included in the other
            if CSS(this_seed_nodes, nodes) > t_similarity and inter_presence.intersection(
                    period).duration() > 0.5 * min([inter_presence.duration(), period.duration()]):
                redundant = True
                break

        # If community not redundant, we compute its quality and add it to the list of communities
        if not redundant:
            #print(similars)

            sum_quality = 0
            for stable in similars:
                sum_quality += sum([1 - (x[1]) for x in stable])

            C.append((this_seed_nodes, inter_presence, granularity, sum_quality))

