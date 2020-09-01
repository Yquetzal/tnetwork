import networkx as nx
from tnetwork import DynGraphSN
from tnetwork.dyn_graph.encodings import code_length_LS,code_length_SN_E,code_length_SN_M
import os
import tnetwork as tn
import pandas as pd
import json

import bidict
__all__ = ["read_snapshots", "write_snapshots", "write_snapshots_single_file","write_as_SN_E"]

def _detectAutomaticallyFormat(networkFile):
    format = networkFile.split(".")[1]
    return format


def _write_network_file(graph, out_name, out_format=None, data=False,weight=False):
    """
    Write the graph representation on file using a user specified format

    :param graph: networkx graph
    :param out_name: pattern for the output filename
    :param out_format: output format. Accepted values: edges(edgelist)|ncol|gefx|gml|pajek|graphML
    """

    if out_format==None:
        out_format="edges"
    os.makedirs(os.path.dirname(out_name), exist_ok=True)
    #print("writing graph of format " + out_format + " at " + out_name)
    if out_format == 'edges':
        nx.write_edgelist(graph, "%s.edges" % (out_name), data=data)
    elif out_format == 'gefx':
        nx.write_gexf(graph, "%s.gefx" % (out_name))
    elif out_format == 'gml':
        nx.write_gml(graph, "%s.gml" % (out_name))
    elif out_format == 'pajek':
        nx.write_pajek(graph, "%s.pajek" % (out_name))
    elif out_format == 'ncol':
            nx.write_edgelist(graph, "%s.ncol" % (out_name), delimiter='\t',data=weight)
    elif out_format == 'graphML' :
        g = nx.write_graphml(graph, "%s.graphml" % (out_name))
    else:
        raise Exception("UNKNOWN FORMAT " + out_format)


def _read_network_file(in_name, in_format="", directed=False):
    """
    Read the graph representation on file using a user specified format

    :param in_name: pattern for the output filename
    :param in_format: output format. Accepted values: edgelist|ncol|gefx|gml|pajek|graphML

    """

    if in_format == 'edges':
        if directed:
            g = nx.read_edgelist(in_name, create_using=nx.DiGraph())
        else:
            g = nx.read_edgelist(in_name, data=False)
    elif in_format == 'gefx':
        g = nx.read_gexf(in_name)
    elif in_format == 'gml':
        g = nx.read_gml(in_name)
    elif in_format == 'graphML' or in_format == 'graphml':
        g = nx.read_graphml(in_name)
        nodesInfo = g.nodes(data=True)
        if len(nx.get_node_attributes(g,"label"))>0:
            node2Label = {nodeid: data["label"].replace(" ","_") for (nodeid, data) in nodesInfo}
            g = nx.relabel_nodes(g, node2Label, copy=False)
    elif in_format == 'pajek':
        g = nx.read_pajek(in_name)
    elif in_format == 'ncol':
        g = nx.read_edgelist(in_name)
    else:
        raise Exception("UNKNOWN FORMAT " + in_format)
    return g


def read_snapshots(inputDir:str, format=None,frequency=1,prefix="") -> DynGraphSN:
    """
    Read as one file per snapshot
    
    Read a dynamic graph as a directory containing one file per snapshot. 
    If the format is not provided, it is infered automatically from file extensions

    :param inputDir: directory where the files are located
    :param format: a string among edges(edgelist)|ncol|gefx|gml|pajek|graphML, by default, the extension of the files
    :return: a DynGraphSN object
    """


    anSnGraph = tn.DynGraphSN(frequency=frequency)
    files = os.listdir(inputDir)
    visibleFiles = [f for f in files if f[0] != "."]

    if format==None:
        format=_detectAutomaticallyFormat(visibleFiles[0])

    for f in visibleFiles:
        g = _read_network_file(inputDir + "/" + f, format)  # type:nx.Graph
        anSnGraph.add_snapshot(int(os.path.splitext(f)[0][len(prefix):]), g)


    return anSnGraph


