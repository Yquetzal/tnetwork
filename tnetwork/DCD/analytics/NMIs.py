import math
import scipy as sp
import scipy.stats


####Detecting the overlapping and hierarchical community structure in complex networks
####Normalized Mutual Information to evaluate overlapping community finding algorithms
logBase = 2

def partialEntropyAProba(proba):
    if proba==0:
        return 0
    return -proba * math.log(proba,logBase)

def entropyFracSet(fracSet):
    toReturn = 0
    for frac in fracSet:
        toReturn+=partialEntropyAProba(frac)
    return toReturn

def comPairConditionalEntropy(cl,clKnown,allNodes): #cl1,cl2, snapshot_communities (set of nodes)
    #H(Xi|Yj ) =H(Xi, Yj ) − H(Yj )
    # h(a,n) + h(b,n) + h(c,n) + h(d,n)
    # −h(b + d, n)−h(a + c, n)
    #a: count agreeing on not belonging
    #b: count disagreeing : not in 1 but in 2
    #c: count disagreeing : not in 2 but in 1
    #d: count agreeing on belonging
    nbNodes = len(allNodes)

    a =len((allNodes - cl) - clKnown)/nbNodes
    b = len(clKnown-cl)/nbNodes
    c = len(cl-clKnown)/nbNodes
    d = len(cl & clKnown)/nbNodes

    if partialEntropyAProba(a)+partialEntropyAProba(d)>partialEntropyAProba(b)+partialEntropyAProba(c):
        entropyKnown=sp.stats.entropy([len(clKnown)/nbNodes,1-len(clKnown)/nbNodes],base=logBase)
        conditionalEntropy = sp.stats.entropy([a,b,c,d],base=logBase) - entropyKnown
        #print("normal",entropyKnown,sp.stats.entropy([a,b,c,d],base=logBase))
    else:
        conditionalEntropy = sp.stats.entropy([len(cl)/nbNodes,1-len(cl)/nbNodes],base=logBase)
    #print("abcd",a,b,c,d,conditionalEntropy,cl,clKnown)

    return conditionalEntropy #*nbNodes

def coverEntropy(cover,allNodes): #cover is a list of set, no com ID
    allEntr = []
    for com in cover:
        fractionIn = len(com)/len(allNodes)
        allEntr.append(sp.stats.entropy([fractionIn,1-fractionIn],base=logBase))

    return sum(allEntr)



def coverConditionalEntropy(cover,coverRef,allNodes): #cover and coverRef and list of set
    X=cover
    Y=coverRef

    allMatches = []
    #print(cover)
    #print(coverRef)
    for com in cover:
        matches = [(com2,comPairConditionalEntropy(com,com2,allNodes)) for com2 in coverRef]
        bestMatch = min(matches,key=lambda c: c[1])
        allMatches.append(bestMatch[1])
    #print(allMatches)
    return sum(allMatches)

def NMI(cover,coverRef,allNodes=-1,variant="LFR",adjustForChance=False): #cover and coverRef should be list of set, no community ID
    """
    :param cover: set of set of nodes
    :param coverRef:set of set of nodes
    :param allNodes:
    :param variant:
    :param adjustForChance:
    :return:
    """
    if (len(cover)==0 and len(coverRef)!=0) or (len(cover)!=0 and len(coverRef)==0):
        return 0
    if cover==coverRef:
        return 1

    if allNodes==-1:
        allNodes={n for c in coverRef for n in c}
        allNodes|={n for c in cover for n in c}

    #print("compute HXY")
    HXY = coverConditionalEntropy(cover,coverRef,allNodes)
    #print("compute HYX")

    HYX = coverConditionalEntropy(coverRef,cover,allNodes)
    HX = coverEntropy(cover,allNodes)
    #print("HY")
    HY = coverEntropy(coverRef,allNodes)

    #print("HXY...",HXY,HYX,HX,HY)
    NMI = -10
    if variant=="LFR":
        NMI = 1- 0.5*(HXY/HX+HYX/HY)
    elif variant=="MGH":
        IXY = 0.5*(HX-HXY+HY-HYX)
        NMI =  IXY/(max(HX,HY))
    if NMI<0 or NMI>1 or math.isnan(NMI):
        print("NMI: %s  from %s %s %s %s "%(NMI,HXY,HYX,HX,HY))
        raise Exception("incorrect NMI")
    return NMI

def NMIdynamic(covers,coversRef,allNodes=-1,variant="LFR", symmetric=True): #covers,coversRef : ordered list of cover type:(dict/bidic com:set(nodes))
    combinedCover = {}
    combinedCoverRef = {}

    for t in range(len(coversRef)): #for each slice
        #if len(coversRef[t])==0:


        for c in covers[t]: #for each com:
            combinedCover.setdefault(c,set())
            combinedCover[c]|= {(t,n) for n in covers[t][c]}
        for c in coversRef[t]:  # for each com:
            combinedCoverRef.setdefault(c, set())
            combinedCoverRef[c] |= {(t, n) for n in coversRef[t][c]}

    if not symmetric:
        acceptableNodes = set()
        for c in combinedCoverRef:
            acceptableNodes |= {n for n in combinedCoverRef[c]}
        for c in combinedCover:
            combinedCover[c] = combinedCover[c] & acceptableNodes
        combinedCover = {c:v for c,v in combinedCover.items() if len(v)>0}


    if len(combinedCoverRef)>0: # if there is no com in the reference, we cannot compute NMI
        if len(combinedCover)==0: # if the set of tested coms is empty, its NMI value is 0
            return 0
        return NMI(combinedCover.values(),combinedCoverRef.values(),allNodes,variant=variant)
    else:
        return None


