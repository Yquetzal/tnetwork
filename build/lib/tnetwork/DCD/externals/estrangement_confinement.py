import networkx as nx
import tnetwork as tn
import leidenalg as la
import sortedcontainers
import time
import os
from tnetwork.DCD.externals.estrangement_master.Estrangement.estrangement import ECA
from tnetwork.readwrite.SN_graph_io import _write_network_file
from tnetwork.DCD.externals.utils import clean_create_dir, clear_file

from tnetwork.utils.community_utils import single_list_community2nodesets



def estrangement_confinement(dyn_graph:tn.DynGraphSN, tolerance=0.00001,convergence_tolerance=0.01,delta=0.05,elapsed_time=False,**kwargs):
    """
    Estrangement confinement

    Algorithm introduced in [1]. Uses original code.



    [1]Kawadia, V., & Sreenivasan, S. (2012).
    Sequential detection of temporal communities by estrangement confinement.
    Scientific reports, 2, 794.

    :param delta: see original article
    :param convergence_tolerance: see original article
    :param tolerance: see original article
    :return:
    """
    print("preprocessing estrangement confinement")

    #write files
    dir = os.path.dirname(__file__)
    dir_graphs = os.path.join(dir, "temp","estrangement","graph")
    result_file = os.path.join(dir, "temp","estrangement","result.log")
    clean_create_dir(dir_graphs)
    clear_file(result_file)

    all_nodes = set()
    allGraphs = dyn_graph.snapshots()
    for g in allGraphs.values():
        all_nodes = all_nodes.union(g.nodes())
    node_dict = {v:k for k,v in enumerate(all_nodes)}
    node_dict_reversed = {v:k for k,v in node_dict.items()}


    for i,g in enumerate(allGraphs.values()):
        nx.set_edge_attributes(g,1,"weight")
        g_copy = nx.relabel_nodes(g,node_dict,copy=True)
        _write_network_file(g_copy, os.path.join(dir_graphs, str(i)), out_format="ncol",weight=["weight"])
    start_time = time.time()
    print("calling external code")

    ECA(dir_graphs,result_file,tolerance=tolerance,convergence_tolerance=convergence_tolerance,delta=delta,**kwargs)
    print("postprocessing")
    duration = time.time() - start_time

    with open(result_file, 'r') as fr:
        result = eval(fr.read())
    to_return=tn.DynCommunitiesSN()
    for t,affils in result.items():
        partitions = tn.utils.community_utils.affiliations2nodesets(affils)
        #print(partitions)
        for c,nodes in partitions.items():
            partitions[c] = [node_dict_reversed[x] for x in nodes]
        to_return.set_communities(t,partitions)


    # to_return = tn.DynCommunitiesSN()
    # ts  =list(igraph_graphs.keys())
    # for i in range(len(coms)):
    #     t= ts[i]
    #     partition = single_list_community2nodesets(coms[i],igraph_graphs[t].vs["name"])
    #    to_return.set_communities(t,partition)

    print("sucessfully estrangement confinement")

    if elapsed_time:
        return (to_return,{"total":duration})
    return to_return