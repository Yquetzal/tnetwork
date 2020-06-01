import networkx as nx
import tnetwork as tn
import leidenalg as la
import sortedcontainers
import time

from tnetwork.utils.community_utils import single_list_community2nodesets
try:
    import igraph as ig
except ModuleNotFoundError:
    ig = None


def __from_graph_tool_to_nx(graph, node_map=None, directed=None):

    if directed is None:
        directed = graph.is_directed()

    if directed:
        tp = nx.DiGraph()
    else:
        tp = nx.Graph()

    tp.add_nodes_from([int(v) for v in graph.vertices()])
    tp.add_edges_from([(int(e.source()), int(e.target()))
                       for e in graph.edges()])
    if node_map:
        nx.relabel_nodes(tp, node_map, copy=False)

    return tp


def __from_nx_to_igraph(g, directed=None):
    """
    :param g:
    :param directed:
    :return:
    """

    if ig is None:
        raise ModuleNotFoundError(
            "Optional dependency not satisfied: install igraph to use the selected feature.")

    if directed is None:
        directed = g.is_directed()

    gi = ig.Graph(directed=directed)

    ##Two problems to handle:
    # 1)in igraph, names have to be str.
    # 2)since we can ask to compute metrics with found communities and the the original graph, we need to keep
    #the original nodes types in communities. Therefore we need to handle some transparent conversion for non-str nodes.
    if type(list(g.nodes)[0]) is str: #if nodes are string, no problem
        gi.add_vertices([n for n in g.nodes()])
        gi.add_edges([(u, v) for (u, v) in g.edges()])

    else:
        if set(range(len(g.nodes)))==set(g.nodes()):#if original names are well formed contiguous ints, keep this for efficiency.
            # Put these int as str with identitiers in the name attribute
            gi.add_vertices(len(g.nodes))
            gi.add_edges([(u, v) for (u, v) in g.edges()])
            gi.vs["name"]=["\\"+str(n) for n in g.nodes()]
        else: #if names are not well formed ints, convert to string and use the identifier to remember converting back to int
            #convert = {str(x):x for x in g.nodes()}
            gi.add_vertices(["\\"+str(n) for n in g.nodes()])
            gi.add_edges([("\\"+str(u), "\\"+str(v)) for (u, v) in g.edges()])
            #for k,v in convert.items():
            #    gi.vs["name"][k]=v


    edgelist = nx.to_pandas_edgelist(g)
    for attr in edgelist.columns[2:]:
        gi.es[attr] = edgelist[attr]

    return gi




def transversal_network_leidenalg(dyn_graph:tn.DynGraphSN, interslice_weight=1,elapsed_time=False):
    """
    Multiplex community detection reimplemented in leidenalg

    Algorithm described in [1]
    (see method `mucha_original` for more information)
    This function use the implementation in the leidenalg library instead of the original matlab implementation.
    It requires the installation of the leidenalg library (including igraph).
    It is usually slower than the original implementation (but does not require matlab)

    [1]Mucha, P. J., Richardson, T., Macon, K., Porter, M. A., & Onnela, J. P. (2010).
    Community structure in time-dependent, multiscale, and multiplex networks.
    science, 328(5980), 876-878.

    :param dyn_graph: dynamic network
    :param interslice_weight:
    :param elapsed_time:
    :return:
    """
    print("preprocessing transversal network leidenalg ")


    graphs = dyn_graph.snapshots()
    igraph_graphs = sortedcontainers.SortedDict()
    for t,g in graphs.items():
        igraph_graphs[t]=__from_nx_to_igraph(g)

    start_time = time.time()
    print("calling external code")

    coms,scores = la.find_partition_temporal(list(igraph_graphs.values()),
                               la.ModularityVertexPartition,
                               interslice_weight=interslice_weight,
                               vertex_id_attr="name")
    duration = time.time() - start_time
    print("postprocessing ")

    to_return = tn.DynCommunitiesSN()
    ts  =list(igraph_graphs.keys())
    for i in range(len(coms)):
        t= ts[i]
        partition = single_list_community2nodesets(coms[i],igraph_graphs[t].vs["name"])
        to_return.set_communities(t,partition)

    print("sucessfully finished transversal network leidenalg  ")

    if elapsed_time:
        return (to_return,{"total":duration})
    return to_return