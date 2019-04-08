#!/usr/bin/env python
# -*- coding: utf-8 -*- 
import EMA
import pprint
import sys

def runAnalysisTemplate(complexities):

	def functions(complexities):
		functions= []

		##complexidade_flag
		terms = []
		terms.append(EMA.ExpTerm())
		monomial = EMA.Monomial("a", terms, "a")
		monomial.discretize = False
		functions.append(monomial)

		return functions

	resultsFolder = "./emafiles"

	r = EMA.Runner(variableNames=["N"], databaseFolder=resultsFolder, customResources=[])

	wf = True
	if len(sys.argv)>1:
		wf = (sys.argv[1]=="1")

	#for (resource, unit, factor) in r.resources:
	resource = "Time"
	if wf:
		fn = r.getResourceUsageFunction(resource, discardTimeUnder=10, case='mean', equivalenceThreshold=0.005, 
						tieBreakMaxVal=0, discreteFunctionsOnly=False, printFunctionReport=True, possibleFunctions=functions)
		titleStr = r.getFunctionString(resource,fn[-1][1],True)
	else:
		fn = None; titleStr = resource
	print "\n" + resource + ":"
	pprint.pprint(fn)

	#	r.plotResourceUsage(resource, title=titleStr, mode="windows", style=("points" if wf else "lines"), cases = (0,1,0), 
	#		usageFunction=fn, exportToFolder="graphs", exportToFormat="eps")

	#	r.plotResourceUsage(resource, title=EMA.FunctionPredictor.getConcreteFunction(fn[0][1]), mode="windows", style = "points", cases = (0,1,0), 
	#		usageFunction=fn, exportToFolder="graphs", exportToFormat="png")

