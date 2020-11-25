#!/usr/bin/env python
# -*- coding: utf-8 -*- 
import EMA
import pprint
import sys

def myFunctions():
	functions= []
	terms = []
	terms.append(EMA.PolyTerm("x", 1))
	m = EMA.Monomial("a", terms, "a"); m.discretize = False
	functions.append(m)
	terms = []
	terms.append(EMA.PolyTerm("x", 2))
	m = EMA.Monomial("a", terms, "a"); m.discretize = False
	functions.append(m)
	terms = []
	terms.append(EMA.PolyTerm("x", 3))
	m = EMA.Monomial("a", terms, "a"); m.discretize = False
	functions.append(m)
	terms = []
	terms.append(EMA.PolyTerm("x", 4))
	m = EMA.Monomial("a", terms, "a"); m.discretize = False
	functions.append(m)
	terms = []
	terms.append(EMA.LogTerm("x", 2, 1))
	m = EMA.Monomial("a", terms, "a"); m.discretize = False
	functions.append(m)
	terms = []
	terms.append(EMA.PolyTerm("x", 1))
	terms.append(EMA.LogTerm("x", 2, 1))
	m = EMA.Monomial("a", terms, "a"); m.discretize = False
	functions.append(m)
	terms = []
	terms.append(EMA.ExpTerm("x", 2, 1))
	m = EMA.Monomial("a", terms, "a"); m.discretize = False
	functions.append(m)
	return functions

r = EMA.Runner(variableNames=["N"], databaseFolder="~/workspace/main/results", customResources=[])

wf = True
if len(sys.argv)>1:
	wf = (sys.argv[1]=="1")

#for (resource, unit, factor) in r.resources:
resource = "Time"
if wf:
	fn = r.getResourceUsageFunction(resource, discardTimeUnder=10, case='mean', equivalenceThreshold=0.005, 
					tieBreakMaxVal=0, discreteFunctionsOnly=False, printFunctionReport=True, possibleFunctions=myFunctions)
	titleStr = r.getFunctionString(resource,fn[-1][1],True)
else:
	fn = None; titleStr = resource
print "\n" + resource + ":"
pprint.pprint(fn)

#	r.plotResourceUsage(resource, title=titleStr, mode="windows", style=("points" if wf else "lines"), cases = (0,1,0), 
#		usageFunction=fn, exportToFolder="graphs", exportToFormat="eps")

#	r.plotResourceUsage(resource, title=EMA.FunctionPredictor.getConcreteFunction(fn[0][1]), mode="windows", style = "points", cases = (0,1,0), 
#		usageFunction=fn, exportToFolder="graphs", exportToFormat="png")
