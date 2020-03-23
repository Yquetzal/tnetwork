from tnetwork.DCD.computing_coms_by_sn import *
from tnetwork.utils.community_utils import  affiliations2nodesets
import time
import networkx as nx
from tnetwork.DCD.pure_python.estrangement_master.estrangement.estrangement import *
import tnetwork as tn
from tnetwork.readwrite.SN_graph_io import _write_network_file
import json

#####################
####WARNING
##Currently does not work and is used as an external code, i.e., requires to write files on disk.
#######################
def _write(dynGraph:tn.DynGraphSN,dir):
    allGraphs = list(dynGraph.snapshots().values())

    all_nodes = set()
    for g in allGraphs:
        all_nodes.update(set(g.nodes))
    nodes_dict = {v: i for i, v in enumerate(all_nodes)}

    for i, g in enumerate(allGraphs):
        gg = nx.relabel_nodes(g, nodes_dict)
        nx.set_node_attributes(gg, 1, "weight")
        nx.write_edgelist(gg, os.path.join(dir, str(i + 1) + ".ncol"), data=["weight"])

    return nodes_dict
def _convert_to_dyncom(coms,nodes_dict):
    nodes_dict_inv = {v:k for k,v in nodes_dict.items()}
    to_return = tn.DynCommunitiesSN()

    for t,partition in coms.items():
        partition = affiliations2nodesets(partition)
        for comID in partition:
            partition[comID] = {nodes_dict_inv[n] for n in partition[comID]}

        to_return.set_communities(t,partition)
    return to_return


def estrangement_confinement(dynGraph:tn.DynGraphSN, tolerance=0.0001,convergence_tolerance=0.01,delta=0.05,minrepeats=1,increpeats=1,maxfun=500,write_stats=False):
    """

    """
    dir = os.path.dirname(__file__)
    dir = os.path.join(dir, "estrangement_master","data","temp")

    filelist = [f for f in os.listdir(dir)]
    for f in filelist:
        os.remove(os.path.join(dir, f))

    nodes_dict = _write(dynGraph,dir)
    #
    #
    result_file= os.path.join(dir,"results.log")
    coms = ECA(dir,result_file, tolerance,convergence_tolerance,delta,minrepeats,increpeats,maxfun,write_stats)

    dyn_com =_convert_to_dyncom(coms,nodes_dict)

    dyn_com.create_standard_event_graph(threshold=0.3)

    dyn_com._relabel_coms_from_continue_events(typedEvents=False)

    return dyn_com