import EMA
import platform
from datetime import datetime
import sys
import pprint
##il_flag
sys.path.insert(0, ilflag)
##import_flag

def createInput(variableNames, variableValues, standardInput, parameters, usageFilename):
	N = variableValues[0]
	standardInput.write(str(N) + '\n')
	##gerador_flag

##databaseFolder_flag
resultsFolder = "./emafiles"
r = EMA.Runner(["N"], databaseFolder=resultsFolder, customResources=[])

##cmd_flag

##minVarValues_flag
##maxVarValues_flag
##numOfPoints_flag
##timeLowerLimit_flag
##timeUpperLimit_flag
##createInstance_flag

myVarValues = r.getSuggestedVariableValues(runstatement=cmd, timeLowerLimit=timeLowerLimit, timeUpperLimit=timeUpperLimit, memoryLimit=200, 
					   numOfPoints=numOfPoints, minVarValues=minVarValues, maxVarValues=maxVarValues, 
					   createInstance=createInput)
pprint.pprint(myVarValues)

##maxNumSamples_flag
	 
r.runSimulation(runstatement=cmd, variableValues=myVarValues, createInstance=createInput,
		samplingConvergenceFactor=("CPU",0.01), minNumOfSamples=1, maxNumOfSamples=maxNumOfSamples, 
		discardOutliers=[res[0] for res in r.resources], appending=False)

