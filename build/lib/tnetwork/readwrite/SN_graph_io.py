import networkx as nx
import os
import tnetwork as dn

from tnetwork.utils.bidict import *


def _detectAutomaticallyFormat(networkFile):
    format = networkFile.split(".")[1]
    return format


def _write_network_file(graph, out_name, out_format=None, data=False):
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
        nx.write_edgelist(graph, "%s.ncol" % (out_name), delimiter='\t')
    elif out_format == 'graphML':
        g = nx.write_graphml(graph, "%s.graphML" % (out_name))
    else:
        raise Exception("UNKNOWN FORMAT " + out_format)


def _read_network_file(in_name, in_format="", directed=False):
    """
    Read the graph representation on file using a user specified format

    :param in_name: pattern for the output filename
    :param in_format: output format. Accepted values: edgelist|ncol|gefx|gml|pajek\graphML
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
    elif in_format == 'graphML':
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


def read_snapshots_dir(inputDir, format=None):
    """
    Read a dynamic graph as a directory containing one file per snapshot. If the format is not provided, it is infered automatically from file extensions

    :param inputDir: directory where the files are located
    :param format: a string among edges(edgelist)|ncol|gefx|gml|pajek|graphML, by default, the extension of the files
    :return: a DynGraphSN object
    """


    anSnGraph = dn.DynGraphSN()
    files = os.listdir(inputDir)
    visibleFiles = [f for f in files if f[0] != "."]

    if format==None:
        format=_detectAutomaticallyFormat(visibleFiles[0])

    for f in visibleFiles:
        g = _read_network_file(inputDir + "/" + f, format)  # type:nx.Graph
        anSnGraph.add_snaphsot(int(os.path.splitext(f)[0]), g)


    return anSnGraph


def write_snapshots_dir(dynGraph, outputDir, format=None):
    """
    Write a dynamic graph as a directory containing one file for each snapshot. The format of files can be chosen
    :param dynGraph: a dynamic graph
    :param outputDir: address of the directory to write
    :param format: default edgelist, choose among edges(edgelist)|ncol|gefx|gml|pajek|graphML
    """
    if format==None:
        format="edges"
    allGraphs = dynGraph.snapshots()
    for g in allGraphs:
        _write_network_file(allGraphs[g],os.path.join(outputDir,str(g)),out_format=format)











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
    coms = bidict()
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
                    #     theDynCom.addBelonging(n,startTime,comID)
                    # if asTN:
                    #     theDynCom.addBelonging(n,comID,startTime) #belongings without end
                coms[frozenset(currentCom)]=comID
    return coms


def read_graph_link_stream(inputFile, toSN=True):
    """
    SOCIOPATTERN format
    this format is a variation of snapshots, in which all snapshots are in a single file, adapted for occasional observations
    at a high framerate (each SN is meaningless), Link stream
    """
    theDynGraph = dn.DynGraphSN()
    f = open(inputFile)

    for l in f:
        l = l.split("\t")
        date = int(l[0])
        n1 = l[1]
        n2 = l[2]
        if toSN:
            theDynGraph.add_interaction(n1,n2,date)
    return theDynGraph





