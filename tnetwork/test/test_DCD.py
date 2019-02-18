import unittest
import tnetwork as tn
import tnetwork.DCD as DCD
import shutil


class DCDTestCase(unittest.TestCase):


    def test_simple_matching(self):
        dg = tn.DynGraphSN.graph_socioPatterns2012()
        dg = dg.aggregate_sliding_window(60*60*24)

        coms = DCD.simple_matching(dg)

        tn.write_com_SN(coms,"testDir")
        shutil.rmtree("testDir")

    def test_survival_graph(self):
        dg = tn.DynGraphSN.graph_socioPatterns2012()
        dg = dg.aggregate_sliding_window(60 * 60 * 24)

        coms = DCD.matching_survival_graph(dg)

        tn.write_com_SN(coms, "testDir")
        shutil.rmtree("testDir")


if __name__ == '__main__':
    unittest.main()
