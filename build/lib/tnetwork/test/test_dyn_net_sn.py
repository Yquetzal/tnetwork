import unittest
import tnetwork as dn
import networkx as nx


class FunctionTestCase(unittest.TestCase):

    def test_add_nodes(self):
        dg = dn.DynGraphSN()
        dg.add_node_presence(1,1)
        dg.add_node_presence(2,1)
        dg.add_nodes_presence_from(3,[1,2,3,4])
        dg.remove_node_presence(2,1)

        self.assertEqual(len(dg.snapshots()),4)
        self.assertEqual(list(dg.snapshots()[1].nodes),[1,3])



    def test_add_functions(self):
        dg = dn.DynGraphSN()
        dg.add_interaction(1,2,4)

        self.assertEqual(len(dg.snapshots()),1)
        self.assertEqual(list(dg.snapshots()[4].edges),[(1,2)])

        dg.add_interaction(1, 2, 6)

        self.assertEqual(dg.snapshots_timesteps(),[4,6])


        dg.add_interactions_from((2, 3), [6,7,8])

        self.assertEqual(dg.snapshots_timesteps(),[4,6,7,8])
        self.assertEqual(list(dg.snapshots()[6].edges),[(1,2),(2,3)])

        dg.add_interactions_from([(5, 6),(6,7)], [9,10])
        self.assertEqual(list(dg.snapshots()[9].edges),[(5,6)])
        self.assertEqual(list(dg.snapshots()[10].edges),[(6,7)])

    def test_remove_functions(self):
        dg = dn.DynGraphSN([nx.karate_club_graph(),nx.karate_club_graph()])
        dg.remove_interaction(1,2,1)

        g = nx.karate_club_graph()
        g.remove_edge(1,2)
        self.assertEqual(set(g.edges),set(dg.snapshots(1).edges))




        dg = dn.DynGraphSN([nx.karate_club_graph(),nx.karate_club_graph()])
        g = nx.karate_club_graph()
        es = list(g.edges)[:3]
        print(es)
        dg.remove_interactions_from(es,0)

        self.assertEqual(set(g.edges),set(dg.snapshots(1).edges))
        g.remove_edges_from(es)

        self.assertEqual(set(g.edges),set(dg.snapshots(0).edges))




    def test_aggregation(self):
        dg =  dn.DynGraphSN.graph_socioPatterns2012()
        dg.aggregate_sliding_window(60*60*24)

if __name__ == '__main__':
    unittest.main()
