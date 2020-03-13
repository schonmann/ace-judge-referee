from lib import EMA

def createInput(variableNames, variableValues, standardInput, parameters, usageFilename):
	N = variableValues[0]
	standardInput.write(str(N) + '\n')
	library.GeraEntrada(N, standardInput)

def verdict(executable_path, complexities, input_generator):

    resultsFolder = "./emafiles"
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