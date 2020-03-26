import tnetwork as tn
import os
import networkx as nx
from matlab import engine
import time
import io
import scipy.io
from tnetwork.readwrite.SN_graph_io import _write_network_file
from tnetwork.utils.community_utils import affiliations2nodesets


#####
#This algorithm suffer from several problems, the code is slow and has some peculiarities that makes it hard to run
#####
def _runMatlabCode(dummy_coms_files, graphs_files, T,ouput_file):

    dir = os.path.dirname(__file__)
    visuAddress = os.path.join(dir, "DYNMOGA2015b-2")

    print("starting matlab engine")
    eng = engine.start_matlab()
    eng.addpath(visuAddress, nargout=0)
    print("matlab engine started successfully")
    start_time = time.time()

    out = io.StringIO()
    err = io.StringIO()
    #(S, Q) = eng.genlouvain('file.mat', nargout=2)
    try:
        eng.run_DYNMOGA(dummy_coms_files,graphs_files,T,ouput_file, stdout=out, stderr=err,nargout=0)
    except:
        print(err.getvalue())
        print(out.getvalue())


    print("matlab code ran successfully")

    #print(err.getvalue())

    duration = time.time() - start_time

    return(duration)

def _create_and_clean_directory(dir):

    if not os.path.exists(dir):
        os.makedirs(dir, exist_ok=True)
    else:
        filelist = [f for f in os.listdir(dir)]
        for f in filelist:
            os.remove(os.path.join(dir, f))

def _write_for_dynmoga(dynGraph: tn.DynGraphSN, outputDir: str):
    """
    """
    _create_and_clean_directory(outputDir)

    dyn_graph_normalized,dic_nodes,dic_time = dynGraph.normalize_to_integers(nodes_start_at=1,time_start_at=1)

    for i in dic_time.keys():
        path = os.path.join(outputDir,"nets.t0"+str(i)+".edges")
        nx.write_edgelist(dyn_graph_normalized.snapshots(i),path ,data=False)

        f = open(os.path.join(outputDir, "coms.t0" + str(i) + ".comm1"),"w+")
        #for i,n in enumerate(dyn_graph_normalized.snapshots(i).nodes):
        for j, n in enumerate(list(dic_nodes.keys())):
            f.write(str(n)+" "+str(j+1  )+"\n")
        f.close()


    return dic_nodes,dic_time


def _load_dynmoga(file, dic_nodes, dic_times, dyn_graph):

    to_return = tn.DynCommunitiesSN()
    res = scipy.io.loadmat(file)
    coms = res["Z1"]

    coms = zip(*coms)
    for i, partition in enumerate(coms):
        real_nodes = dyn_graph.snapshots(dic_times[i+1]).nodes
        part_temp = {dic_nodes[i+1]:partition[i] for i in range(len(dic_nodes)) if  dic_nodes[i+1] in real_nodes}
        part_temp = affiliations2nodesets(part_temp)
        to_return.set_communities(dic_times[i+1],part_temp)
    return to_return

def dynmoga(dynGraph: tn.DynGraphSN,elapsed_time=False):
    """
    Dynmoga Algorithm

    Requires Matlab

    :param dynGraph:
    :param elapsed_time:
    :return:
    """
    dir = os.path.dirname(__file__)
    dir = os.path.join(dir,"temp","dynmoga")

    dic_nodes,dic_times = _write_for_dynmoga(dynGraph, dir)

    T = len(dynGraph.snapshots())

    output_file = os.path.join(dir,"dynmoga_output.mat")
    duration = _runMatlabCode(os.path.join(dir, "coms"), os.path.join(dir, "nets"), T, output_file)

    start = time.time()
    #load_address = "/Users/cazabetremy/Documents/GitHub/tnetwork/result_T_" + str(T) + "_bS_" + str(len(dic_nodes)) + ".mat"
    load_address = output_file

    print("+++++++++++++++")
    print(load_address)
    print(dic_times)
    dyn_coms = _load_dynmoga(load_address, dic_nodes, dic_times, dynGraph)

    dyn_coms.create_standard_event_graph()

    dyn_coms._relabel_coms_from_continue_events(typedEvents=False)

    duration2 = time.time() - start

    if elapsed_time:
        return dyn_coms,{"total":duration+duration2}
    return dyn_coms