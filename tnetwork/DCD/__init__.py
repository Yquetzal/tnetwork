from tnetwork.DCD.pure_python.matching_survival_graph import label_smoothing
from tnetwork.DCD.pure_python.simple_matching import iterative_match
from tnetwork.DCD.pure_python.rollingCPM import rollingCPM
from tnetwork.DCD.pure_python.community_tracker import MSSCD
from tnetwork.DCD.pure_python.smoothed_louvain import smoothed_louvain
from tnetwork.DCD.pure_python.smoothed_graph import smoothed_graph


from tnetwork.DCD.multi_temporal_scale import generate_multi_temporal_scale
from tnetwork.DCD.analytics import *

from tnetwork.DCD.communities_scenarios import ComScenario, generate_toy_random_network,generate_simple_random_graph
from tnetwork.DCD.benchmarking import DCD_benchmark,run_algos_on_graph
#from tnetwork.DCD.benchmarks import *

#methods_intern = ["label_smoothing", "smoothed_graph", "iterative_match", "smoothed_louvain", "rollingCPM","MSSCD"]
#generation = ["ComScenario","generate_multi_temporal_scale","generate_toy_random_network","generate_simple_random_graph"]
#benchmarking = ["DCD_benchmark"]
#__all__ = methods_intern+generation+benchmarking