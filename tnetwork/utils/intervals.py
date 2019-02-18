from sortedcontainers import *

class intervals:
    """
    This class uses a sorted dictionary to maintain efficiently a proper complex interval, i.e. that can be composed of several intervals.

    """
    def __init__(self):

        self.interv  = SortedDict()

    def contains_t(self, t):
        """
        Return True if the provided t is in the current interval
        :param t: a time step to test
        :return: True if the time is in the interval, False otherwise
        """
        iBefore = self.interv.bisect_right(t) - 1
        if iBefore >= 0:
            potentialInterval = self.interv.peekitem(iBefore)
            print(potentialInterval)
            if potentialInterval[1][0] <= t < potentialInterval[1][1]:
                return True
        return False

    def add_interval(self, interval):
        """
        Add the provided interval to the current interval object.
        :param interval: provided as a pair (start, end)
        """

        #get the index of element that is just before the point where we should insert the provided interval
        toRemove=[]
        mergedInterv=interval
        iPotentialMergeLeft = self.interv.bisect_left(interval[0])-1
        if iPotentialMergeLeft!=-1: # if not inserted at the beginning
            previousInterv = self.interv.peekitem(iPotentialMergeLeft)[1]
            if previousInterv[1]>=interval[0]: #if previous interval end after beggining of new
                mergedInterv=self._merge_overlapping_intervals(previousInterv, interval) #merge
                toRemove.append(iPotentialMergeLeft) #delete previous


        #get the index of element just before (or exactly at) the end of the provided interval
        iPotentialMergeAfter = self.interv.bisect_left(interval[1])

        if iPotentialMergeAfter<len(self.interv): #if new interval not ending after last
            succInterv = self.interv.peekitem(iPotentialMergeAfter)[1]
            if succInterv[0]==mergedInterv[1] : #if start of element = end of new element
                mergedInterv = self._merge_overlapping_intervals(mergedInterv, succInterv) #merge them
                toRemove.append(iPotentialMergeAfter)

        for i in range(iPotentialMergeLeft+1,iPotentialMergeAfter):
            toRemove.append(i)

        toRemove.sort()
        toRemove.reverse()
        for i in toRemove:
            del self.interv.iloc[i]
        self.interv[mergedInterv[0]]=mergedInterv

    def remove_interval(self, interval):
        """
        remove the provided interval from the current intervals
        :param interval: the interval to remove provided as a tuples (start, stop)
        """

        # get the index of element that is just before the interval we want to remove
        toRemove = []
        toAdd=[]
        iMinToDelete = self.interv.bisect_left(interval[0])-1
        iMaxToDelete = self.interv.bisect_left(interval[1])

        for i in range(max(0,iMinToDelete),iMaxToDelete):
            toRemove.append(i)
            afterSubstraction = self._substract_intervals(self.interv.peekitem(i)[1], interval)

            for interv in  afterSubstraction:
                if interv!=[]:
                    toAdd.append(interv)

        toRemove.sort()
        toRemove.reverse()
        for i in toRemove:
            del self.interv.iloc[i]
        for newIntervs in toAdd:
            self.interv[newIntervs[0]] = newIntervs


    def add_intervals(self, intervals):
        """
        Add several intervals to the current intervals.
        Note: inneficient if there is a lot of overlaps
        :param intervals:
        :return:
        """
        for interv in intervals:
            self.add_interval(interv)

    def get_intervals(self):
        """
        Return the intervals as a list of pairs (start, end)
        :return: list of pairs
        """
        return list(self.interv.values())

    def _merge_overlapping_intervals(self, interval1, interval2):
        """
        merge overlapping intervals provided as pairs (start, stop)
        :param interval1: an interval
        :param interval2: another interval
        :return: a single interval, result of the merge
        """
        return ((min([interval1[0],interval2[0]]),max([interval1[1],interval2[1]])))

    def _substract_intervals(self, before, toSubstract):
        """
        Remove interval toSubstract from interval before. Provided as pairs (start, stop)
        :param before:
        :param toSubstract:
        :return:
        """
        left=[]
        right=[]
        if toSubstract[0]>before[0]:
            left=(before[0],min(before[1],toSubstract[0]))

        if toSubstract[1]<before[1]:
            right=(max(toSubstract[1],before[0]),before[1])
        return(left,right)

    def duration(self):
        """
        Return the duration of this interval, i.e. the sum of the difference between end and start for all intervals in the current interval object.
        :return:
        """
        totalDuration = 0
        for thisInterv in self.interv.values():
            totalDuration+=thisInterv[1]-thisInterv[0]
        return totalDuration

    def __str__(self):
        toReturn=""
        for interv in self.interv.values():
            toReturn+="["+str(interv[0])+","+str(interv[1])+"[ "
        return toReturn

    def  __eq__(self, other):
        return set(self.interv.values())==set(other.interv.values())
    __repr__ = __str__