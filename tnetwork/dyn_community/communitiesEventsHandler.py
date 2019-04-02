import networkx as nx

class CommunitiesEvent(nx.DiGraph):
    def __init__(self):
        super(CommunitiesEvent, self).__init__()

    def add_event(self, n1, n2, tBefore, tAfter, type, fraction=-1):
        """

        :param n1:
        :param n2:
        :param tBefore:
        :param tAfter:
        :param type:
        :param fraction:
        :return:
        """
        self.add_edge(n1,n2,time=(tBefore,tAfter),type=type,fraction=fraction)

    def add_events_from(self, sources, dests, tBefore, tAfter,
                        type, fraction):  # type can be merge, continue, split or unknown
        for source in sources:
            if not source in dests:
                for dest in dests:
                    self.add_event(source, dest, time=(tBefore, tAfter), type=type, fraction=fraction)

    def is_newborn(self, c):
        return self.is_newborn_from_void(c) or self.is_newborn_from_merge(c) or self.is_newborn_from_split(c)

    def is_newborn_from_void(self, c):
        return self.in_degree(c)==0

    def is_newborn_from_merge(self, c):
        if self.in_degree(c) <= 1:  # if no ancestor, not a split
            return False
        for pred in self.predecessors(c):  # for each ancestor
            if pred == c:  # if it is the same node (strange but who knows)
                return False

            #if isinstance(pred, tuple):  # if the community has an ID associated
             #   if pred[1] == c[1]:  # and the coms have the same IDs
              #      return False
        return True

    def main_successor(self, ancestorCom,
                       allSuccessors):  # return the successor most probable of being the continutation of current com (in term of nm common nodes
        if len(allSuccessors) < 2:
            print("STRANGE: Ask for main ancestor while there is only one: %s" % allSuccessors)
            return -1
        similarity = {k: len(ancestorCom & allSuccessors[k]) for k in allSuccessors}
        maxVal = max(similarity.values())
        for k in similarity:
            if similarity[k] == maxVal:
                return k

    def is_newborn_from_split(self, c):
        if self.in_degree(c) == 0:  # if no ancestor, not a split
            return False

        for pred in self.predecessors(c):  # for each ancestor (case of strange com match)
            hasAValidPred = False
            if self.out_degree(pred) > 1:  # if it is a divide
                if pred == c:  # if it is the same node (strange but who knows)
                    return False

                #if isinstance(pred, tuple):  # if the community has an ID associated
                #    if pred[1] == c[1]:  # and the coms have the same IDs
                #        return False
                hasAValidPred = True
        if hasAValidPred:
            return True
        else:
            return False