from tnetwork.utils.read_write import write_list_of_list

def nodesets2affiliations(communities):
    """
    Transform community format to "affiliations"

    Representation expected in input: dictionary, key=node set, value= community ID
    Representation in output: dictionary, key=node, value=set of affiliations ID

    :param communities: dictionary, key=node set, value= community ID
    :return: dictionary, key=node, value=list of affiliations ID
    """
    node2com = dict()
    for nodes,id in communities.items():
        for n in nodes:
            node2com.setdefault(n,set())
            node2com[n].add(id)
    return node2com


def affiliations2nodesets(communities):
    """
    Transform community format to "nodesets"

    Representation expected in input: dictionary, key=node, value=list/set of affiliations ID
    Representation in output: dictionary, key=node, value=set of affiliations ID

    :param partition:
    :return:
    """
    asNodeSets = {}
    for n, c in communities.items():
        asNodeSets.setdefault(c, set()).add(n)
    return asNodeSets

def jaccard(com1, com2):
    return float(len(com1 & com2)) / float(len(com1 | com2))

def write_communities_as_nodeset(partition,file,community_name=True):
    """

    :param community: affiliations as dict (setofnodes:name), or set of set of nodes
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

    :param community: affiliations as dict (setofnodes:name), or set of set of nodes
    :param type:
    :return:
    """
    to_print = []
    for node,affiliations in partition.items():
        if not isinstance(affiliations,set) and not isinstance(affiliations,list):
            affiliations = list([affiliations])
        to_print.append([node]+list(affiliations))
    write_list_of_list(to_print,file)
