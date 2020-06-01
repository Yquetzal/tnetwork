import tnetwork as tn
import os
import networkx as nx
import subprocess
import time


def _launchCommandWaitAnswer(acommand, printOutput=False, timeout=10):
    try:
        process = subprocess.check_output(acommand, shell=True,timeout=timeout,stderr=subprocess.STDOUT)
    except:
        print("ERROR, the java code for dynamo failed or timed out, check timeout parameter and/or output when running: ")
        print(acommand)

    # if printOutput:
    #     while (True):
    #         retcode = process.poll()  # returns None while subprocess is running
    #         line = process.stdout.readline()
    #         print(line)
    #         # yield line
    #         if (retcode is not None):
    #             if retcode != 0:
    #                 print
    #                 "FAILURE WITH : " + acommand
    #             break
    #process.delay()



def _write_for_dynamo(dynGraph: tn.DynGraphSN, outputDir: str):
    """
    """
    allGraphs = list(dynGraph.snapshots().values())
    sn_dir = os.path.join(outputDir, "sn")
    diff_dir = os.path.join(outputDir, "diff")

    filelist = [f for f in os.listdir(sn_dir)]
    for f in filelist:
        os.remove(os.path.join(sn_dir, f))

    filelist = [f for f in os.listdir(diff_dir)]
    for f in filelist:
        os.remove(os.path.join(diff_dir, f))

    if not os.path.exists(sn_dir):
        os.makedirs(sn_dir, exist_ok=True)
    if not os.path.exists(diff_dir):
        os.makedirs(diff_dir, exist_ok=True)

    all_nodes = set()
    allGraphs_copy = []
    for g in allGraphs:
        all_nodes.update(set(g.nodes()))
    nodes_dict = {v: i for i, v in enumerate(all_nodes)}
    for g in allGraphs:
        allGraphs_copy.append(nx.relabel_nodes(g, nodes_dict))

    for i, g in enumerate(allGraphs_copy):
        #_write_network_file(g, os.path.join(sn_dir, str(i + 1)), out_format=format)
        f = open(os.path.join(sn_dir, str(i + 1)+".edges"), "w+")
        for e in g.edges():
            ee = sorted(e)
            f.write(str(ee[0]) + "   " + str(ee[1]) + "\n")


        f.close()

        if i > 0:
            f = open(os.path.join(diff_dir, str(i + 1) + ".diff"), "w+")
            added_edges = set(g.edges()) - set(allGraphs_copy[i - 1].edges())
            removed_edges = set(allGraphs_copy[i - 1].edges()) - set(g.edges())
            for e in added_edges:
                ee = sorted(e)
                f.write("   +   " + str(ee[0]) + "   " + str(ee[1]) + "\n")

            for e in removed_edges:
                ee = sorted(e)

                f.write("   -   " + str(ee[0]) + "   " + str(ee[1]) + "\n")
            f.close()

    return nodes_dict


def _read_coms_dynamo(dynGraph: tn.DynGraphSN, input_dir, nodes_dict):
    nodes_dict = {v:k for k,v in nodes_dict.items()}
    coms = tn.DynCommunitiesSN()
    i=1
    for t,g in dynGraph.snapshots().items():
        communities_this_step = {}
        file_Addr = os.path.join(input_dir,"runDynamicModularity_com_"+str(i))
        i+=1
        f = open(file_Addr)
        for id_line,l in enumerate(f.readlines()):
            l = l[:-1]

            real_node = nodes_dict[id_line]
            if real_node in g.nodes:
                communities_this_step.setdefault(l, set())
                communities_this_step[l].add(real_node)
        coms.set_communities(t,communities_this_step)
    coms.create_standard_event_graph(threshold=0.3)
    #print(coms.events.edges)
    coms._relabel_coms_from_continue_events(typedEvents=False)
    return coms

def dynamo(dyn_graph: tn.DynGraphSN, elapsed_time=False, timeout=10):
    """
    DynaMo algorithm

    Requires JAVA
    Algorithm introduced in [1].
    In summary, maintain a high modularity solution through local updates of community structure

    [1]Zhuang, D., Chang, M. J., & Li, M. (2019).
    DynaMo: Dynamic Community Detection by Incrementally Maximizing Modularity.
    IEEE Transactions on Knowledge and Data Engineering.

    :param dyn_graph:
    :param elapsed_time:
    :param timeout:
    :return:
    """
    print("start dynamo")

    dir_or = os.path.dirname(__file__)
    dir = os.path.join(dir_or,"temp")

    ##clean community dir
    com_dir = os.path.join(dir, "coms_dynamo")
    filelist = [f for f in os.listdir(com_dir)]
    for f in filelist:
        os.remove(os.path.join(com_dir, f))


    dict_nodes = _write_for_dynamo(dyn_graph, dir)
    start = time.time()

    print("run external code")


    command = "java -jar "+dir_or+"/DYNAMO/dynamo.jar " + dir + " " + com_dir
    _launchCommandWaitAnswer(command, timeout=timeout)

    #_launchCommandWaitAnswer("java -jar /Users/cazabetremy/ownCloud/Projects-recherche/DYNAMO/dynamo.jar " + dir + " " + dir + "/coms_dynamo", timeout)
    print("postprocess")


    dyn_coms = _read_coms_dynamo(dyn_graph,com_dir , dict_nodes)
    duration = time.time() - start
    print("dynamo run")
    if elapsed_time:
        return dyn_coms,{"total":duration}
    else:
        return dyn_coms