from lib import EMA
from subprocess import PIPE, Popen
import signal

class CommandTimeout(Exception):
    pass

def alarm_handler(signum, frame):
    raise CommandTimeout

def run_command_timeout(command, input, timeout=3, stdout=PIPE, stdin=PIPE):
    p = Popen(command, stdout=stdout, stdin=stdin)

    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(timeout)

    p.stdin.write(input)

    try:
        stdoutdata, stderrdata = p.communicate()
        signal.alarm(0)
        return stdoutdata, stderrdata
    except CommandTimeout:
        pass

def verdict(executable_path, complexities, input_generator):

    resultsFolder = "./emafiles/%s/" % executable_path
    r = EMA.Runner(["N"], databaseFolder=resultsFolder, customResources=[])
    
    minVarValues = [1]
    maxVarValues = [1e9]
    numOfPoints = [15]
    timeLowerLimit = 500
    timeUpperLimit = 15000

    myVarValues = r.getSuggestedVariableValues(runstatement='./', timeLowerLimit=timeLowerLimit, timeUpperLimit=timeUpperLimit, memoryLimit=200,
                        numOfPoints=numOfPoints, minVarValues=minVarValues, maxVarValues=maxVarValues,
                        createInstance=createInput)
    pprint.pprint(myVarValues)

    maxNumOfSamples = 30
        
    r.runSimulation(runstatement=cmd, variableValues=myVarValues, createInstance=createInput,
            samplingConvergenceFactor=("CPU",0.01), minNumOfSamples=1, maxNumOfSamples=maxNumOfSamples,
            discardOutliers=[res[0] for res in r.resources], appending=False)

    return {
        'verdict': 'CORRECT_COMPLEXITY'
    }

def simulate(problemId, answer_key_exe_path, input_generator_exe_path, complexities, bigoNotation):

    # we run the input generator executable passing the value of N to stdin :)
    def createInput(variableNames, variableValues, standardInput, parameters, usageFilename):
        n_value = variableValues[0]
        input = "%s\n" % n_value
        run_command_timeout(input_generator_exe_path, input=input, stdout=standardInput)

    minNumOfSamples=1
    maxNumOfSamples = 5
    minVarValues = [1]
    maxVarValues = [1e6]
    numOfPoints = [5]
    timeLowerLimit = 0
    timeUpperLimit = 15000
    
    resultsFolder = "./emafiles/%s/" % problemId
    runner = EMA.Runner(["N"], databaseFolder=resultsFolder, customResources=[])

    suggestedVarValues = runner.getSuggestedVariableValues(runstatement=answer_key_exe_path, timeLowerLimit=timeLowerLimit, timeUpperLimit=timeUpperLimit, memoryLimit=200, 
					   numOfPoints=numOfPoints, minVarValues=minVarValues, maxVarValues=maxVarValues, 
					   createInstance=createInput)
        
    runner.runSimulation(runstatement=answer_key_exe_path, variableValues=suggestedVarValues, createInstance=createInput,
            samplingConvergenceFactor=("CPU",0.01), minNumOfSamples=minNumOfSamples, maxNumOfSamples=maxNumOfSamples, 
            discardOutliers=[res[0] for res in runner.resources], appending=False)

    return {
        'verdict': 'READY',
    }