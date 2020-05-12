import tnetwork as tn
import os
import subprocess

from tnetwork.readwrite.SN_com_io import _read_stable_coms_PAF_format
import time


def launchCommandWaitAnswer(acommand, printOutput=False,timeout=600):
    #process = subprocess.Popen(acommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    process = subprocess.check_output(acommand, shell=True,timeout=timeout,stderr=subprocess.STDOUT)
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



def write_for_paf(dynGraph: tn.DynGraphSN, outputFile: str):
    """
    """
    tn.write_snapshots_single_file(dynGraph,outputFile,both_directions=True)


def read_coms_dynamo(dynGraph: tn.DynGraphSN, input_dir, nodes_dict):
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

def paf(dynGraph: tn.DynGraphSN,elapsed_time=False,timeout=10):
    print("start paf")

    aFile = os.path.dirname(__file__)
    aFile = os.path.join(aFile,"temp/")
    network_file = aFile+"edges.paf"
    result_file_1 = aFile+"seeds.paf"

    write_for_paf(dynGraph,network_file)
    start = time.time()


    #--------------------
    print("run multidupehack code")
    command_location ="/Users/remycazabet/Documents/loic/multidupehack/"
    command = "multidupehack -c '1 2' -e '2 1 1' -s '3 6 6'"
    launchCommandWaitAnswer(command_location+command+" "+network_file+" -o "+result_file_1,timeout)
    print("multidupehack code run")
    #--------------------
    result_file_2 = aFile+"res.paf"
    print("run paf code")
    command_location = "/Users/remycazabet/Documents/loic/paf/"
    command = "paf -vf "+network_file +" -a 40000 -o "+result_file_2+" --pa --ps "+ result_file_1
    launchCommandWaitAnswer(command_location + command , timeout)
    print("paf code run")

    #-------
    dyn_coms = _read_stable_coms_PAF_format(result_file_2)
    duration = time.time() - start

    if elapsed_time:
        return dyn_coms,{"total":duration}
    else:
        return dyn_coms