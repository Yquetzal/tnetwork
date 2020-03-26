import sortedcontainers
import bidict
import os
import tnetwork as tn
from tnetwork.utils.community_utils import *

__all__ = ["read_SN_by_com", "write_com_SN"]

def _read_static_coms_by_node(inputFile, separator="\t"):
    """
    Read snapshot_affiliations as a file, 1 line per node

    :param inputFile: file as str
    :param separator:

    """
    coms = dict()
    f = open(inputFile)
    for l in f:

        l = l.rstrip().split(separator)
        for com in l[1:]:
            comID = com
            coms.setdefault(comID,set()).add(l[0])
    toReturn = bidict.bidict()
    for com,nodes in coms.items():
        toReturn[frozenset(nodes)]=com

    return toReturn

def _read_stable_coms_PAF_format(inputFile):
    """
    blabla
    """
    dyn_coms = tn.DynCommunitiesSN()
    f = open(inputFile)
    i=0
    for line in f:
        parts = line.split(" ")
        timestamps = parts[0].split(",")
        timestamps = [int(x) for x in timestamps]
        nodes = parts[1].split(",")
        nodes = set(nodes)
        dyn_coms.add_affiliation(nodes,i,timestamps)
        i+=1
    return dyn_coms



def read_SN_by_com(inputDir, sn_id_transformer=None, **kwargs):
    """
    Read directory, 1 file = snapshot_affiliations of a snaphshot

    By default, the name of the file is used as snapshot id. A function can be passed to associate a different
    ID snapshot to files

    The format to read is:
    ::

            node1   com1    com2
            node2   com1
            node3   com2    com3    com4
            ...

    :param inputDir: directory
    :param sn_id_transformer: a function taking a str and
    :param kwargs: a separator can be passed with parameter separator
    :return: a dynamic community object

    """
    theDynCom = tn.dynamicCommunitiesSN()
    files = os.listdir(inputDir)
    visibleFiles = [f for f in files if f[0] != "."]
    timeIDs = sortedcontainers.SortedDict() #a dictionary associating timeIds to files
    if sn_id_transformer!=None:
        for f in visibleFiles:
            timeID = sn_id_transformer(f)
            if timeID!=None:
                timeIDs[timeID]=f
    else:
        for f in visibleFiles:
            timeIDs[int(f)]=f

    for t in timeIDs:  # for each file in order of their name
        f = inputDir + "/" + str(timeIDs[t])
        coms = _read_static_coms_by_node(f, **kwargs)

        theDynCom.set_communities(t, coms)
    return theDynCom

def write_com_SN(dyn_communities:tn.DynCommunitiesSN, output_dir, asNodeSet=True):
    """
    Write directory, 1 file = snapshot_affiliations of a snaphshot

    Write dynamic snapshot_affiliations as a directory containing one file for each snapshot.

    Two possible formats:

    **Affiliations:**
    ::

            node1   com1    com2
            node2   com1
            node3   com2    com3    com4

    **Node Sets:**
    ::

            com:com1    n1  n2  n3
            com:another_com    n1   n4  n5


    :param dynGraph: a dynamic graph
    :param outputDir: address of the directory to write
    :param asNodeSet: if True, node sets, otherwise, snapshot_affiliations

    """
    os.makedirs(output_dir, exist_ok=True)
    all_partitions = dyn_communities.snapshot_communities()
    for t,p in all_partitions.items():
        if asNodeSet:
            write_communities_as_nodeset(p,os.path.join(output_dir,str(t)))
        else:
            p = nodesets2affiliations(p)
            write_communities_as_affiliations(p,os.path.join(output_dir,str(t)))
