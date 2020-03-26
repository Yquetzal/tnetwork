import tnetwork as tn
import networkx as nx
import numpy as np


def _generate_a_community(to_return_graph,to_return_com,nb_nodes, duration, frequency):
    """
    This method add a community with desired properties to the provided dynamic graphs and dynamic coms

    :param to_return_graph: dynamic graph to modify
    :param to_return_com: dynamic coms to modify
    :param nb_nodes: nb nodes in the community
    :param duration: duration of the community
    :param frequency: community edges appear every 1/frequency snapshots in average
    :return:
    """

    #Choose a random start date and fix the end date accordingly
    nb_steps = len(to_return_graph.snapshots())
    start = int(np.random.randint(0, nb_steps - duration))
    end = start + duration

    #Choose random nodes
    nodes = np.random.choice(to_return_graph.snapshots(start).nodes, nb_nodes, replace=False)

    # Add this community to the dyn com
    to_return_com.add_affiliation(nodes, str(start).zfill(5)+str(nodes), [x for x in range(start, end)])

    #For every step, add edges with probability frequency
    for step in range(start, end):
        current_graph = to_return_graph.snapshots(step)
        randoms = np.random.random(nb_nodes * nb_nodes)
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                if randoms[i * nb_nodes + j] < frequency:
                    current_graph.add_edge(nodes[i], nodes[j])


def generate_multi_temporal_scale(nb_steps=5000,nb_nodes=100,nb_com = 10,noise=None,max_com_size=None,max_com_duration=None):
    """
    Generate dynamic graph with stable communities

    This benchmark allows to generate temporal networks as described in
    `Detecting Stable Communities in Link Streams at Multiple Temporal Scales. Boudebza, S., Cazabet, R., Nouali, O., & Azouaou, F. (2019).`.

    To sum up the method, *stable* communities are generated (i.e., no node change).
    These communities exist for some periods, but have different *temporal scales*, i.e., some of them have a high frequency of edges (their edges appear at every step) while others have a lower frequency (i.e., each edge appear only every $t$ steps). To simplify, communities are complete cliques.(but for the low frequency ones, we might observe only a small fraction of their edges in every step)

    The basic parameters are the number of steps, number of nodes and number of communities.
    There are other parameters allowing to modify the random noise, the maximal size of communities and the maximal duration of communities,
    that are by default assigned with values scaled according to the other parameters.

    :param nb_steps: steps in the graph
    :param nb_nodes: total nb nodes
    :param nb_com: nb desired communities
    :param noise: random noise at each step, i.e. probability for any edge to exist at any step. default,1/(nb_nodes**2)
    :param max_com_size: max number of nodes. Default: nb_nodes/4
    :param max_com_duration: max community duration. Default: nb_steps/2
    :return:
    """

    to_return_graph = tn.DynGraphSN()
    to_return_com = tn.DynCommunitiesSN()

    if noise==None:
        noise = 1/(nb_nodes*nb_nodes) #in average, 1 random interaction per timestep

    if max_com_duration==None:
        max_com_duration = nb_steps/2

    if max_com_size==None:
        max_com_size = int(nb_nodes/4)

    #initialise each step with a random graph with noise
    for i in range(nb_steps):
        to_return_graph.add_snapshot(i,nx.erdos_renyi_graph(nb_nodes,noise))

    #for each desired community
    for n in range(nb_com):
        #get a random size
        size = np.random.uniform(np.log(4),np.log(max_com_size))
        size = int(np.exp(size))

        #get a random duration
        duration = np.random.uniform(np.log(10),np.log(max_com_duration))
        duration = int(np.exp(duration))

        #We whoose the clique frequency so that all communities last long enough to be detectable
        cliques_frequency = 10/duration

        _generate_a_community(to_return_graph,to_return_com,size, duration, cliques_frequency)

    return (to_return_graph,to_return_com)


