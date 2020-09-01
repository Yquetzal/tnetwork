import unittest
import tnetwork as tn


class FunctionTestCase(unittest.TestCase):

    def test_SN2IG2SN(self):
        sn = tn.graph_socioPatterns2012(format=tn.DynGraphSN)
        ig = sn.to_DynGraphIG()
        sn2 = ig.to_DynGraphSN(slices=20)


        self.assertEqual(sn.snapshots_timesteps(),sn2.snapshots_timesteps())
        for t in sn.snapshots_timesteps():
            self.assertEqual(sn.graph_at_time(t).edges(), sn2.graph_at_time(t).edges())

    def test_IG2SN2IG(self):
        ig = tn.graph_socioPatterns2012(format=tn.DynGraphIG)
        sn = ig.to_DynGraphSN(slices=20)
        ig2 = sn.to_DynGraphIG()
        self.assertEqual(ig.interactions(),ig2.interactions())

    def test_SN2LS2SN(self):
        sn = tn.graph_socioPatterns2012(format=tn.DynGraphSN)
        sn = sn.aggregate_sliding_window(60 * 60 * 24)
        ls = sn.to_DynGraphLS()
        sn2 = ls.to_DynGraphSN(slices=20,weighted=False)

        self.assertEqual(sn.snapshots_timesteps(), sn2.snapshots_timesteps())
        for t in sn.snapshots_timesteps():
            self.assertEqual(sn.graph_at_time(t).edges(), sn2.graph_at_time(t).edges())

    def test_aggregateDay(self):
        dg = tn.graph_socioPatterns2012(format=tn.DynGraphSN)
        dgd = dg.aggregate_time_period("day")
        sg = dgd.to_DynGraphIG()
        dg2 = sg.to_DynGraphSN(60*60*24)

        self.assertEqual(dgd.snapshots_timesteps(),dg2.snapshots_timesteps())
        for t in dgd.snapshots_timesteps():
            self.assertEqual(dgd.graph_at_time(t).edges(), dg2.graph_at_time(t).edges())

    def test_SN2IGaggregatePeriod(self):
        dg = tn.graph_socioPatterns2012(format=tn.DynGraphSN)
        dgd = dg.aggregate_sliding_window(60*60*24)
        sg = dgd.to_DynGraphIG()
        dg2 = sg.to_DynGraphSN(60*60*24)

        self.assertEqual(dgd.snapshots_timesteps(),dg2.snapshots_timesteps())
        for t in dgd.snapshots_timesteps():
            self.assertEqual(dgd.graph_at_time(t).edges(), dg2.graph_at_time(t).edges())


if __name__ == '__main__':
    unittest.main()
