import statistics
from tnetwork.utils.community_utils import jaccard
import networkx as nx



def community_duration(a_dyn_com):
    """
    Community duration

    :param a_dyn_com: community as sortedDict of snapshots
    :return:
    """
    return len(a_dyn_com)


def community_avg_size(a_dyn_com):
    """
    Community average size

    :param a_dyn_com: community as sortedDict of snapshots
    :return:
    """
    return statistics.mean([len(x) for x in a_dyn_com.values()])


def community_avg_stability(a_dyn_com):
    """
    Community average jaccard change

    :param a_dyn_com: community as sortedDict of snapshots
    :return:
    """
    if community_duration(a_dyn_com) == 1:
        return None

    changes = []
    ts = list(a_dyn_com.keys())
    for i in range(len(ts) - 1):
        changes.append(jaccard(a_dyn_com[ts[i]], a_dyn_com[ts[i + 1]]))
    return statistics.mean(changes)

def community_avg_score(a_dyn_com,dyn_graph,score=nx.conductance):
    scores = []
    try:
        for t,nodes in a_dyn_com.items():
            scores.append(score(dyn_graph.snapshots(t),nodes))
    except:
        return None
    return statistics.mean(scores)

def community_avg_subgraph_property(a_dyn_com,dyn_graph,property=nx.transitivity):
    scores = []

    for t,nodes in a_dyn_com.items():
        #print(t, nodes)
        #print(dyn_graph.snapshots(t).nodes)
        try:

            subgraph  = dyn_graph.snapshots(t).subgraph(nodes)
            #print(subgraph.degree)

            scores.append(property(subgraph))
        except:
            pass
    if len(scores)==0:
        return None
    return statistics.mean(scores)