def write_snapshots(dynGraph:DynGraphSN, outputDir:str, format:str=None):
    """
    Write one file per snapshot
    
    Write a dynamic graph as a directory containing one file for each snapshot. The format of files can be chosen.
    
    :param dynGraph: a dynamic graph
    :param outputDir: address of the directory to write
    :param format: default edgelist, choose among edges(edgelist)|ncol|gefx|gml|pajek|graphML
    """
    if format==None:
        format="edges"
    allGraphs = dynGraph.snapshots()
    for g in allGraphs:
        _write_network_file(allGraphs[g],os.path.join(outputDir,str(g)),out_format=format)


def write_snapshots_single_file(dynGraph: DynGraphSN, outputFile: str,both_directions=False):
    """
    Write a single file with all edges from all steps

    Format:
    time n1 n2 1
    :param dynGraph: a dynamic graph
    :param outputFile: address of the file to write
    """
    f = open(outputFile,"w")
    allGraphs = dynGraph.snapshots()
    for t,g in allGraphs.items():
        for e in g.edges():
            weights=" "+str(1)
            f.write(str(t)+" "+str(e[0])+" "+str(e[1])+weights+"\n")
            if both_directions:
                f.write(str(t) + " " + str(e[1]) + " " + str(e[0]) + weights + "\n")
    f.close()


def _readStaticSNByCom(inputFile, commentsChar="#", nodeSeparator=" ", nodeInBrackets=False,
                       mainSeparator="\t", comIDposition=0, nodeListPosition=1):
    """
    nodeSeparator: characters that separate the list of nodes
    nodeInBrackets : if true, list of nodes in the community is [x y z] instead of just x y z
    mainSeparator : character used to separate comID from nodesIDS
    """

    #read community file from a static network
    # if asSN:
    #     theDynCom = dn.dynamicCommunitiesSN()
    # if asTN:
    #     theDynCom = dn.dynamicCommunitiesTN()
    coms = bidict.bidict()
    f = open(inputFile)

    for l in f:  # for each line
        currentCom = set()
        if not l[0] == commentsChar:  # if it is not a comment line
            l = l.rstrip().split("\t")
            comID = l[comIDposition]
            nodesIDs = l[nodeListPosition]
            if len(nodesIDs)>=1:
                # if nodeInBrackets:
                if "[" in nodesIDs:
                    nodesIDs = nodesIDs[1:-1]
                if ", " in nodesIDs:
                    nodeSeparator = ", "
                for n in nodesIDs.split(nodeSeparator):
                    currentCom.add(n)
                    # if asSN:
                    #     theDynCom.add_affiliation(n,startTime,comID)
                    # if asTN:
                    #     theDynCom.add_affiliation(n,comID,startTime) #belongings without end
                coms[frozenset(currentCom)]=comID
    return coms


# def read_graph_link_stream(inputFile:str) -> DynGraphSN:
#     """
#     Format used by SOCIOPATTERN
#
#     This format is a variation of snapshot_affiliations, in which all snapshot_affiliations are in a single file, adapted for occasional observations
#     at a high framerate (each SN is not really meaningful).
#
#     Format:
#     ::
#
#         DATE1	N1	N2
#         DATE1	N2	N3
#         DATE2	N1	N2
#         DATE3	N1	N2
#         DATE3	N2	N4
#         DATE3	N5	N2
#
#     :param inputFile: address of the file to read
#     :return: DynGraphSN
#     """
#     # theDynGraph = DynGraphSN()
#     # f = open(inputFile)
#     #
#     # for l in f:
#     #     l = l.split("\t")
#     #     date = int(l[0])
#     #     n1 = l[1]
#     #     n2 = l[2]
#     #     theDynGraph.add_interaction(n1,n2,date)
#     # return theDynGraph
#     return read_link_stream(inputFile,time_first_column=True)





def write_as_SN_E( graph:tn.DynGraphSN, filename):
    """

    :param filename:
    :return:
    """
    nodes = list(graph.cumulated_graph().nodes())
    dict_nodes = {n: i for i, n in enumerate(nodes)}
    times = list(graph.change_times())
    dict_times = {t: i for i, t in enumerate(times)}

    interactions = []
    for t,g in graph.snapshots().items():
        renamed = [[ dict_nodes[e[0]],dict_nodes[e[1]]] for e in g.edges()]
        interactions.append(renamed)
    json.dump({"nodes": nodes, "times": times, "interactions": interactions}, open(filename, 'w'))


