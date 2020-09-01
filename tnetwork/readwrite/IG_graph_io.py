import tnetwork as tn
import sortedcontainers
from tnetwork.utils import write_list_of_list
import json

__all__ = ["write_period_lists", "read_period_lists", "write_ordered_changes", "write_as_IG"]


def write_period_lists(theDynGraph:tn.DynGraphIG, fileOutput:str):
    """
    Write as list of periods

    Write an interval graph graph as a list of periods, for the graph, the nodes, and the edges

    Exemple of result:
    ::

        SG  0:100
        N   N1  0:10 50:60
        N   NODE_3  0:20 30:60
        E1  N1  NODE_3  5:10

    Means that the graph exists from time 0 to 100, it contains 2 nodes (N1 and NODE_3) that exist each over 2 intervals
    and one edge between those 2 nodes during the interval from 5 to 10

    :param theDynGraph: a dynamic graph
    :param fileOutput: the address of the file to write

    """
    toWrite = []
    toWrite.append(["SG", str(theDynGraph._start) + ":" + str(theDynGraph._end)])
    for (n, intervs) in theDynGraph.node_presence().items():
        toAdd = ["N",n]

        for interv in intervs.periods():
            toAdd += [str(interv[0])+":"+str(interv[1])]
        toWrite.append(toAdd)

    for ((n1,n2),intervs) in theDynGraph.interactions_intervals().items():
        toAdd = ["E", n1, n2]
        for interv in intervs.periods():
            toAdd += [str(interv[0])+":"+str(interv[1])]
        toWrite.append(toAdd)

    write_list_of_list(toWrite,fileOutput,sep="\t")


def read_period_lists(file_address:str):
    """
    Read as list of periods

    Read an interval graph as a list of periods, for the graph, the nodes, and the edges

    See write_IG for an explanation of the format

    :param file_address:

    """
    aDynGraph = tn.DynGraphIG()
    file = open(file_address)
    for line in file:
        parts = line.split("\t")

        if parts[0]=="SG":
            for period in parts[1:]:
                times = period.split(":")
                aDynGraph._start =int(times[0])
                aDynGraph._end = int(times[1])

        if parts[0]=="N":
            nodeName = parts[1]
            parts= parts[2:]
            for period in parts:
                times = period.split(":")
                start=int(times[0])
                end = int(times[1])
                aDynGraph.add_node_presence(nodeName, (start, end))

        if parts[0]=="E":
            n1 = parts[1]
            n2= parts[2]
            parts = parts[3:]
            for period in parts:
                times = period.split(":")
                start=int(times[0])
                end = int(times[1])
                aDynGraph.add_interaction(n1,n2, (start, end))
    return aDynGraph

def write_ordered_changes(dynNet:tn.DynGraphIG, fileOutput, dateEveryLine=False, nodeModifications=False, separator="\t", edgeIdentifier="l"):
    """
    Write as list of successive changes

    (use with caution, not tested recently)
    Write the dynamic network as a list of successive changes. There are several variants:

       * OML :ordered modif list with dates as #DATE and no nodes (Online Modification List)
       * OMLN : with nodes
       * OMLR : with repeated dates
       * OMLRN : nodes and repeated dates

    :param dynNet: dynamic network
    :param fileOutput: address of file to write
    :param dateEveryLine: if true, date is repeated for each modification (each line). If false, date modification is on its own line (#DATE) before the modifications happening at this date
    :param nodeModifications: write not only edges but also nodes modifications
    :param separator: choose a separator
    :param edgeIdentifier: character to differenciate edges from nodes.

    """
    if type(dynNet) is tn.DynGraphSN:
        dynNet = dynNet.toDynGraphTN(convertTimeToInteger=False)

    timeOfActions = sortedcontainers.SortedDict()
    #NOTE : can be easily optimized ! one complete check to add and to remove nodes...
    dataDicNodes={}
    if nodeModifications: #note that we add nodes before edges, so that nodes are added before there edges...
        dataDicNodes = dynNet.nodesD()

        for (n,intervs) in dataDicNodes.items():
            #times = self.nodes[n]
            for interv in intervs.periods():
                addDate = interv[0]

                #delDate = maxInterval(interv)
                timeOfActions.setdefault(addDate,[]).append("+n" + separator + str(n))

    dataDicEdges = dynNet.edgesD()

    for (e,intervs) in dataDicEdges.items():
        #print("e",e,intervs)
        #times = self.edges[e]
        for interv in intervs.periods():
            addDate = interv[0]
            delDate = interv[1]
            (node1, node2) = list(e)
            if not addDate in timeOfActions:
                timeOfActions[addDate] = []
            if not delDate in timeOfActions:
                timeOfActions[delDate] = []
            timeOfActions[addDate].append("+"+edgeIdentifier+separator + str(node1) + separator + str(node2))
            timeOfActions[delDate].append("-"+edgeIdentifier+separator + str(node1) + separator + str(node2))

    if nodeModifications:  # note that we remove nodes after edges,...
        for (n,intervs) in dataDicNodes.items():
            #times = self.nodes[n]
            for interv in intervs.periods():
                delDate = interv[1]

                if not delDate in timeOfActions:
                    timeOfActions[delDate] = []
                timeOfActions[delDate].append("-n" + separator + str(n))

    #(orderedKeys, orderedValues) = fromDictionaryOutputOrderedKeysAndValuesByKey(timeOfActions)
    toWrite = []
    for k in timeOfActions: #sorted because sorteddict
        if not dateEveryLine:
            toWrite.append(["#" + str(k)])
        for val in timeOfActions[k]:
            if dateEveryLine:
                val+=separator+str(k)
            toWrite.append([val])

    tn.write_list_of_list(toWrite, fileOutput, separator="\t")

def write_as_IG( graph, filename):
    """
    Write a corresponding json file

    :param filename:
    :return:
    """
    nodes = list(graph._graph.nodes())
    dict_nodes = {n: i for i, n in enumerate(nodes)}
    times = list(graph.change_times())
    dict_times = {t: i for i, t in enumerate(times)}

    interactions = graph.edge_presence()
    interactions = {str((dict_nodes[e[0]], dict_nodes[e[1]])): [[dict_times[p[0]],dict_times[p[1]]] for p in ts] for e, ts in
                    interactions.items()}
    json.dump({"nodes": nodes, "times": times, "interactions": interactions}, open(filename, 'w'))