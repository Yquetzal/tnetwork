import subprocess


def launchCommandWaitAnswer(acommand, printOutput=True):
    process = subprocess.Popen(acommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while (True):
        retcode = process.poll()  # returns None while subprocess is running
        line = process.stdout.readline()
        if printOutput:
            print(line)
        # yield line
        if (retcode is not None):
            if retcode != 0:

                print("FAILURE WITH : " + acommand)
            break
    process.wait()