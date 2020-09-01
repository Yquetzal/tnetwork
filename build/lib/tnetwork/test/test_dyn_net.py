import unittest
import tnetwork as tn
import networkx as nx


class FunctionTestCase(unittest.TestCase):

    def test_add_nodes_sn(self):
        dg = tn.DynGraphSN()
        dg.add_node_presence(1,1)
        dg.add_node_presence(2,1)
        dg.add_nodes_presence_from(3,[1,2,3,4,5,6])
        dg.add_nodes_presence_from([4,5],1)
        dg.add_nodes_presence_from([6, 7], [1,2])

        dg.remove_node_presence(2,1)
        dg.remove_node_presence(3, 2)

        self.assertEqual(set(dg.graph_at_time(1).nodes()),set([1,3,4,5,6,7]))
        self.assertEqual(set(dg.graph_at_time(2).nodes()),set([6,7]))
        self.assertEqual(set(dg.graph_at_time(3).nodes()),set([3]))
        self.assertEqual(set(dg.graph_at_time(4).nodes()),set([3]))
        self.assertEqual(set(dg.graph_at_time(6).nodes()),set([3]))

    def test_add_nodes_ig(self):
        dg = tn.DynGraphIG()
        dg.add_node_presence(1,(1,2))
        dg.add_node_presence(2,(1,2))
        dg.add_nodes_presence_from(3,(1,7))
        dg.add_nodes_presence_from([4,5],(1,2))
        dg.add_nodes_presence_from([6, 7], (1,3))

        dg.remove_node_presence(2,(1,2))
        dg.remove_node_presence(3, (2,3))

        self.assertEqual(set(dg.graph_at_time(1).nodes()),set([1,3,4,5,6,7]))
        self.assertEqual(set(dg.graph_at_time(2).nodes()),set([6,7]))
        self.assertEqual(set(dg.graph_at_time(3).nodes()),set([3]))
        self.assertEqual(set(dg.graph_at_time(4).nodes()),set([3]))
        self.assertEqual(set(dg.graph_at_time(6).nodes()),set([3]))

    def test_add_nodes_ls(self):
        dg = tn.DynGraphLS()
        dg.add_node_presence(1,(1,2))
        dg.add_node_presence(2,(1,2))
        dg.add_nodes_presence_from(3,(1,7))
        dg.add_nodes_presence_from([4,5],(1,2))
        dg.add_nodes_presence_from([6, 7], (1,3))

        dg.remove_node_presence(2,(1,2))
        dg.remove_node_presence(3, (2,3))

        self.assertEqual(set(dg.graph_at_time(1).nodes()),set([1,3,4,5,6,7]))
        self.assertEqual(set(dg.graph_at_time(2).nodes()),set([6,7]))
        self.assertEqual(set(dg.graph_at_time(3).nodes()),set([3]))
        self.assertEqual(set(dg.graph_at_time(4).nodes()),set([3]))
        self.assertEqual(set(dg.graph_at_time(6).nodes()),set([3]))

    def test_add_interactions_sn(self):
        dg = tn.DynGraphSN()
        dg.add_interaction(1,2,4)

        self.assertEqual(set(dg.graph_at_time(4).edges()),set([(1,2)]))

        dg.add_interaction(1, 2, 6)

        self.assertEqual(dg.edge_presence((1,2)),[4,6])


        dg.add_interactions_from({2, 3}, [6,7,8])

        self.assertEqual(list(dg.graph_at_time(6).edges()),[(1,2),(2,3)])

        dg.add_interactions_from([(5, 6),(6,7)], 9)
        self.assertEqual(list(dg.graph_at_time(9).edges()),[(5,6),(6,7)])

        dg.add_interactions_from([(1, 2),(1,3)], [10,11])
        self.assertEqual(list(dg.graph_at_time(10).edges()),[(1,2),(1,3)])
        self.assertEqual(list(dg.graph_at_time(11).edges()),[(1,2),(1,3)])


    def test_add_interactions_ig(self):
        dg = tn.DynGraphIG()
        dg.add_interaction(1,2,(4,5))

        self.assertEqual(set(dg.graph_at_time(4).edges()),set([(1,2)]))

        dg.add_interaction(1, 2, (6,7))

        self.assertEqual(dg.edge_presence((1,2),as_intervals=True),tn.Intervals([(4,5),(6,7)]))


        dg.add_interactions_from({2, 3}, (6,7,9))

        self.assertEqual(list(dg.graph_at_time(6).edges()),[(1,2),(2,3)])

        dg.add_interactions_from([(5, 6),(6,7)], (9,10))
        self.assertEqual(list(dg.graph_at_time(9).edges()),[(5,6),(6,7)])

        dg.add_interactions_from([(1, 2),(1,3)], (10,12))
        self.assertEqual(list(dg.graph_at_time(10).edges()),[(1,2),(1,3)])
        self.assertEqual(list(dg.graph_at_time(11).edges()),[(1,2),(1,3)])

    def test_add_interactions_ls(self):
        dg = tn.DynGraphLS()
        dg.add_interaction(1,2,4)

        self.assertEqual(set(dg.graph_at_time(4).edges()),set([(1,2)]))

        dg.add_interaction(1, 2, 6)

        self.assertEqual(list(dg.edge_presence((1,2))),[4,6])


        dg.add_interactions_from({2, 3}, [6,7,8])

        self.assertEqual(list(dg.graph_at_time(6).edges()),[(1,2),(2,3)])

        dg.add_interactions_from([(5, 6),(6,7)], 9)
        self.assertEqual(list(dg.graph_at_time(9).edges()),[(5,6),(6,7)])

        dg.add_interactions_from([(1, 2),(1,3)], [10,11])
        self.assertEqual(list(dg.graph_at_time(10).edges()),[(1,2),(1,3)])
        self.assertEqual(list(dg.graph_at_time(11).edges()),[(1,2),(1,3)])

    def test_remove_functions(self):
        dg = tn.DynGraphSN([nx.karate_club_graph(), nx.karate_club_graph()])
        dg.remove_interaction(1,2,1)

        g = nx.karate_club_graph()
        g.remove_edge(1,2)
        self.assertEqual(set(g.edges),set(dg.snapshots(1).edges))




        dg = tn.DynGraphSN([nx.karate_club_graph(), nx.karate_club_graph()])
        g = nx.karate_club_graph()
        es = list(g.edges)[:3]
        print(es)
        dg.remove_interactions_from(es,0)

        self.assertEqual(set(g.edges),set(dg.snapshots(1).edges))
        g.remove_edges_from(es)

        self.assertEqual(set(g.edges),set(dg.snapshots(0).edges))


if __name__ == '__main__':
    unittest.main()
