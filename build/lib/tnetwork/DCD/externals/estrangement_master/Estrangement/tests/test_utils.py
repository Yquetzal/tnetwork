import networkx as nx
import sys
import os
import nose

sys.path.append(os.getcwd() + "/..")
import utils

class test_utils:
	def setUp(self):
	        self.g0 = nx.Graph()
        	self.g1 = nx.Graph()
		self.g2 = nx.Graph()
		self.g3 = nx.Graph()
		self.g4 = nx.Graph()
		self.g5 = nx.Graph()
    		self.g7 = nx.Graph()
    		self.g6 = nx.Graph()
        	self.g0.add_edges_from([(1,2,{'weight':2}),(1,3,{'weight':1}),(2,4,{'weight':1})])
        	self.g1.add_edges_from([(1,4,{'weight':1}),(2,3,{'weight':1}),(3,4,{'weight':1})])
        	self.g2.add_edges_from([(1,2,{'weight':2}),(2,3,{'weight':1}),(3,4,{'weight':1})])
		self.g3.add_edges_from([(5,6),(5,7)])
		self.g4.add_edges_from([(1,5),(2,3)])	
        	self.g5.add_edges_from([(1,2,{'weight':2}),(1,3,{'weight':1}),(2,4,{'weight':1})])
    		self.g6.add_edges_from([(1,2,{'weight':1}),(1,3,{'weight':1}),(2,3,{'weight':1})])
    		self.g7.add_edges_from([(1,2,{'weight':1})])
		self.label_dict1 = {1:'a',2:'a',3:'b',4:'b',5:'c',6:'c'}	
		self.label_dict2 = {1:'a',2:'b',3:'b',4:'b',5:'c',6:'c'}	
		self.label_dict3 = {1:'a',2:'b',3:'c',4:'d',5:'e',6:'f'}	
		self.label_dict4 = {1:'a',2:'a',3:'a',4:'a',5:'a',6:'a'}	
		self.label_dict5 = {1:'b',2:'b',3:'b',4:'b',5:'b',6:'b'}
    		self.label_dict6 = {1:'a',2:'b',3:'b'}

	def test_graph_distance(self):
    		assert utils.graph_distance(self.g0, self.g1) == 1
    		assert utils.graph_distance(self.g0, self.g1, False) == 1
    		assert utils.graph_distance(self.g0, self.g0) == 0
    		assert utils.graph_distance(self.g0, self.g0) == 0
		assert utils.graph_distance(self.g0, self.g2, False) == 0.8
		assert utils.graph_distance(self.g0, self.g2, True) == 0.5

	def test_node_graph_distance(self):
                assert utils.node_graph_distance(self.g0, self.g1) == 0
                assert utils.node_graph_distance(self.g0, self.g0) == 0
                assert utils.node_graph_distance(self.g0, self.g3) == 1
                assert utils.node_graph_distance(self.g0, self.g4) == 0.4
		assert utils.node_graph_distance(nx.path_graph(2),nx.path_graph(4)) == 0.5                  
 
	def test_Estrangement(self):
		assert utils.Estrangement(self.g0, self.label_dict4, self.g3) == 0     # no common edge
		assert utils.Estrangement(self.g0, self.label_dict3, self.g5) == 1     # all common edge, all diff community
		assert utils.Estrangement(self.g0, self.label_dict1, self.g2) == 0.25      # one edge between community
		nose.tools.assert_almost_equal(utils.Estrangement(self.g6, self.label_dict6, self.g7),0.3333,4)
		print(utils.Estrangement(self.g6, self.label_dict6, self.g7))
		
	def test_match_labels(self):
		assert utils.match_labels(self.label_dict1, self.label_dict1) == self.label_dict1  # snapshots are the same
                assert utils.match_labels(self.label_dict5, self.label_dict4) == self.label_dict4  # same community, diff label
                assert utils.match_labels(self.label_dict4, self.label_dict4) == self.label_dict4  # same community, same label

	def test_confidence_interval(self):
		assert utils.confidence_interval([2,2,2,2]) == 0
		nose.tools.assert_almost_equal(utils.confidence_interval([1,2,3,4]), 1.096,3)
		assert utils.confidence_interval([2,2,4,4]) == 0.98
		

