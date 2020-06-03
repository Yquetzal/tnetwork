import matplotlib.pyplot as plt

def _get_return(function, x, y, return_var):
    return_var.append(function(x, elapsed_time=y))

from tnetwork.DCD.analytics.dynamic_partition import *
from sklearn.metrics import adjusted_rand_score,f1_score
import pandas as pd

import os
import numpy as np
import pickle






# def standard_methods_to_test():
#     eng = engine.start_matlab()
#
#     def smoothed_louvain(x, elapsed_time=True):
#         return tn.DCD.iterative_match(x, CDalgo="smoothedLouvain", elapsed_time=elapsed_time)
#
#     # methods_to_test = {"iterative":DCD.iterative_match,"dynamo":dynamo,"dynmoga":dynmoga,"smoothed_louvain":smoothed_louvain}
#
#     def mucha_opti(x, elapsed_time=True):
#         return transversal_network_mucha_original(x, elapsed_time=elapsed_time, matlab_session=eng)
#
#     def mucha_global(x, elapsed_time=True):
#         return transversal_network_mucha_original(x, elapsed_time=elapsed_time, matlab_session=eng, form="global")
#
#     print("pas de mucha")
#     methods_to_test = {"iterative": tn.DCD.iterative_match,
#                        "dynamo": dynamo,
#                        "smoothed_louvain": smoothed_louvain,
#                        "mucha": mucha_opti,  # "mucha_global":mucha_global,
#                        "survival_graph": tn.DCD.match_survival_graph}  # ,"dynmoga":dynmoga}#
#
#     # methods_to_test = {"smoothed_louvain":smoothed_louvain}#,"dynmoga":dynmoga}#
#     return methods_to_test






def compute_all_stats(all_infos, detailed=True):
    """

    :param all_infos:
    :param detailed:
    :return:
    """
    names = []
    times = []

    LAMI = []
    LARI = []

    #LNMI = []
    #LF1 = []

    nb_changes = []
    # entropies = []
    ent_by_nodes = []
    S = []

    modularities = []

    nmis = []
    ARIs = []

    #F1s = []

    nb_nodes = []
    nb_steps = []
    IDs = {}

    for id,an_experiment in all_infos.items():
        GT_as_sn = an_experiment["GT"]
        dyn_graph_sn=an_experiment["graph"]
        if "result" not in an_experiment:
            results={}
        else:
            results = an_experiment["result"]
        iteration = an_experiment["ID"]

        print(id)
        for name, (result, time) in results.items():
            print(name)
            for k, v in iteration.items():
                IDs.setdefault(k,[])
                IDs[k].append(v)
            names.append(name)
            times.append(time["total"])
            nb_steps.append(len(dyn_graph_sn.snapshots()))
            nb_nodes.append(len(dyn_graph_sn.snapshots(dyn_graph_sn.snapshots_timesteps()[0]).nodes))
            if detailed:
                LAMI.append(longitudinal_similarity(GT_as_sn, result))
                # def nf1go(x, y):
                #     a = NF1(y, x)
                #     score = a.get_f1()[0]
                #     return score


                #LF1.append(longitudinal_similarity(GT_as_sn,result,score=f1_score(),convert_coms_sklearn_format=False))
                #LAMI.append(longitudinal_similarity(GT_as_sn, result))
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

                rand = similarity_at_each_step(GT_as_sn,result,score=adjusted_rand_score)
                ARIs.append(np.average(rand[0],weights=rand[1]))

                #sim = similarity_at_each_step(GT_as_sn,result,score=f1_score())
                #F1s.append(np.average(sim[0],weights=sim[1]))


    df = pd.DataFrame()
    df["algorithm"] = names
    df["running time"] = times
    print(names)
    if detailed:
        print(LAMI)
        df["LAMI"] = LAMI
        #df["LF1"] = LF1

        #df["LNMI"] = LNMI
        df["LARI"] = LARI


        df["SM-N"] = nb_changes
        #df["I_old"] = entropies
        df["SM-L"] = ent_by_nodes
        df["SM-P"] = S


        df["Q"] = modularities
        df["AMI"] = nmis
        df["ARI"] = ARIs

        #df["F1"] = F1s


    df["# nodes"] = nb_nodes
    df["# steps"] = nb_steps

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
        if plot!=False:
            #dyn_graph = dyn_graph_sn.to_DynGraphIG(sn_duration=1)
            p = tn.plot_longitudinal(dyn_graph_sn, results[name][0])#.to_DynCommunitiesIG(1))
            location = os.path.join(plot,name+".png")
            p.savefig(location, bbox_inches='tight')
            plt.clf()
    if plot:
        pickle.dump(results,open(os.path.join(plot,"result.pickle"),"wb"))
    return results


def subset(graph, com, length):
    subgraph = tn.DynGraphSN(list(graph.snapshots().values())[:length])
    subcomsGT = tn.DynCommunitiesSN()
    for t in subgraph.snapshots_timesteps():
        subcomsGT.set_communities(t, com.snapshot_communities(t))
    return (subgraph, subcomsGT)
