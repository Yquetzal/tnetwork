import networkx as nx
import sys
import os

sys.path.append(os.getcwd() + "/..")
import lpa
import utils

class opt:
	resolution = 0.2
	delta = 0.01
	tolerance = 0.01

class test_utils:
	def setUp(self):
		self.g0 = nx.Graph()
                self.g1 = nx.Graph()
                self.g2 = nx.Graph()
                self.g0.add_edges_from([(1,2,{'weight':1}),(1,3,{'weight':1}),(1,4,{'weight':1}),(2,3,{'weight':1}),(2,4,{'weight':1}),(3,4,{'weight':1})])  # 4 node clique
                self.g1.add_edges_from([(1,2,{'weight':1}),(1,3,{'weight':1}),(1,4,{'weight':1}),(2,3,{'weight':1}),(2,4,{'weight':1}),(3,4,{'weight':1}),(4,5,{'weight':1}),(6,5,{'weight':1}),(3,6,{'weight':1})])  
                self.g2.add_edges_from([(1,2,{'weight':10}),(2,3,{'weight':3}),(3,4,{'weight':3}),(2,4,{'weight':3}),(4,5,{'weight':3}),(2,5,{'weight':3})])
		self.label_dict1 = {1:'a',2:'a',3:'a',4:'a'}
		self.label_dict2 = {1:'b',2:'a',3:'a',4:'a'}
		self.label_dict3 = {1:'a',2:'a',3:'a',4:'b',5:'b',6:'b'}
		self.label_dict4 = {1:'a',2:'a',3:'a',4:'a',5:'b',6:'b'}

	def test_lpa(self):
		out_label_dict = lpa.lpa(self.g0, opt.tolerance, 1,self.label_dict1)  	# all are in the same community => no change
		assert out_label_dict == self.label_dict1 
		out_label_dict = lpa.lpa(self.g0, opt.tolerance, 1,self.label_dict2)	# clique with 1 in 'b', others in 'a'
		assert out_label_dict == self.label_dict1 
		# a---a---b    a---a---b    
		# | x | \ | => | x |   | 
		# a---a---b    a---a---b  
		out_label_dict = lpa.lpa(self.g1, opt.tolerance, 1,self.label_dict3)  
		assert out_label_dict == self.label_dict4  

          	 
