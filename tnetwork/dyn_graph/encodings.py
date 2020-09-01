import numpy as np
__all__ = ["code_length_LS","code_length_SN_M","code_length_SN_E","code_length_IG"]
def _code_length_init(dyn_graph, nb_nodes=None, nb_unique_edges=None, nb_interactions=None, nb_time=None):
    if nb_interactions == None:
        nb_interactions = len(dyn_graph.interactions())

    if nb_time == None:
        nb_time = len(dyn_graph.change_times())

    if nb_nodes == None or nb_unique_edges == None:
        g_cumulated = dyn_graph.cumulated_graph()
        if nb_nodes==None:
            nb_nodes = len(g_cumulated.nodes())
        if nb_unique_edges==None:
            nb_unique_edges = len(g_cumulated.edges())
    time_encoding = np.log2(nb_time)
    node_encoding = np.log2(nb_nodes)
    edge_encoding = node_encoding * 2
    #print(nb_nodes,nb_unique_edges,nb_interactions,nb_time,time_encoding,edge_encoding)
    return nb_nodes,nb_unique_edges,nb_interactions,nb_time,time_encoding,edge_encoding

def code_length_LS(dyn_graph, **kwargs):
    nb_nodes,nb_unique_edges,nb_interactions,nb_time,time_encoding,edge_encoding = _code_length_init(dyn_graph,**kwargs)

    # (N1,N2)_T1_T2_STOP_(N2,N3)
    total_code = edge_encoding * nb_unique_edges + nb_interactions * time_encoding + time_encoding * nb_unique_edges
    #print("ls: ",edge_encoding * nb_unique_edges, nb_interactions * time_encoding,time_encoding * nb_unique_edges)

    return total_code

def code_length_SN_M(dyn_graph,**kwargs):
    """
    Time info should not be repeated
    2 versions:
    - edges are strongly repeated => matrix form
    :return:
    """
    nb_nodes, nb_unique_edges, nb_interactions, nb_time, time_encoding, edge_encoding = _code_length_init(dyn_graph,
                                                                                                          **kwargs)

    total_code_matrix = nb_unique_edges*nb_time+edge_encoding*nb_unique_edges+time_encoding*nb_time
    #print("sn_m: ",nb_unique_edges*nb_time,edge_encoding*nb_unique_edges,time_encoding*nb_time)
    return total_code_matrix

def code_length_SN_E(dyn_graph, **kwargs):
    """
    Time info should not be repeated
    2 versions:
    - edges are little repeated => each interaction encoded explicitly
    :return:
    """
    nb_nodes, nb_unique_edges, nb_interactions, nb_time, time_encoding, edge_encoding = _code_length_init(dyn_graph,
                                                                                                          **kwargs)
    #T1_(N1,N2)_(N3,N4)_STOP_T2_...
    total_code_edges = nb_interactions*edge_encoding + nb_time*time_encoding + nb_time*edge_encoding
    #print("sn_e: ",nb_interactions*edge_encoding,nb_time*time_encoding,nb_time*edge_encoding)
    return total_code_edges

def code_length_IG(dyn_graph, **kwargs):
    """

    :return:
    """
    nb_nodes, nb_unique_edges, nb_interactions, nb_time, time_encoding, edge_encoding = _code_length_init(dyn_graph,
                                                                                                          **kwargs)
    nb_periods = nb_interactions
    total_code = edge_encoding*nb_unique_edges + 2*nb_periods*time_encoding + nb_unique_edges*time_encoding
    #print("sn_ig: ",edge_encoding*nb_unique_edges,2*nb_periods*time_encoding,nb_unique_edges*time_encoding)

    return total_code
