from tnetwork.dyn_graph.encodings import code_length_SN_M,code_length_SN_E,code_length_LS,code_length_IG
import tnetwork as tn
import pandas as pd
import networkx as nx

__all__ = ["from_pandas_interaction_list", "_encoding_efficiency", "read_interactions"]

def _encoding_efficiency(interactions:pd.DataFrame, frequency):
    nb_interactions = len(interactions)
    nb_unique_edges = len(set(interactions["e"]))
    nb_time = len(set(interactions["time"]))
    nb_nodes = len(set(list(interactions["n1"])+list(interactions["n2"])))
    print("nb_interactions:",nb_interactions,"nb_unique_Edges:",nb_unique_edges,"nb_time:",nb_time,"nb_nodes:",nb_nodes)

    ls_encoding=code_length_LS(None,nb_nodes=nb_nodes, nb_unique_edges=nb_unique_edges, nb_interactions=nb_interactions, nb_time=nb_time)
    sn_m_encoding = code_length_SN_M(None,nb_nodes=nb_nodes, nb_unique_edges=nb_unique_edges, nb_interactions=nb_interactions, nb_time=nb_time)
    sn_e_encoding = code_length_SN_E(None,nb_nodes=nb_nodes, nb_unique_edges=nb_unique_edges, nb_interactions=nb_interactions, nb_time=nb_time)

    df = interactions.sort_values(["e","time"], ascending=(True,True))
    previous = (-1,-1)
    times=set()
    nb_interactions_IG = 0
    for index, row in df.iterrows():
        if not (row["e"]==previous[0] and row["time"]==previous[1]+frequency):
            nb_interactions_IG+=1
            times.add(row["time"])
        previous=(row["e"],row["time"])
    nb_time_IG = len(times)
    print("nb intervals: ",nb_interactions_IG)
    sn_ig_encoding = code_length_IG(None,nb_nodes=nb_nodes, nb_unique_edges=nb_unique_edges, nb_interactions=nb_interactions_IG, nb_time=nb_time_IG)
    results = {}
    results["ls"]=ls_encoding
    results["sn_m"]=sn_m_encoding
    results["sn_e"]=sn_e_encoding
    results["ig"]=sn_ig_encoding

    d_view = sorted([(v, k) for k, v in results.items()])
    for v, k in d_view:
        print(k,":",v)
    return results


def from_pandas_interaction_list(interactions,format,frequency=1,source="n1",target="n2",time="time"):
    interactions = two_columns2unidrected_edge(interactions,source="n1",target="n2")
    if format==tn.DynGraphSN:
        all_times = set(interactions[time])
        all_graphs = {}
        for t in all_times:
            this_t = interactions[interactions["time"]==t]
            all_graphs[t]=nx.from_pandas_edgelist(this_t,source=source,target=target)

        return tn.DynGraphSN(all_graphs,frequency=frequency)

    if format==tn.DynGraphLS:
        #all_edges = set(interactions["e"])
        #print(len(all_edges))
        edges_time = {}
        for i,row in interactions.iterrows():
            edges_time.setdefault(row["e"],[]).append(row[time])
        #for e in all_edges:
        #    edges_time[e]= list(interactions[interactions["e"]==e][time])
        to_return = tn.DynGraphLS(edges=edges_time,frequency=frequency)
        return to_return

    if format==tn.DynGraphIG:
        #all_edges = set(interactions["e"])
        edges_time = {}
        for i,row in interactions.iterrows():
            edges_time.setdefault(row["e"],[]).append(row[time])
        for e,v in edges_time.items():
            edges_time[e]=tn.Intervals.from_time_list(v,frequency)
        #for e in all_edges:
        #    edges_time[e]= list(interactions[interactions["e"]==e][time])
        #    edges_time[e]=tn.Intervals.from_time_list(edges_time)
        to_return = tn.DynGraphIG(edges_time)
        return to_return


def two_columns2unidrected_edge(interactions,source="n1",target="n2"):
    to_return = interactions[interactions[source] != interactions[target]]
    to_return["e"] = to_return.apply(lambda row: tuple(sorted([row[source], row[target]])), axis=1)
    return to_return

def read_interactions(file,frequency=1,format=None,time_first_column=False,sep="\t",columns=None):
    """
    Read link stream data


    :param file: file to read
    :param frequency: frequency of data collection, i.e., smallest possible difference between successive timestamps
    :param format: by default, the most efficient format is selected automatically based on encoding length.
    :param time_first_column: If there are only 3 columns, you can use True if time is on the first column adn false if it is on the last
    :param sep: column separator
    :param columns: if there are more than 3 columns, give column names, the used one being "n1", "n2" and "time"
    :return:
    """
    #theDynGraph = DynGraphSN()

    if columns==None:
        columns=["n1","n2","time"]
        if time_first_column:
            columns=["time","n1","n2"]
    interactions = pd.read_csv(file,names=columns,sep=sep)
    interactions = two_columns2unidrected_edge(interactions)

    if format==None:
        efficiency = _encoding_efficiency(interactions, frequency)
        best_key = min(efficiency, key=efficiency.get)
        if best_key=="ls":
            format=tn.DynGraphLS
        if best_key=="sn_m" or best_key=="sn_e":
            format=tn.DynGraphSN
        if best_key=="ig":
            format=tn.DynGraphIG
    print("graph will be loaded as: ",format)
    return tn.from_pandas_interaction_list(interactions,format,frequency=frequency,source="n1",target="n2")