import pandas as pd
from tnetwork import DynCommunitiesIG

__all__ = ["write_IGC"]

def write_IGC(dyn_communities:DynCommunitiesIG, outputFile, renumber=False):
    """
    Write snapshot_affiliations as interval lists

    Format is:
    ::

        node1   com1=5:10   com2=10:20
        node2   com1=0:100  com3=50:100


    use with caution, not tested for some time

    :param dyn_communities: dynamic snapshot_affiliations
    :param outputFile: address of file to write
    :param renumber: use successive ids instead of original community ids
    """

    toWrite = []
    comFloatIDs = {}
    comIDs = 1
    for n,belongings in enumerate(dyn_communities._by_com()):
        line = [str(n)]
        for com in belongings:
            if renumber:
                if not com in comFloatIDs:
                    comFloatIDs[com] = comIDs
                    comIDs += 1
            else:
                comFloatIDs[com]=com
            for boundaries in belongings[com].periods():
                line.append(str(comFloatIDs[com])+"="+str(boundaries[0]) + ":" + str(boundaries[1]))

        toWrite.append(line)
    pd_temp = pd.DataFrame(toWrite)
    pd_temp.to_csv(outputFile)

def _read_com_ordered_changes(inputFile):
    """
    Read dynamic snapshot_affiliations as sequences of change

    format:
    ::

        #   time1
        +nc node1 com1
        +nc node2 com1
        +nc node3 com2
        +nc node4 com2
        #   time2
        =   com1    com2
        -nc node1 com1
        -nc node4 com1

    (use with caution, not tested for some time)

    :param inputFile:
    :return:
    """
    dynCom = DynCommunitiesIG
    f = open(inputFile)
    date = -1
    for l in f:
        l = l.rstrip().split("\t")
        action = l[0]
        if "#" in action:
            date = float(action[1:])

        if action == "+nc":
            node = l[1]
            com = l[2]

            dynCom.add_affiliation(node, com, date)

        if action == "-nc":
            node = l[1]
            com = l[2]
            dynCom.remove_affiliation(node, com, date)

        if action == "=":
            conserved = l[1]
            removed = l[2]
            dynCom.add_event(conserved + removed, conserved, date, date, "merge")

    return dynCom