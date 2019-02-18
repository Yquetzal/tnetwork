import pandas as pd

def write_SGC(self, outputFile, renumber=False):
    """
    SG => stream graph. format I use for my visualisation
    :param self:
    :param outputFile:
    :param renumber:
    :return:
    """

    toWrite = []
    comFloatIDs = {}
    comIDs = 1
    for n in self.nodes:
        line = [str(n).replace(" ","_")]
        belongings = self.nodes[n]
        for com in belongings:
            if renumber:
                if not com in comFloatIDs:
                    comFloatIDs[com] = comIDs
                    comIDs += 1
            else:
                comFloatIDs[com]=com
            for boundaries in belongings[com].get_intervals():

                # line.append(str(com.begin)+"_"+str(com.end-self.stepL)+":"+str(comFloatIDs[com.data]))
                line.append(str(boundaries[0]) + "_" + str(boundaries[1]) + ":" + str(comFloatIDs[com]))
        toWrite.append(line)
    pd_temp = pd.DataFrame(toWrite)
    pd_temp.to_csv(outputFile)

def read_com_ordered_changes(inputFile):
    """
    Read a dynamic graph represented as a sequence of changes
    :param inputFile:
    :return:
    """
    dynCom = dn.dynamicCommunitiesTN()
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

            dynCom.add_belonging(node, com, date)

        if action == "-nc":
            node = l[1]
            com = l[2]
            dynCom.removeBelonging(node, com,date)

        if action == "=":
            conserved = l[1]
            removed = l[2]
            dynCom.add_event(conserved + removed, conserved, date, date, "merge")

    return dynCom