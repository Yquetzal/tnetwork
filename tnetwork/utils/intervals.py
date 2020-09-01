import copy
import sortedcontainers
import numbers

class Intervals:
    """
    Class used to represent complex intervals

    This class is used to represent periods of existence of nodes and edges. Nodes and edges can exist during
    not continuous periods (e.g., from time 2 to 5, and from time 7 to 8). Those intervals are represent as
    closed on the left and open on the right, i.e., [2,5[ and [2,8[. If we were to use closed intervals on the
    right, we would be confronted to ponctual overlaps (without duration), which cause troubles. Furthermore,
    intervals are often used to represent discrete time events. If we want to express that an edge exist
    during one hour, from 8a.m. to 9a.m, representing it as [8,9[ gives the following results:

    * Does the edge exist at 8a.m? -> answer YES
    * Does the edge exist at 9a.m? -> answer NO
    * Duration -> 1h

    When intervals are added, overlapping ones are merged, i.e. if the current Intervals contains
    [0,3[ and [4,5[
    and we add the interval [2,4[,
    The resulting Interval will be [0,5[

    This class uses a sorted dictionary to maintain efficiently a proper complex interval,
    key=start date, value=pair(start,end)

    The attribute "interv" contains the interval (a SortedDict) and can be safely manipulated
    """
    def __init__(self,initial=None):
        """
        Instantiate intervals

        Instanciate an intervals object. Can be initialized by a list of intervals

        :param initial: a single interval as a pair (start, end), or a list of pair or an Interval object
        """

        self.interv  = sortedcontainers.SortedDict()
        if initial!=None:
            if isinstance(initial,Intervals):
                for start,intv in initial.interv.items():
                    self.interv[start]=intv
            else:
                if isinstance(initial[0],numbers.Number):
                    initial = [initial]
                for period in initial:
                    self.interv[period[0]]=period


    def intersection(self, other_Intervals):
        """
        Intersection with another Intervals

        return the intersection between the current interval and the one provided as parameter, i.e. a new Interval
        containing periods in common between them.

        :param intervals: intervals provided as a Intervals object
        :return: a new Intervals object
        """
        to_return = copy.deepcopy(self)
        start = self.start()
        for interval in other_Intervals.periods():
            to_return._substract_one_period((start, interval[0]))
            start=interval[1]
        to_return._substract_one_period((start, self.end()))
        return to_return

    def union(self,other_Intervals):
        """
        Union with another Intervals

        Return the union between the current interval and the one provided as parameter, i.e. a new interval containing
        all sub-intervals of both. (if they overlap, it is handled)

        :param intervals: intervals provided as a Intervals object
        :return: a new Intervals object
        """
        to_return = copy.deepcopy(self)
        for interval in other_Intervals.periods():
            to_return.add_interval(interval)
        return to_return

    def __add__(self, o):
        """
        Add two Intervals using + operator

        >>> a = Intervals((0,2))
        >>> b = Intervals((1,6))
        >>> c = a+b

        :param o: other interval
        :return:
        """
        return self.union(o)

    def __sub__(self, o):
        """
       Substract an interval from other using - operator

       >>> a = Intervals((0,6))
       >>> b = Intervals((1,2))
       >>> c = a-b

       :param o: other interval
       :return:
       """
        return self.difference(o)

    def __contains__(self, time):
        """
       Defines the in operator

       >>> a = Intervals((0,6))
       >>> b = Intervals((1,2))
       >>> if b in a:
       >>>    print("b is contained in a")

       :param o: other interval
       :return:
       """
        if type(time) is Intervals:
            return self.contains(time)
        return self.contains_t(time)


    def difference(self,other_Intervals):
        """
        Current interval - other_Intervals


        :param other_Intervals:
        :return:
        """
        to_return = Intervals(self)

        for t_start,inter in other_Intervals.interv.items():
            to_return._substract_one_period(inter)

        return to_return


    def contains(self,period):
        """
        Is the period contained in this Interval

        Check if the provided period is included in the (active time of the) current Interval

        :param period: the period to test
        :return: True or False
        """
        t_start= period[0]
        t_end=period[1]
        iBefore = self.interv.bisect_right(t_start) - 1
        if iBefore >= 0:
            potentialInterval = self.interv.peekitem(iBefore)
            if potentialInterval[1][0] <= t_start and  t_end <= potentialInterval[1][1]:
                return True
        return False

    def contains_t(self, t):
        """
        Return True if the provided t is in the current Intervals

        :param t: a time step to test
        :return: True if the time is in the interval, False otherwise
        """
        iBefore = self.interv.bisect_right(t) - 1
        if iBefore >= 0:
            potentialInterval = self.interv.peekitem(iBefore)
            if potentialInterval[1][0] <= t < potentialInterval[1][1]:
                return True
        return False

    def _add_interval_at_the_end(self, interval):
        """
        Add the provided interval at the end.

        The advantage of this function is that it is much faster than the normal addition of interval.

        :param interval: the interval to add
        """
        (last_t,last_period) = self.interv.peekitem(-1)
        if last_period[-1]==interval[0]: #the period to add start at the point where ther previous stop
            self.interv[last_t]=(last_t,interval[-1])
        else:
            self.interv[interval[0]]=interval

    def add_interval(self, interval):
        """
        Add the provided interval to the current interval object.

        Note that the method is relatively slow since all cases need to be checked.
        One could use a specific, optimized function to add specifically at the end: _add_interval_at_the_end

        :param interval: provided as a pair (start, end)
        """

        #if empty interval, simply add
        if len(self.interv)==0:
            self.interv[interval[0]]=interval
            return

        #if interval after the current time, add it at the end
        start = interval[0]
        last_current = self.interv.peekitem(-1)[1][1]
        if start>=last_current:
            self._add_interval_at_the_end(interval)
            return

        #if interval already included, do nothing
        if self.contains(interval):
            return

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

    def _substract_one_period(self, interval):
        """
        Remove the provided interval from the current periods

        :param interval: the interval to remove provided as a tuple (start, stop) or an Interval object
        """

        # get the index of element that is just before the interval we want to remove
        toRemove = []
        toAdd=[]
        iMinToDelete = self.interv.bisect_left(interval[0])-1
        iMaxToDelete = self.interv.bisect_left(interval[1])

        for i in range(max(0,iMinToDelete),iMaxToDelete):
            toRemove.append(i)
            afterSubstraction = self._substract_tuple_from_tuple(self.interv.peekitem(i)[1], interval)

            for interv in  afterSubstraction:
                if interv!=[]:
                    toAdd.append(interv)

        toRemove.sort()
        toRemove.reverse()
        for i in toRemove:
            del self.interv.iloc[i]
        for newIntervs in toAdd:
            self.interv[newIntervs[0]] = newIntervs


    def _add_intervals(self, intervals):
        """
        Add several periods to the current periods.

        Note: inneficient if there is a lot of overlaps

        :param intervals:
        :return:
        """
        for interv in intervals:
            self.add_interval(interv)

    def periods(self):
        """
        Return the periods as a list of pairs (start, end)

        :return: list of pairs
        """
        return [tuple(a) for a in self.interv.values()]

    def _merge_overlapping_intervals(self, interval1, interval2):
        """
        merge overlapping periods provided as pairs (start, stop)

        :param interval1: an interval
        :param interval2: another interval
        :return: a single interval, result of the merge
        """
        return ((min([interval1[0],interval2[0]]),max([interval1[1],interval2[1]])))

    def _substract_tuple_from_tuple(self, before, toSubstract):
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


    def start(self):
        """
        First date of the Intervals

        :return: int
        """
        return self.interv.peekitem(0)[0]

    def end(self):
        """
        Last date of the interval

        :return: int
        """
        return self.interv.peekitem(-1)[1][1]

    def duration(self):
        """
        Duration of the interval

        Return the duration of this interval, i.e. the sum of the difference between end and start for all periods
        in the current interval object.
        :return:
        """
        totalDuration = 0
        for thisInterv in self.interv.values():
            totalDuration+=thisInterv[1]-thisInterv[0]
        return totalDuration

    def _discretize(self, slices):
        """
        Discretize the interval according to provided slices

        :param slices:
        :return:
        """
        to_return={}
        sorted_slices = sortedcontainers.SortedList(slices)
        for period in self.periods(): # for each period of the current interval
            bins = list(sorted_slices.irange(period[0],period[1],inclusive=(True,True))) #Get concerned slices
            for i in range(len(bins)-1):
                to_return[bins[i]]=bins[i+1]-bins[i]
            if len(bins)>0 and period[0]<bins[0]:
                i_bin_before = sorted_slices.bisect_left(period[0])

                bin_before = sorted_slices[i_bin_before-1]
                to_return[bin_before]=bins[0]-period[0]

            if len(bins)>0 and period[1]>bins[-1]:
                #i_bin_after = sorted_slices.bisect_right(period[1])
                #bin_after = sorted_slices[i_bin_after]
                #print(period[1],bins[-1],bin_after)

                to_return[bins[-1]]=period[1]-bins[-1]
        return to_return


    def __str__(self):
        toReturn=""
        for interv in self.interv.values():
            toReturn+="["+str(interv[0])+","+str(interv[1])+"[ "
        return toReturn

    def  __eq__(self, other):
        """
        Defines the = operator

        Checks if two intervals cover the same periods
        :param other:
        :return:
        """
        if not isinstance(other,Intervals):
            return False
        return [x for x in self.interv.values()]==[x for x in other.interv.values()]
    __repr__ = __str__

    @staticmethod
    def from_time_list(atimelist,interval):
        """

        :param timelist: list of sorted observation time
        :param interval: duration between intervals
        :return: an interval
        """
        all_periods= []
        current_interval=[atimelist[0],atimelist[0]+interval]
        for t in atimelist:
            if t==current_interval[1]:
                current_interval[1]=t+interval
            else:
                all_periods.append(current_interval)
                current_interval=[t,t+interval]
        all_periods.append(current_interval)
        return Intervals(all_periods)
