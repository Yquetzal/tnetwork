import tnetwork as dn
import os
import subprocess
import time



###############################
######For this class, it is necessary to have Matlab installed
######And to set up the matlab for python engine, see how to there
###### https://fr.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html
###### (you can find the value of matlabroot by tapping matlabroot in your matlab console)
################################


def launchCommandWaitAnswer(acommand, printOutput=True):
    process = subprocess.Popen(acommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if printOutput:
        while (True):
            retcode = process.poll()  # returns None while subprocess is running
            line = process.stdout.readline()
            print(line)
            # yield line
            if (retcode is not None):
                if retcode != 0:
                    print
                    "FAILURE WITH : " + acommand
                break
    process.wait()


def iLCD(dynNet,par1=None,par2=None,runningTime=False):
    #initialisation inspired by http://netwiki.amath.unc.edu/GenLouvain/GenLouvain

    dir = os.path.dirname(__file__)
    jarLocation = os.path.join(dir, "iLCD2016.jar")
    sandBox = os.path.join(dir, "sandBox")

    networkLocation = sandBox+"/network.ctnf"
    communitiesLocation = sandBox+"/snapshot_affiliations"
    dn.write_ordered_changes(dynNet, networkLocation, edgeIdentifier="")

    commandToLaunch = "java -jar "+jarLocation+" -i "+networkLocation+" -o "+communitiesLocation
    start_time = time.time()

    launchCommandWaitAnswer(commandToLaunch,printOutput=False)
    duration = (time.time() - start_time)
    #print("algorithm Running time: %s seconds ---" % runningTime)

    dynComs = dn.readListOfModifCOM(communitiesLocation+".ctnf")
    if runningTime:
        return duration
    return dynComs






#preprocessMatrixForm(0.5)
#muchaOriginal("bla")