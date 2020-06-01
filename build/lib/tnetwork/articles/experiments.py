from bokeh.io import export_png, output_file, show


def _get_return(function, x, y, return_var):
    return_var.append(function(x, elapsed_time=y))

from tnetwork.DCD.analytics.dynamic_partition import *
from nf1 import NF1
from sklearn.metrics import adjusted_rand_score,normalized_mutual_info_score
import pandas as pd


import numpy as np

from tnetwork.DCD.externals.dynamo import dynamo
from tnetwork.DCD.externals.dynmoga import dynmoga
from tnetwork.DCD.externals.MuchaOriginal import transversal_network_mucha_original
from matlab import engine


def standard_methods_to_test():
    eng = engine.start_matlab()

    def smoothed_louvain(x, elapsed_time=True):
        return tn.DCD.iterative_match(x, CDalgo="smoothedLouvain", elapsed_time=elapsed_time)

    # methods_to_test = {"iterative":DCD.iterative_match,"dynamo":dynamo,"dynmoga":dynmoga,"smoothed_louvain":smoothed_louvain}

    def mucha_opti(x, elapsed_time=True):
        return transversal_network_mucha_original(x, elapsed_time=elapsed_time, matlab_session=eng)

    def mucha_global(x, elapsed_time=True):
        return transversal_network_mucha_original(x, elapsed_time=elapsed_time, matlab_session=eng, form="global")

    print("pas de mucha")
    methods_to_test = {"iterative": tn.DCD.iterative_match,
                       "dynamo": dynamo,
                       "smoothed_louvain": smoothed_louvain,
                       "mucha": mucha_opti,  # "mucha_global":mucha_global,
                       "survival_graph": tn.DCD.label_smoothing}  # ,"dynmoga":dynmoga}#

    # methods_to_test = {"smoothed_louvain":smoothed_louvain}#,"dynmoga":dynmoga}#
    return methods_to_test


def generate_graph(nb_com =6,min_size=4,max_size=15,operations=18,mu=0.1):
    print("generating graph with nb_com = ",nb_com)
    prog_scenario = tn.ComScenario(verbose=False, external_density_penalty=mu)
    all_communities = set(prog_scenario.INITIALIZE(np.random.randint(min_size,max_size,size=nb_com)))

    for i in range(operations):
        [com1] = np.random.choice(list(all_communities),1,replace=False)
        all_communities.remove(com1)

        if len(com1.nodes())<max_size and len(all_communities)>0: #merge
            [com2] = np.random.choice(list(all_communities),1,replace=False)
            largest_com = max([com1,com2],key=lambda x: len(x.nodes()))
            merged = prog_scenario.MERGE([com1,com2], largest_com.label(), wait=20)
            all_communities.remove(com2)
            all_communities.add(merged)
        else: #split
            smallest_size = int(len(com1.nodes())/3)
            (com2,com3) = prog_scenario.SPLIT(com1, [prog_scenario._get_new_ID("CUSTOM"), com1.label()], [smallest_size, len(com1.nodes()) - smallest_size], wait=20)
            all_communities|= set([com2,com3])
    (dyn_graph,dyn_com) = prog_scenario.run()


    return(dyn_graph,dyn_com)





def compute_all_stats(all_infos, detailed=True):
    names = []
    times = []
    LaNMI = []
    LNMI = []

    LF1 = []
    LARI = []

    nb_changes = []
    # entropies = []
    ent_by_nodes = []
    S = []

    modularities = []
    nmis = []

    IDs = {}

    for id,an_experiment in all_infos.items():
        GT_as_sn = an_experiment["GT"]
        dyn_graph_sn=an_experiment["graph"]
        results = an_experiment["result"]
        iteration = an_experiment["ID"]

        print(id)
        for name, (result, time) in results.items():
            for k, v in iteration.items():
                IDs.setdefault(k,[])
                IDs[k].append(v)
            names.append(name)
            times.append(time["total"])
            if detailed:
                LaNMI.append(longitudinal_similarity(GT_as_sn, result))
                def nf1go(x, y):
                    a = NF1(y, x)
                    score = a.get_f1()[0]
                    return score


                LF1.append(longitudinal_similarity(GT_as_sn,result,score=nf1go,convert_coms_sklearn_format=False))
                LNMI.append(longitudinal_similarity(GT_as_sn, result))
                LARI.append(longitudinal_similarity(GT_as_sn, result, score=adjusted_rand_score))

                nb_changes.append(nb_node_change(result))

                consecutive_NMIs = consecutive_sn_similarity(result)
                #entropies.append(entropy(result))
                ent_by_nodes.append(entropy_by_node(result)) #####Slow
                S.append(np.average(consecutive_NMIs[0], weights=consecutive_NMIs[1]))

                mods = quality_at_each_step(result, dyn_graph_sn)
                modularities.append(np.average(mods[0], weights=mods[1]))

                sim = similarity_at_each_step(GT_as_sn,result)
                nmis.append(np.average(sim[0],weights=sim[1]))


    df = pd.DataFrame()
    df["algorithm"] = names
    df["running time"] = times

    if detailed:
        df["LaNMI"] = LaNMI
        df["LNMI"] = LNMI

        df["LF1"] = LF1
        df["LARI"] = LARI


        df["M"] = nb_changes
        #df["I_old"] = entropies
        df["I"] = ent_by_nodes
        df["S"] = S


        df["Q"] = modularities
        df["aNMI"] = nmis

    df["# nodes"] = len(dyn_graph_sn.snapshots(dyn_graph_sn.snapshots_timesteps()[0]).nodes)
    df["# steps"] = len(dyn_graph_sn.snapshots())

    for k,l in IDs.items():
        df[k]=l

    return df




def run_all_algos(methods_to_test, dyn_graph_sn, plot=False, waiting=120):
    """

    :param methods_to_test:
    :param dyn_graph_sn:
    :param plot:
    :param waiting:
    :return:
    """
    results = {}
    if plot:
        dyn_graph = dyn_graph_sn.to_DynGraphIG(sn_duration=1)
    methods_this_step = {name: m for name, m in methods_to_test.items()}
    for name, m in methods_this_step.items():
        results[name] = m(dyn_graph_sn, elapsed_time=True)
        #  manager = multiprocessing.Manager()
        #  temp = manager.list()
        #  p = multiprocessing.Process(target=_get_return, args=(m,dyn_graph_sn,True,temp))
        #  p.start()
        #  p.join(waiting)

        #  if p.is_alive():
        #      print ("running... let's kill it...")
        #      del methods_to_test[name]

        # Terminate
        #     p.terminate()
        #     p.join()
        # else:
        # results[name] = temp[0]
        if plot:
            output_file(name + ".html")
            p = tn.plot_longitudinal(dyn_graph, results[name][0].to_DynCommunitiesIG(1))
            show(p)
            export_png(p, filename=name + ".png")

    return results


def subset(graph, com, length):
    subgraph = tn.DynGraphSN(list(graph.snapshots().values())[:length])
    subcomsGT = tn.DynCommunitiesSN()
    for t in subgraph.snapshots_timesteps():
        subcomsGT.set_communities(t, com.snapshot_communities(t))
    return (subgraph, subcomsGT)
