
class DynGraph():
    def node_presence(self, nbunch=None):
        raise NotImplementedError("Not implemented")

    def add_interaction(self,u_of_edge,v_of_edge,time):
        raise NotImplementedError("Not implemented")

    def add_interactions_from(self, nodePairs, times):
        raise NotImplementedError("Not implemented")

    def add_node_presence(self,node,time):
        raise NotImplementedError("Not implemented")

    def add_nodes_presence_from(self, nodes, times):
        raise NotImplementedError("Not implemented")

    def remove_node_presence(self,node,time):
        raise NotImplementedError("Not implemented")

    def graph_at_time(self,t):
        raise NotImplementedError("Not implemented")

    def remove_interaction(self,u_of_edge,v_of_edge,time):
        raise NotImplementedError("Not implemented")

    def remove_interactions_from(self, nodePairs, periods):
        raise NotImplementedError("Not implemented")
    