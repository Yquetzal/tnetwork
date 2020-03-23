class DynCommunities():

    def slice(self,start,end):
        raise NotImplementedError("Not implemented")

    def affiliations(self, t=None):
        raise NotImplementedError("Not implemented")

    def communities(self, t=None):
        raise NotImplementedError("Not implemented")

    def add_affiliation(self, nodes, cIDs, times):
        raise NotImplementedError("Not implemented")

    def add_affiliations_from(self, clusters, times):
        raise NotImplementedError("Not implemented")

    def remove_affiliation(self, n, com, times):
        raise NotImplementedError("Not implemented")

    def affiliations_durations(self, nodes=None, communities=None):
        raise NotImplementedError("Not implemented")

    def nodes_main_com(self):
        raise NotImplementedError("Not implemented")
