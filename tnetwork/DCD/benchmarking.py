
def _get_return(function, x, y, return_var):
    return_var.append(function(x, elapsed_time=y))

from tnetwork.DCD.analytics.dynamic_partition import *
import sklearn
import pandas as pd
import numpy as np
import tnetwork as tn





def _compute_all_stats(all_infos, detailed=True):
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

    SM_N = []
    # entropies = []
    SM_L = []
    SM_P = []

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

        for name, (result, time) in results.items():
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
                LARI.append(longitudinal_similarity(GT_as_sn, result, score=sklearn.metrics.adjusted_rand_score))

                SM_N.append(tn.SM_N(result))

                #entropies.append(entropy(result))
                SM_L.append(tn.SM_L(result)) #####Slow
                SM_P.append(tn.SM_P(result))

                mods = quality_at_each_step(result, dyn_graph_sn)
                modularities.append(np.average(mods[0], weights=mods[1]))



                sim = similarity_at_each_step(GT_as_sn,result)
                nmis.append(np.average(sim[0],weights=sim[1]))

                rand = similarity_at_each_step(GT_as_sn,result,score=sklearn.metrics.adjusted_rand_score)
                ARIs.append(np.average(rand[0],weights=rand[1]))

                #sim = similarity_at_each_step(GT_as_sn,result,score=f1_score())
                #F1s.append(np.average(sim[0],weights=sim[1]))


    df = pd.DataFrame()
    df["algorithm"] = names
    df["running time"] = times
    if detailed:
        df["LAMI"] = LAMI
        #df["LF1"] = LF1

        #df["LNMI"] = LNMI
        df["LARI"] = LARI


        df["SM-N"] = SM_N
        #df["I_old"] = entropies
        df["SM-L"] = SM_L
        df["SM-P"] = SM_P


        df["Q"] = modularities
        df["AMI"] = nmis
        df["ARI"] = ARIs

        #df["F1"] = F1s


    df["# nodes"] = nb_nodes
    df["# steps"] = nb_steps

    for k,l in IDs.items():
        df[k]=l

    return df




def run_algos_on_graph(methods_to_test, dyn_graph_sn):#, plot=False,**kwargs):
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

        # if plot!=False:
        #     p = tn.plot_longitudinal(dyn_graph_sn, results[name][0],**kwargs)#.to_DynCommunitiesIG(1))
        #     location = os.path.join(plot,name+".png")
        #     p.savefig(location, bbox_inches='tight')
        #     plt.clf()

    return results


def _subset(graph, com, length):
    subgraph = tn.DynGraphSN(list(graph.snapshots().values())[:length])
    subcomsGT = tn.DynCommunitiesSN()
    for t in subgraph.snapshots_timesteps():
        subcomsGT.set_communities(t, com.snapshot_communities(t))
    return (subgraph, subcomsGT)


def DCD_benchmark(methods_to_test, mus, nb_coms=[10], subsets=None, iterations=2, min_size=5, max_size=15,
                  operations=20, only_time_statistics=False):
    """
    Compute stats and running time for methods

    Function to reproduce benchmarks in XXX.
    Given methods and some parameters, run algorithms, compute stats, and return the results.

    Due to some occasional crashes with some methods, it is safer to call the method several times with subsets of parameters and combine the results
    later.

    For scalability tests, don't forget to set only_time_statistics=True

    :param methods_to_test: dictionary {method_name,method}
    :param mus: list of mu values (float)
    :param nb_coms: list of number of communities
    :param subsets: list of subset sizes to test
    :param iterations: number of iteration for each combination of parameters
    :param min_size: min size of communities
    :param max_size: max size of communities
    :param operations: number of events in the random graph
    :param only_time_statistics: if True, do not compute statistics such as average modularity, smoothness etc., which are very time consuming.
    :return: communities as a dictionary {ID:{ID:{"}
    """
    saved_coms = {}

    if subsets == None:
        subsets = [None]
    for mu in mus:
        print("mu: ", mu)

        for iteration in range(iterations):
            print("iteration: ", iteration)

            for nb_com in nb_coms:

                (dyn_graph, GT) = tn.generate_simple_random_graph(nb_com, min_size, max_size, operations, mu_noise=0.01, mu=mu)

                dyn_graph_sn = dyn_graph.to_DynGraphSN(slices=1)
                GT_as_sn = GT.to_DynCommunitiesSN(slices=1)

                for length in subsets:
                    print("subset length:",length)
                    ID = (mu, iteration, nb_com, length)
                    saved_coms[ID] = {}
                    saved_coms[ID]["ID"] = {"mu": ID[0], "iteration": ID[1], "#coms": nb_com}
                    if length == None:
                        subgraph = dyn_graph_sn
                        subcomsGT = GT_as_sn
                    else:
                        subgraph, subcomsGT = _subset(dyn_graph_sn, GT_as_sn, length)

                    saved_coms[ID]["graph"] = subgraph
                    saved_coms[ID]["GT"] = subcomsGT

                    try:
                        result = run_algos_on_graph(methods_to_test, subgraph)
                        saved_coms[ID]["result"] = result
                    except:
                        print("error computing algos")
    print("Compute stats")
    stats = _compute_all_stats(saved_coms, detailed= not only_time_statistics)
    return stats



from os import listdir
from os.path import isfile, join
def _load_all_files(keyword, dir_or):
    """
    Function to load all files with a given keyword and concatenate their csvs"""
    mypath = dir_or
    onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    all_pds = []
    for fil in onlyfiles:
        if keyword in fil:
            a_pd = pd.read_csv(mypath+"/"+fil,index_col=0)
            a_pd["file"]=fil
            all_pds.append(a_pd)
            print(len(a_pd))
    df_stats = pd.concat(all_pds)
    return df_stats





