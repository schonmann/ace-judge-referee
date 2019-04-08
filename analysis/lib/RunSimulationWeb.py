import EMA
import platform
from datetime import datetime
import sys
import pprint
ilflag = "uploads/resposta_correta/20181214/"
sys.path.insert(0, ilflag)
import nca907ef4130c434c973e70ab216ff1e2 as library

def createInput(variableNames, variableValues, standardInput, parameters, usageFilename):
	N = variableValues[0]
	standardInput.write(str(N) + '\n')
	library.GeraEntrada(N, standardInput)

resultsFolder = "./emafiles"
r = EMA.Runner(["N"], databaseFolder=resultsFolder, customResources=[])

cmd = "./enviado"

minVarValues = [1]
maxVarValues = [1e9]
numOfPoints = [15]
timeLowerLimit = 500
timeUpperLimit = 15000

myVarValues = r.getSuggestedVariableValues(runstatement=cmd, timeLowerLimit=timeLowerLimit, timeUpperLimit=timeUpperLimit, memoryLimit=200, 
					   numOfPoints=numOfPoints, minVarValues=minVarValues, maxVarValues=maxVarValues, 
					   createInstance=createInput)
pprint.pprint(myVarValues)

maxNumOfSamples = 30
	 
r.runSimulation(runstatement=cmd, variableValues=myVarValues, createInstance=createInput,
		samplingConvergenceFactor=("CPU",0.01), minNumOfSamples=1, maxNumOfSamples=maxNumOfSamples, 
		discardOutliers=[res[0] for res in r.resources], appending=False)

