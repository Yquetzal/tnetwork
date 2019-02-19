import tnetwork as dn
from sortedcontainers import *



def write_SG(theDynGraph:dn.DynGraphSG, fileOutput):
    """
    Write a stream graph as a list of intervals, for the graph, the nodes, and the edges
    :param theDynGraph: a dynamic graph
    :param fileOutput: the address of the file to write

    """
    toWrite = []
    toWrite.append(["SG", str(theDynGraph._start)+":"+str(theDynGraph._end)])
    for (n, intervs) in theDynGraph.node_presence().items():
        toAdd = ["N",n]

        for interv in intervs.get_intervals():
            toAdd += [str(interv[0])+":"+str(interv[1])]
        toWrite.append(toAdd)

    for ((n1,n2),intervs) in theDynGraph.interactions().items():
        toAdd = ["E", n1, n2]
        for interv in intervs.get_intervals():
            toAdd += [str(interv[0])+":"+str(interv[1])]
        toWrite.append(toAdd)


    dn.write_list_of_list(toWrite,fileOutput,sep="\t")


def read_SG(fileInput):
    """
    Read a stream graph as a list of intervals, for the graph, the nodes, and the edges
    :param fileInput:

    """
    aDynGraph = dn.DynGraphSG()
    file = open(fileInput)
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

def write_ordered_changes(dynNet:dn.DynGraphSG, fileOutput, dateEveryLine=False, nodeModifications=False, separator="\t", edgeIdentifier="l"):
    """
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
    if type(dynNet) is dn.DynGraphSN:
        dynNet = dynNet.toDynGraphTN(convertTimeToInteger=False)

    timeOfActions = SortedDict()
    #NOTE : can be easily optimized ! one complete check to add and to remove nodes...
    dataDicNodes={}
    if nodeModifications: #note that we add nodes before edges, so that nodes are added before there edges...
        dataDicNodes = dynNet.nodesD()

        for (n,intervs) in dataDicNodes.items():
            #times = self.nodes[n]
            for interv in intervs.get_intervals():
                addDate = interv[0]

                #delDate = maxInterval(interv)
                timeOfActions.setdefault(addDate,[]).append("+n" + separator + str(n))

    dataDicEdges = dynNet.edgesD()

    for (e,intervs) in dataDicEdges.items():
        #print("e",e,intervs)
        #times = self.edges[e]
        for interv in intervs.get_intervals():
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
            for interv in intervs.get_intervals():
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

    dn.write_list_of_list(toWrite, fileOutput, separator="\t")

