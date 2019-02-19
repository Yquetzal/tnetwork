from sortedcontainers import *
from tnetwork.utils.bidict import *
import os
import tnetwork as tn
from tnetwork.utils.community_utils import *


def read_static_coms_by_node(inputFile, separator="\t"):
    """
    Read a file containing communities such as each line is:
    node SEP com1 SEP com2 ...
    :param inputFile:
    :param separator:

    """
    coms = dict()
    f = open(inputFile)
    for l in f:

        l = l.rstrip().split(separator)
        for com in l[1:]:
            comID = com
            coms.setdefault(comID,set()).add(l[0])
    toReturn = bidict()
    for com,nodes in coms.items():
        toReturn[frozenset(nodes)]=com

    return toReturn



def read_SN_by_com(inputDir, nameFilter=None, **kwargs):
    """
    Read directory in which each file correponds to a community list
    :param inputDir: directory
    :param nameFilter: a function that takes a file name and decript it into a
    :param kwargs:
    :return: a dynamic community object

    """
    theDynCom = tn.dynamicCommunitiesSN()
    files = os.listdir(inputDir)
    visibleFiles = [f for f in files if f[0] != "."]
    timeIDs = SortedDict() #a dictionary associating timeIds to files
    if nameFilter!=None:
        for f in visibleFiles:
            timeID = nameFilter(f)
            if timeID!=None:
                timeIDs[timeID]=f

        #visibleFiles = timeIDs.keys()
    currentComIDs = 0

    for t in timeIDs:  # for each file in order of their name
        f = inputDir + "/" + str(timeIDs[t])
        coms = read_static_coms_by_node(f,**kwargs)
        #print(coms)
        theDynCom.add_belongins_from(coms, t)
    return theDynCom

def write_com_SN(dyn_communities:tn.DynamicCommunitiesSN, output_dir,asNodeSet=True):
    """
    Write dynamic communities as a directory containing one file for each snapshot.
    :param dynGraph: a dynamic graph
    :param outputDir: address of the directory to write

    """
    os.makedirs(output_dir, exist_ok=True)
    all_partitions = dyn_communities.communities()
    for t,p in all_partitions.items():
        if asNodeSet:
            write_communities_as_nodeset(p,os.path.join(output_dir,str(t)))
        else:
            p = nodesets2affiliations(p)
            write_communities_as_affiliations(p,os.path.join(output_dir,str(t)))
