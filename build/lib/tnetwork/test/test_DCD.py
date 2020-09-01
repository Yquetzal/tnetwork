import unittest
import tnetwork as tn
import tnetwork.DCD as DCD
import shutil
import tnetwork.DCD.externals as DCDextern

class DCDTestCase(unittest.TestCase):


    def test_simple_matching(self):
        dg = tn.graph_socioPatterns2012(tn.DynGraphSN)
        dg = dg.aggregate_sliding_window(60*60*24)

        coms = DCD.iterative_match(dg)

        tn.write_com_SN(coms,"testDir")
        shutil.rmtree("testDir")

    def test_survival_graph(self):
        dg = tn.graph_socioPatterns2012(tn.DynGraphSN)
        dg = dg.aggregate_sliding_window(60 * 60 * 24)

        coms = DCD.label_smoothing(dg)

        tn.write_com_SN(coms, "testDir")
        shutil.rmtree("testDir")


    def test_k_cliques(self):
        dg = tn.graph_socioPatterns2012(tn.DynGraphSN)
        dg = dg.aggregate_sliding_window(60 * 60 * 24)

        coms = DCD.rollingCPM(dg)

        tn.write_com_SN(coms, "testDir")
        shutil.rmtree("testDir")

    def test_dynamo(self):
        dg = tn.graph_socioPatterns2012(tn.DynGraphSN)
        dg = dg.aggregate_time_period("day")

        coms = DCDextern.dynamo(dg)

        tn.write_com_SN(coms, "testDir")
        shutil.rmtree("testDir")

    def test_mucha(self):
        dg = tn.graph_socioPatterns2012(tn.DynGraphSN)
        dg = dg.aggregate_sliding_window(60 * 60 * 24)

        coms = DCDextern.transversal_network_mucha_original(dg)

        tn.write_com_SN(coms, "testDir")
        shutil.rmtree("testDir")


if __name__ == '__main__':
    unittest.main()
