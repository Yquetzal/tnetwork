from tnetwork.utils.read_write import write_list_of_list
import pandas as pd
import pkg_resources
import numbers

def nodesets2affiliations(communities):
    """
    Transform community format to "snapshot_affiliations"

    Representation expected in input: dictionary, key= community ID, value= node set
    Representation in output: dictionary, key=node, value=set of snapshot_affiliations ID

    :param communities: dictionary, key=node set, value= community ID
    :return: dictionary, key=node, value=list of snapshot_affiliations ID
    """
    node2com = dict()
    for id, nodes in communities.items():
        for n in nodes:
            node2com.setdefault(n,set())
            node2com[n].add(id)
    return node2com


def affiliations2nodesets(communities):
    """
    Transform community format to "nodesets"

    Representation expected in input: dictionary, key=node, value=list/set of communities ID
    Representation in output: bidict, key=community ID , value=set of nodes

    :param partition:
    :return:
    """

    if communities==None:
        return None

    asNodeSets = dict()

    if len(communities)==0:
        return asNodeSets

    for n, coms in communities.items():
        if isinstance(coms,str) or isinstance(coms,numbers.Number):
            coms=[coms]
        for c in coms:
            asNodeSets.setdefault(c, set())
            asNodeSets[c].add(n)

    return asNodeSets

def single_list_community2nodesets(affiliation_list,node_ids):
    to_return = dict()
    for i in range(len(affiliation_list)):
        to_return.setdefault(affiliation_list[i],set()).add(node_ids[i])
    return to_return

def jaccard(com1, com2):
    union_size = len(com1 | com2)
    if union_size==0:
        return 0
    return len(com1 & com2) / union_size

def write_communities_as_nodeset(partition,file,community_name=True):
    """

    :param community: snapshot_affiliations as dict (setofnodes:name), or set of set of nodes
    :param type:
    :return:
    """

    to_print=[]

    if isinstance(partition,set):
        partition = {k:v for k,v in enumerate(partition)}

    for nodes,name in partition.items():
        if community_name:
            to_print.append(["com:"+str(name)]+list(nodes))
        else:
            to_print.append(nodes)
    write_list_of_list(to_print,file)


def write_communities_as_affiliations(partition,file):
    """

    :param community: snapshot_affiliations as dict (setofnodes:name), or set of set of nodes
    :param type:
    :return:
    """
    to_print = []
    for node,affiliations in partition.items():
        if not isinstance(affiliations,set) and not isinstance(affiliations,list):
            affiliations = list([affiliations])
        to_print.append([node]+list(affiliations))
    write_list_of_list(to_print,file)

def read_socioPatterns_com():
    resource_package = __name__
    resource_package = '.'.join(resource_package.split(".")[:-2])

    resource_path = '/'.join(("dyn_graph",'toy_data', 'thiers_2012.csv'))
    fileLocation = pkg_resources.resource_filename(resource_package, resource_path)
    df = pd.read_csv(fileLocation, sep="\t",
                     names=["t", "n1", "n2", "n1_class", "n2_class"])
    coms = {}
    for index, row in df.iterrows():
        coms[str(row["n1"])] = row["n1_class"]
        coms[str(row["n2"])] = row["n2_class"]
    return coms

#functions to add to community_utils
def read_socioPatterns_Primary_School_com():
    resource_package = __name__
    resource_package = '.'.join(resource_package.split(".")[:-2])

    resource_path = '/'.join(("dyn_graph",'toy_data', 'Primary_School.csv'))
    fileLocation = pkg_resources.resource_filename(resource_package, resource_path)
    df = pd.read_csv(fileLocation, sep="\t",
                     names=["t", "n1", "n2", "n1_class", "n2_class"])
    coms = {}
    for index, row in df.iterrows():
        coms[str(row["n1"])] = row["n1_class"]
        coms[str(row["n2"])] = row["n2_class"]
    return coms
def read_socioPatterns_Hospital():
    resource_package = __name__
    resource_package = '.'.join(resource_package.split(".")[:-2])

    resource_path = '/'.join(("dyn_graph",'toy_data', 'Contacts_Hospital.csv'))
    fileLocation = pkg_resources.resource_filename(resource_package, resource_path)
    df = pd.read_csv(fileLocation, sep="\t",
                     names=["t", "n1", "n2", "n1_class", "n2_class"])
    coms = {}
    for index, row in df.iterrows():
        coms[str(row["n1"])] = row["n1_class"]
        coms[str(row["n2"])] = row["n2_class"]
    return coms