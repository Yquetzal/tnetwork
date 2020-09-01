import tnetwork as tn
import json

__all__ = ["write_as_LS", "read_LS", ]

def write_as_LS(graph, filename):
    """

    :param filename:
    :return:
    """
    nodes = list(graph._graph.nodes())
    dict_nodes = {n: i for i, n in enumerate(nodes)}
    times = list(graph.change_times())
    dict_times = {t: i for i, t in enumerate(times)}

    interactions = graph.edge_presence()
    interactions = {str((dict_nodes[e[0]], dict_nodes[e[1]])): [dict_times[t] for t in ts] for e, ts in
                    interactions.items()}
    json.dump({"frequency":graph.frequency,"nodes": nodes, "times": times, "interactions": interactions}, open(filename, 'w'))


def read_LS(filename):
    """
    Read TS json format

    :param filename:
    :return:
    """
    g = json.load(open(filename, 'r'))
    node_dict = {i: n for i, n in enumerate(g["nodes"])}
    time_dict = {i: t for i, t in enumerate(g["times"])}
    freq = g["frequency"]
    edges = g["interactions"]
    edges = {eval(e): [time_dict[t] for t in ts] for e, ts in edges.items()}
    edges = {(node_dict[e[0]], node_dict[e[1]]): ts for e, ts in edges.items()}
    return tn.DynGraphLS(edges=edges,frequency=freq)