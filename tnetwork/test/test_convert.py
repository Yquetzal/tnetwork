import unittest
import tnetwork as dn
import networkx as nx


class FunctionTestCase(unittest.TestCase):

    def test_convert1(self):
        dg = dn.DynGraphSN.graph_socioPatterns2012()
        dg = dg.aggregate_time_period("day")
        sg = dg.to_DynGraphSG()
        dg2 = sg.to_DynGraphSN()

        self.assertEqual(dg.snapshots_timesteps(),dg2.snapshots_timesteps())
        for t in dg.snapshots_timesteps():
            self.assertEqual(dg.affiliations(t).edges(), dg2.affiliations(t).edges())

    def test_convert2(self):
        dg = dn.DynGraphSN.graph_socioPatterns2012()
        dg = dg.aggregate_sliding_window(60*60*24)
        sg = dg.to_DynGraphSG(sn_duration=60*60*24)
        dg2 = sg.to_DynGraphSN()

        self.assertEqual(dg.snapshots_timesteps(),dg2.snapshots_timesteps())
        for t in dg.snapshots_timesteps():
            self.assertEqual(dg.affiliations(t).edges(), dg2.affiliations(t).edges())



if __name__ == '__main__':
    unittest.main()