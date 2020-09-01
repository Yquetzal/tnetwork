from __future__ import absolute_import
import unittest
import tnetwork as dn
import shutil


class ReadWriteTestCase(unittest.TestCase):

    def test_read_sociopatterns(self):
        dg = dn.DynGraphSN.graph_socioPatterns2012()

    def test_io_SN(self):
        dg = dn.DynGraphSN.graph_socioPatterns2012()
        dg = dg.aggregate_sliding_window(60*60*24)

        for type in [None,"ncol","gefx","gml","pajek","graphML"]:
            print("writing ",type)
            dn.write_snapshots(dg, "testDir", type)

            print("reading ",type)

            read_dg = dn.read_snapshots("testDir")

            self.assertEqual(len(dg.snapshots()), len(read_dg.snapshots()))

            self.assertEqual(list(dg.snapshots().values())[0].edges, list(read_dg.snapshots().values())[0].edges)

            shutil.rmtree("testDir")

    def test_io_SG(self):
        dg = dn.DynGraphSN.graph_socioPatterns2012()
        dg = dg.aggregate_sliding_window(60*60*24)
        dg_sg = dg.to_DynGraphIG()

        print("printing file")
        dn.write_period_lists(dg_sg, "testFile")

        print("reading file")

        reconstructed = dn.read_period_lists("testFile")

        self.assertEqual(reconstructed.interactions_intervals(), dg_sg.interactions_intervals())


if __name__ == '__main__':
    unittest.main()
