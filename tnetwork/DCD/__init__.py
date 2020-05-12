from tnetwork.DCD.pure_python.matching_survival_graph import match_survival_graph
from tnetwork.DCD.pure_python.simple_matching import iterative_match
from tnetwork.DCD.pure_python.rollingCPM import rollingCPM
from tnetwork.DCD.pure_python.community_tracker import MSSCD
from tnetwork.DCD.pure_python.smoothed_louvain import smoothed_louvain
from tnetwork.DCD.pure_python.smoothed_graph import smoothed_graph


from tnetwork.DCD.multi_temporal_scale import generate_multi_temporal_scale
#from tnetwork.DCD.analytics import analytics_all
from tnetwork.DCD.communities_scenarios import ComScenario

methods_intern = ["match_survival_graph", "smoothed_graph", "iterative_match", "smoothed_louvain", "rollingCPM","MSSCD"]
generation = ["ComScenario","generate_multi_temporal_scale"]

__all__ = methods_intern+generation#+analytics_all