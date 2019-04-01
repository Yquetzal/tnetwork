from infomap import Infomap
from tnetwork.utils.bidict import bidict


def infomap_communities(graph):
    node2i = bidict({n:i for i,n in enumerate(graph.nodes)})
    if len(node2i)==0:
        return {}
    infomapWrapper = Infomap()
    for (n1,n2) in graph.edges():
        infomapWrapper.addLink(node2i[n1],node2i[n2])

    infomapWrapper.run()
    to_return_temp = infomapWrapper.getModules()
    to_return= {}
    for n,c in to_return_temp.items():
        to_return[node2i.inv[n]]=c

    return to_return

