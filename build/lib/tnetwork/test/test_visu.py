import unittest
import tnetwork as tn

from bokeh.server.server import Server
from tnetwork.visualization.plots import visuTest

class VisuTestCase(unittest.TestCase):


    def test_visu_graph_at_t(self):
        dg = tn.DynGraphSN.graph_socioPatterns2012()
        dg = dg.aggregate_sliding_window(60*60*24)



        my_graph = tn.DynGraphSN.graph_socioPatterns2012()
        my_graph = my_graph.aggregate_sliding_window(60 * 60 * 24)
        my_dyn_coms = tn.DCD.iterative_match(my_graph)

        v = visuTest(my_graph,my_dyn_coms)
        server = Server({'/': v.testApplication})
        server.start()
        #server.show("/")

        #server.io_loop.add_callback(server.show, "/")
        #server.io_loop.start()

if __name__ == '__main__':
    unittest.main()
