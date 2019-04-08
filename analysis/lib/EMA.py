import os
import platform
import os.path
import math
import shutil
import subprocess, threading
import multiprocessing
import sys
import ctypes
from datetime import datetime
from random import randint
from random import random
import time

def getRunningTime(baseTime):
		dt = datetime.now() - baseTime
		return ((dt.days*24*60*60 + dt.seconds)*1000 + dt.microseconds/1000.0)

def findStr(text, afterText, untilText):
	start = text.find(afterText) + len(afterText)
	end = text.find(untilText, start)
	return text[start:end].strip()
	
def getVersion():
	return "3.0"

def getNumOfCPUs():
	#returns (logical, physical)
	if platform.system() == "Windows":
		#todo: specific for windows, getting rid of the assumption below
		numOfProc = multiprocessing.cpu_count()
		if numOfProc > 1:
			return (numOfProc, numOfProc/2) #assuming hyperthreading
		else:
			return (1,1)
	else:
		lscpustr = subprocess.check_output("lscpu", shell=True)
		sockets = int(findStr(lscpustr, "Socket(s):", "\n"))
		corepersocket = int(findStr(lscpustr, "Core(s) per socket:", "\n"))
		threadpercore = int(findStr(lscpustr, "Thread(s) per core:", "\n"))
		return (threadpercore * corepersocket * sockets, corepersocket * sockets)

def getCPUUsage():
	if platform.system() == "Windows":
		usage = int(subprocess.check_output("wmic cpu get loadpercentage", shell=True).split("\n")[1])
	else:
		usage = 100-int(subprocess.check_output("vmstat 1 2|tail -1|awk '{print $15}'", shell=True).split("\n")[0])
	return usage

def waitTurnOnSharedEnv(sharedPathForMutex):
	sharedPath = getCanonicalPath(sharedPathForMutex)
	if os.path.isdir(sharedPath):
		myPid = os.getpid()
		queueFilename = sharedPath + "queue"
		procFilename = sharedPath + "processors"
		if not os.path.isfile(procFilename):
			numOfProc = getNumOfCPUs()[1]
			f = open(procFilename, "w")
			f.write(str(numOfProc))
			f.close()
		numOfProc = int(readFile(procFilename))
		f = open(queueFilename, "a")
		f.write(str(myPid) + "\n")
		f.close()
		foundPid = False
		while not foundPid:
			procRunning = []
			procOrder = -1; procListF = readFile(queueFilename).split("\n")[:-1]
			procList = []
			for proc in procListF:
				if not proc in procList:
					procList.append(proc)
			for proc in procList:
				procOrder += 1
				if int(proc) == myPid:
					foundPid = True
					f = open(queueFilename, "w")
					for proc in (procRunning + procList[procOrder:]):
						f.write(proc + "\n")
					f.close()
					break
				else:
					if processIsRunning(int(proc)):
						procRunning.append(proc)
						if len(procRunning) == numOfProc:
							break
			if not foundPid:
				numAheadInQueue = procList.index(str(myPid))
				print "Waiting for EMA processes {0} to finish [{1} processes ahead in queue].".format(procRunning, numAheadInQueue)
				time.sleep(10)
				
def escapeStr(aStr):
	return aStr.encode('string-escape')

def evalFunction(functionString, varNames, varValues):
	for i in range(len(varNames)):
		functionString = functionString.replace(varNames[i], str(varValues[i]))
	functionString = functionString.replace("log", "math.log")
	try:
		return eval(functionString)
	except OverflowError:
		return float("inf")
	except NameError:
		return float("inf")


def getDiscreteValue(val, mode=0):
	if mode == 0:
		r = round(2*val)/2
	else:
		r = getDiscreteValue(val, 0)
		r = r + mode*0.5
	if r == math.ceil(r):
		r = int(r)
	return max(r, 0)

def getPlatformFileFormat(path):
	return path if platform.system() != "Windows" else path.replace("/", "\\")

def getCanonicalPath(folder):
	if platform.system() == "Windows":
		#folder = folder.replace("\", "\\")
                #folder = folder.replace("\\", "\\\\")
		if folder != "":
			if folder[0] == "~":
				folder = folder.replace("~", os.environ["HOMEDRIVE"]+os.environ["HOMEPATH"])
			if folder[len(folder)-1] != "\\":
				folder = folder + "\\"
	else:
		if folder != "":
			if folder[0] == "~":
				folder = folder.replace("~", os.environ["HOME"])
			if folder[len(folder)-1] != "/":
				folder = folder + "/"
	return folder

def mv(src, dst):
	if os.path.isfile(src) or os.path.isdir(src):
		shutil.copy(src, dst)
		rm(src)

def backup(src):
	if os.path.isfile(src):
		i = 0
		while os.path.isfile(src + ".previous." + str(i)):
			i = i+1
		mv(src, src + ".previous." + str(i))	

def rm(obj):
	if os.path.isfile(obj):
                os.remove(obj)
                
	elif os.path.isdir(obj):
		shutil.rmtree(obj)

def mkdir(folder):
	if not os.path.isdir(folder):
		os.mkdir(folder)

def readFile(filename):
	f = open(filename, "r")
	strRead = f.read()
	f.close()
	return strRead
	
def getDiskFreeSpace(folder, disconsiderThisFolder=False):
	sizeInFolder = 0
	if disconsiderThisFolder:
		for dirpath, dirnames, filenames in os.walk(folder):
			for f in filenames:
				fp = os.path.join(dirpath, f)
				sizeInFolder += os.path.getsize(fp)
	if platform.system() == 'Windows':
		free_bytes = ctypes.c_ulonglong(0)
		ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(folder), None, None, ctypes.pointer(free_bytes))
		return free_bytes.value + sizeInFolder
	else:
		statv = os.statvfs(folder)
		return statv.f_bfree*statv.f_bsize + sizeInFolder
        
def freeDiskSpace(ensureFreeSize, folder):
	requiredSpace = ensureFreeSize - getDiskFreeSpace(folder, False)
	numOfDeletions = 0
	if requiredSpace > 0:
		fileList = [os.path.join(folder, f) for f in os.listdir(folder)]
		fileList.sort(key=lambda i: os.stat(i).st_mtime)
		for f in fileList:
			requiredSpace -= os.stat(f).st_size
			os.remove(f)
			numOfDeletions += 1
			if requiredSpace <= 0:
				break
	return numOfDeletions
    
def createValueSeries(v0, vL, increment = 1.5):
	increment = increment if increment != 1.0 else 1.01
	vet = []
	vet.append(v0)
	v0 = v0 * increment
	while v0 <= vL:
		v = int(round(v0))
		if v != vet[len(vet)-1]:
			vet.append(v)
		v0 = v0 * increment
	return vet

def processIsRunning(pid):
	return getProcMemory(pid)[0] != 0.0

def getChildrenProc(pid):
	if platform.system() == "Windows":
		#todo
		return []
	else:
		out = subprocess.Popen(['ps', 'v', '--ppid', str(pid)], stdout=subprocess.PIPE).communicate()[0].split(b'\n')
		children = []
		if len(out) >= 2:
			headers = out[0].split()
			vsz_index = headers.index(b'PID')
			for line in out[1:]:
				cols = line.split()
				if len(cols) >= vsz_index+1:
					ppid = int(cols[vsz_index])
					children.append(ppid)
		return children
	

def getProcMemory(pid, fromParent=False):
	if platform.system() == "Windows":
		out = subprocess.Popen("tasklist /FI \"PID eq {0}\"".format(pid), stdout=subprocess.PIPE).communicate()[0].split(b'\n')
		allocmem, loadedmem = 0.0, 0.0
		if len(out) >= 4:
			vsz_index = 4
			cols = out[3].split()
			if len(cols) >= vsz_index+1:
				allocmem = float(cols[vsz_index].replace(".", "").replace(",", "").replace("K", ""))
				loadedmem = allocmem
	else:
		out = subprocess.Popen(['ps', 'v', '--pid', str(pid)], stdout=subprocess.PIPE).communicate()[0].split(b'\n')
		allocmem, loadedmem = 0.0, 0.0
		if len(out) >= 2:
			headers = out[0].split()
			cols = out[1].split()
			vsz_index = headers.index(b'DRS')
			if len(cols) >= vsz_index+1:
				allocmem = float(cols[vsz_index])

			vsz_index = headers.index(b'RSS')
			if len(cols) >= vsz_index+1:
				loadedmem = float(cols[vsz_index])
		for pchild in getChildrenProc(pid):
			(allocmemchild, loadedmemchild) = getProcMemory(pchild)
			allocmem, loadedmem = allocmem+allocmemchild, loadedmem+loadedmemchild
	return (allocmem, loadedmem)

def printPhaseHeader(text):
	print
	print " "*4 + "+" + "-"*(len(text)+2) + "+"
	print " "*4 + "| " + text + " |"
	print " "*4 + "+" + "-"*(len(text)+2) + "+"
	print

def EMAIsRunning(): 
	for t in threading.enumerate():
		if t.name == "MainThread":
			return t.is_alive()
	return False

class Environ:
	threadCPU = None
	cpuUsage = None 
	@staticmethod
	def getCPUUsage():
		if Environ.threadCPU == None:
			def cpuUsageDeamon():
				while EMAIsRunning():
					Environ.cpuUsage = getCPUUsage()
					time.sleep(1)
			Environ.threadCPU = threading.Thread(target=cpuUsageDeamon)
			Environ.threadCPU.start()
		while Environ.cpuUsage == None:
			time.sleep(1)
		return Environ.cpuUsage


class Debug:
	debugLevel = None # 0 = release version; 1 = information; 2 = possible problems; 3 = internal structures
	@staticmethod
	def isLevel(level):
		return (Debug.debugLevel & (1 << (level-1))) > 0

	@staticmethod
	def log(level, obj, force=False):
		if Debug.debugLevel == None:
			if os.path.isfile("debug.txt"):
				Debug.debugLevel = int(readFile("debug.txt"))
			else:
				Debug.debugLevel = 0
		if force or Debug.isLevel(level):
			print " "*7*level + "{0}".format(obj)
			sys.stdout.flush()

class Command:
	def __init__(self, cmd):
		self.cmd = cmd
		self.process = None
		self.debugging = os.path.isfile("debug.txt")

	@staticmethod
	def stopProcessTree(pid):
		if platform.system() == "Windows":
			os.system("taskkill /PID {0} /T /F >NUL 2>&1".format(pid))

		else:
			out = subprocess.Popen(['pgrep', '-P', str(pid)], stdout=subprocess.PIPE).communicate()[0].split(b'\n')
			os.system("kill -9 {0}".format(pid))
			if len(out) >= 1:
				for i in range(len(out)):
					if out[i] != "":
						childPid = int(out[i])
						Command.stopProcessTree(childPid)

	def stopRunningTree(self):
		if self.process != None:
			Command.stopProcessTree(self.process.pid)

	def getFreeMemory(self):
		if platform.system() == "Windows":
			out = subprocess.Popen('wmic OS get FreePhysicalMemory /Value', stdout=subprocess.PIPE).communicate()[0].split(b'\n')
			vsz_index = 1
			mem = float(out[2].split("=")[vsz_index])
		else:
			out = subprocess.Popen('free', stdout=subprocess.PIPE).communicate()[0].split(b'\n')
			if len(out) > 0 and out[0].split()[5] == "cached":
				vsz_index = 3
				for outline in out:
					#https://askubuntu.com/questions/770108/what-do-the-changes-in-free-output-from-14-04-to-16-04-mean
					if outline[:3] == "-/+":
						mem = float(outline.split()[vsz_index])
			else:
				vsz_index = 6
				for outline in out:
					#https://unix.stackexchange.com/questions/326833/meaning-of-available-field-in-free-m-command 
					if outline[:4] == "Mem:":
						mem = float(outline.split()[vsz_index])
		return mem

	def getUsedMemory(self):
		return getProcMemory(self.process.pid, True)

	def getRunningTime(self, baseTime = None):
		if baseTime == None:
			baseTime = self.startTime
		dt = datetime.now() - baseTime
		return ((dt.days*24*60*60 + dt.seconds)*1000 + dt.microseconds/1000.0)

	def run(self, timeLimit, memoryLimit, tempFolder):

		def formatTime(numOfSec):
			d = int(numOfSec / (3600*24))
			numOfSec = numOfSec-d*(3600*24)
			h = int(numOfSec / 3600)			
			numOfSec = numOfSec-h*3600
			m = int(numOfSec / 60)			
			numOfSec = numOfSec-m*60
	
			dstr = "{0} days".format(d) if d > 1 else "{0} day".format(d) if d == 1 else ""
			hstr = "{0} hrs".format(h) if h > 1 else "{0} hr".format(h) if h == 1 else ""
			mstr = "{0} mins".format(m) if m > 1 else "{0} min".format(m) if m == 1 else ""
			sstr = "{0} secs".format("%.1f" % numOfSec)

			timeStr = ""
			timeStr = timeStr + (", " + dstr if timeStr != "" and dstr != "" else dstr)
			timeStr = timeStr + (", " + hstr if timeStr != "" and hstr != "" else hstr)
			timeStr = timeStr + (", " + mstr if timeStr != "" and mstr != "" else mstr)
			timeStr = timeStr + (", " + sstr if timeStr != "" and sstr != "" else sstr)

			return timeStr

		def timeShouldBeReportedOnScreen(previousReportedTime, curReportedTime):
			#dynamic changes in reporting time: [0] 0.5s [10s] 1s [1min] 10s [5 min] 1 min [1h] 5 min  [24h] 1h
			if previousReportedTime <= 10:
				should = (int(previousReportedTime/0.5) != int(curReportedTime/0.5))
			elif 10 < previousReportedTime <= 60:
				should = (int(previousReportedTime) != int(curReportedTime))
			elif 60 < previousReportedTime <= 5*60:
				should = (int(previousReportedTime/10.0) != int(curReportedTime/10.0))
			elif 5*60 < previousReportedTime <= 60*60:
				should = (int(previousReportedTime/60.0) != int(curReportedTime/60.0))
			elif 60*60 < previousReportedTime <= 24*60*60:
				should = (int(previousReportedTime/300.0) != int(curReportedTime/300.0))
			else:
				should = (int(previousReportedTime/3600.0) != int(curReportedTime/3600.0))
			return should

                freeMemory = int(round(0.9 * self.getFreeMemory() / 1024.0))
		if memoryLimit == 0 or memoryLimit > freeMemory:
			memoryLimit = freeMemory
		timeLimit = timeLimit/1000.0
		tempFolder = getCanonicalPath(tempFolder)
		INTERVAL_MONITOR = 0.1
		INTERVAL_MONITOR_REPORT = 0.5
		print " ~ resource upper bounds :: time: [{0}] space: [{1} MB]".format(formatTime(timeLimit), memoryLimit)
		proctimeout = INTERVAL_MONITOR if timeLimit == 0 else min(timeLimit, INTERVAL_MONITOR)
		def target():
			if platform.system() == "Windows":
				cmd = "@echo off\n{0}".format(self.cmd)
				f = open(tempFolder + "cmd.bat", "w")
				f.write(cmd)
				f.close()
				sys.stdout.flush()
				self.process = subprocess.Popen(tempFolder + "cmd.bat", shell=True)
			else:
				cmd = "ulimit -v {0}\n{1}\n".format(memoryLimit*1024, self.cmd)
				f = open(tempFolder + "cmd.h", "w")
				f.write(cmd)
				f.close()
				os.chmod(tempFolder + "cmd.h", 0777)
				sys.stdout.flush()
				self.process = subprocess.Popen(tempFolder + "cmd.h", shell=True)
			self.process.communicate()
		thread = threading.Thread(target=target)
		previousReportedTime, lastReportedTime, elapsedTimeToReport, self.usedMemory, self.loadedMemory, self.maxUsedMemory, self.maxLoadedMemory = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
		self.startTime = datetime.now()
		thread.start()
		while thread.is_alive() and (timeLimit == 0 or (lastReportedTime + elapsedTimeToReport) < timeLimit) and self.maxUsedMemory/1024.0 <= memoryLimit:
			thread.join(proctimeout)
			elapsedTimeToReport = self.getRunningTime()/1000.0 - lastReportedTime
			if self.process != None and thread.is_alive():
				(self.usedMemory, self.loadedMemory) = self.getUsedMemory()
				self.maxUsedMemory = max(self.usedMemory, self.maxUsedMemory)
				self.maxLoadedMemory = max(self.loadedMemory, self.maxLoadedMemory)
				if elapsedTimeToReport >= INTERVAL_MONITOR_REPORT:
					lastReportedTime = lastReportedTime + elapsedTimeToReport
					elapsedTimeToReport = 0.0
					if timeShouldBeReportedOnScreen(previousReportedTime, lastReportedTime):
						print " | ~ pid: [{0}] time: [{1}] space: [{2} MB]".format(self.process.pid, formatTime(lastReportedTime), "%.1f"%(self.maxUsedMemory/1024))
						sys.stdout.flush()
						previousReportedTime = lastReportedTime
		if thread.is_alive():
			resultcode = "resourceLimit [time]" if (lastReportedTime + elapsedTimeToReport) >= timeLimit else "resourceLimit [memory]"
			self.stopRunningTree()
			thread.join()
		else:
			resultcode = 0 if self.process.returncode == 0 else "resourceLimit [{0}]".format(self.process.returncode)

		print " ~ exit code: {0}".format(resultcode)
		return resultcode

class Term:
	def __init__(self, var):
		self.var = var

	def __repr__(self):
		return str(self)
	def __str__(self):
		return "term()"
	
class PolyTerm(Term):

	def __init__(self, var, exp):
		Term.__init__(self, var)
		self.exp = exp
		
	def getExpr(self, logscale = False):
		if logscale:
			return "{1}*log({0})".format(self.var, self.exp)
		else:
			return "{0}**{1}".format(self.var, self.exp)
	
	def generateParams(self, addToParams = {}):
		if isinstance(self.exp, basestring):
			paramName = "e" + str(len(addToParams))
			addToParams[paramName] = self
			self.exp = paramName

	def getParams(self, addToParams = {}, addToParamValues = []):
		if isinstance(self.exp, basestring):
			paramName = self.exp
			addToParams[paramName] = self
		else:
			addToParamValues.append(("exp", self.exp, self))
			
	def allowDiscretization(self):
		return isinstance(self.exp, basestring)


	def generateClone(self):
		return PolyTerm(self.var, self.exp)
		
	def generateDiscreteValues(self, estimatedParamValues):
		newExps = []
		if isinstance(self.exp, basestring):
			for mode in range(-2,3):
				newExps.append(getDiscreteValue(estimatedParamValues[self.exp], mode))
		else:
			newExps.append(self.exp)
		newTerms = []
		for newExp in newExps: 
			if newExp == 0:
				newTerms.append(1)
			else:
				newTerms.append(PolyTerm(self.var, newExp))
		return newTerms

	def getConstraints(self, addToConstraints = {}, positiveParams = True):
		if isinstance(self.exp, basestring):
			myConstraints = {}
			addToConstraints[self.exp] = myConstraints 
			if positiveParams:
				myConstraints[">="] = 0
		return addToConstraints
		
class ExpTerm(Term):

	def __init__(self, var, base, exp):
		Term.__init__(self, var)
		self.base = base
		self.exp = exp
		
	def getExpr(self, logscale = False):
		if logscale:
			return "({1}**{2})*log({0})".format(self.base, self.var, self.exp)
		else:
			return "{0}**({1}**{2})".format(self.base, self.var, self.exp)

	def generateParams(self, addToParams = {}):
		if isinstance(self.base, basestring):
			paramName = "b" + str(len(addToParams))
			addToParams[paramName] = self
			self.base = paramName
		if isinstance(self.exp, basestring):
			paramName = "e" + str(len(addToParams))
			addToParams[paramName] = self
			self.exp = paramName

	def getParams(self, addToParams = {}, addToParamValues = []):
		if isinstance(self.base, basestring):
			addToParams[self.base] = self
		else:
			addToParamValues.append(("base", self.base, self))
		if isinstance(self.exp, basestring):
			addToParams[self.exp] = self
		else:
			addToParamValues.append(("exp",self.exp, self))

	def allowDiscretization(self):
		return isinstance(self.base, basestring) or isinstance(self.exp, basestring)

	def generateClone(self):
		return ExpTerm(self.var, self.base, self.exp)
		
	def generateDiscreteValues(self, estimatedParamValues):
		newExps, newBases = [], []
		if isinstance(self.base, basestring):
			for mode in range(-2,3):
				newBases.append(getDiscreteValue(estimatedParamValues[self.base], mode))
			newExps.append(self.exp)
		elif isinstance(self.exp, basestring):
			newBases.append(self.base)
			for mode in range(-2,3):
				newExps.append(getDiscreteValue(estimatedParamValues[self.exp], mode))
		else:
			newBases.append(self.base) 
			newExps.append(self.exp) 
		newTerms = []
		for newExp in newExps:
			for newBase in newBases:	
				if not (newBase == 1 or newBase == 0 or newExp == 0):
					newTerms.append(ExpTerm(self.var, newBase, newExp))
		return newTerms

	def getConstraints(self, addToConstraints = {}, positiveParams = True):
		if isinstance(self.base, basestring):
			myConstraints = {}
			addToConstraints[self.base] = myConstraints 
			if positiveParams:
				myConstraints[">="] = 0
		if isinstance(self.exp, basestring):
			myConstraints = {}
			addToConstraints[self.exp] = myConstraints 
			if positiveParams:
				myConstraints[">="] = 0
		return addToConstraints
					
class LogTerm(Term):

	def __init__(self, var, base, exp):
		Term.__init__(self, var)
		self.base = base
		self.exp = exp
		
	def getExpr(self, logscale = False):
		if logscale:
			return "{2}*log(log({1})/log({0}))".format(self.base, self.var, self.exp)
		else:
			return "(log({1})/log({0}))**{2}".format(self.base, self.var, self.exp)
	
	def generateParams(self, addToParams = {}):
		#if isinstance(self.base, basestring):
		#	paramName = "b" + str(len(addToParams))
		#	addToParams[paramName] = self
		#	self.base = paramName
		if isinstance(self.exp, basestring):
			paramName = "e" + str(len(addToParams))
			addToParams[paramName] = self
			self.exp = paramName

	def getParams(self, addToParams = {}, addToParamValues = []):
		#if isinstance(self.base, basestring):
		#	addToParams[self.base] = self
		#else:
		#	addToParamValues.append(("base",self.base, self))
		if isinstance(self.exp, basestring):
			addToParams[self.exp] = self
		else:
			addToParamValues.append(("exp",self.exp, self))
	
	def allowDiscretization(self):
		 #return isinstance(self.base, basestring) or isinstance(self.exp, basestring)
		return isinstance(self.exp, basestring)

	def generateClone(self):
		return LogTerm(self.var, self.base, self.exp)
	
	def generateDiscreteValues(self, estimatedParamValues):
		newExps = []
		if isinstance(self.exp, basestring):
			for mode in range(-2,3):
				newExps.append(getDiscreteValue(estimatedParamValues[self.exp], mode))
		else:
			newExps.append(self.exp) 
		newTerms = []
		for newExp in newExps:
			if newExp == 0:
				newTerms.append(1)
			else:
				newTerms.append(LogTerm(self.var, self.base, newExp))
		return newTerms
		
	def getConstraints(self, addToConstraints = {}, positiveParams = True):
		#if isinstance(self.base, basestring):
		#	myConstraints = {}
		#	addToConstraints[self.base] = myConstraints
		#	myConstraints[">="] = 1
		if isinstance(self.exp, basestring):
			myConstraints = {}
			addToConstraints[self.exp] = myConstraints 
			if positiveParams:
				myConstraints[">="] = 0
		return addToConstraints
				
class Monomial:

	def __init__(self, coef, terms, indep):
		self.coef = coef
		self.terms = terms
		self.indep = indep
		self.maxNumberIter = 0
		self.discretize = True

	def __repr__(self):
		return str(self)
	def __str__(self):
		return "Monomial()"
		
	def getExpr(self, logscale = False):
		expr = ""
		concat = "+" if logscale else "*"
		if len(self.terms) > 0:
			expr = reduce(lambda x,y: x + concat + y, map(lambda term: term.getExpr(logscale), self.terms))
		expr = "" if expr == "" else concat + expr
		#todo: quando logscale, usar a relacao log(termos+c) = log(termos) + log(1+c/termos) [abaixo, log(termos+c) = log(termos)]
		expr = "log({0}){1}".format(self.coef, expr, self.indep) if logscale else "{0}{1}+{2}".format(self.coef, expr, self.indep)
		return expr
	
	def generateParams(self, addToParams = {}):
		if isinstance(self.coef, basestring):
			paramName = "a" + str(len(addToParams))
			addToParams[paramName] = self
			self.coef = paramName
		if isinstance(self.indep, basestring):
			paramName = "c" + str(len(addToParams))
			addToParams[paramName] = self
			self.indep = paramName
		for term in self.terms:
			term.generateParams(addToParams)
		return addToParams

	def getParams(self):
		addToParams = {}; addToParamValues = []
		if isinstance(self.coef, basestring):
			addToParams[self.coef] = self
		else:
			addToParamValues.append(("coef",self.coef, self))
		if isinstance(self.indep, basestring):
			addToParams[self.indep] = self
		else:
			addToParamValues.append(("indep",self.indep, self))
		for term in self.terms:
			term.getParams(addToParams, addToParamValues)
		return (addToParams, addToParamValues)

	def getConstraints(self, addToConstraints = {}, positiveParams = True):
		if isinstance(self.coef, basestring):
			myConstraints = {}
			addToConstraints[self.coef] = myConstraints 
			myConstraints[">="] = 1e-7
		if isinstance(self.indep, basestring):
			myConstraints = {}
			addToConstraints[self.indep] = myConstraints 
			myConstraints[">="] = 0
		for term in self.terms:
			term.getConstraints(addToConstraints, positiveParams)
		return addToConstraints
	
	def allowDiscretization(self):
		for term in self.terms:
			if term.allowDiscretization():
				return True
		return False
		
	def generateDiscreteValues(self, estimatedParamValues):
		newTerms = []
		for term in self.terms:
			if term.allowDiscretization():
				newTerms = term.generateDiscreteValues(estimatedParamValues)
				if not type(newTerms) is list:
					newTerms = [newTerms]
				break
		newMonomials = []
		for newTerm in newTerms:		
				newTerms = []
				monomialCreated = False
				for iTerm in self.terms:
					if iTerm == term:
						if newTerm == None:
							newMonomials.append(None)
							monomialCreated = True
							break
						elif isinstance(newTerm, Term):
							newTerms.append(newTerm)
					else:
						newTerms.append(iTerm.generateClone())
				if not monomialCreated:
					newMonomials.append(Monomial(self.coef, newTerms, self.indep))
		return newMonomials			
	
	def getMaxNumberIter(self):
		return self.maxNumberIter
					
class FunctionPredictor:

	def __init__(self, resource, parent, val, nary, tempfolder):
		self.resource = resource
		self.nary = nary
		self.val = val
		self.parent = parent
		self.points = []
		self.tempfolder = getCanonicalPath(tempfolder)
		if nary == 1:
			self.F = None # (functionStr, parameterValue1, parameterValue2, ...)
		else:
			self.F = [] # of (val, FunctionPredictor)

	@staticmethod
	def getConcreteFunction(functionEstimation):
		fnStr = functionEstimation[0]
		i = 0
		for var in functionEstimation[1].split(","):
			fnStr = fnStr.replace(var, str(functionEstimation[3][i]))
			i = i+1
		return fnStr

	def getFixedValues(self, L):
		if self.parent != None:
			self.parent.getFixedValues(L)
			L.append(self.val)

	def addValuePoint(self, values):
		curVal = len(values) - self.nary - 1
		if self.nary > 1:
			for (val1, f) in self.F:
				if val1 == values[curVal]:
					f.addValuePoint(values)
					return
			f = FunctionPredictor(self.resource, self, values[curVal], self.nary-1, self.tempfolder)
			self.F.append((values[curVal], f))
			f.addValuePoint(values)
		else:
			self.points.append((values[curVal], values[curVal+1]))

	@staticmethod
	def varTransf(x, inf, sup):
		return (sup-inf)/math.pi*(math.atan(x)+math.pi/2)+inf

	@staticmethod
	def varTransfINV(y, inf, sup):
		return math.tan((y-inf)*math.pi/(sup-inf)-math.pi/2)

	@staticmethod
	def getEstimationMaximumError(dataValues, maxErrorPerValue):
		maxError = 0.0
		for (x,y) in dataValues:
			try:
				maxError += maxErrorPerValue**2 * y**2
			except:
				return float("inf")
		return maxError
	
	@staticmethod
	def getEstimationError(dataValues, functionStr, paramValues, exceedingError = 0.0):
		for paramStr in paramValues.keys():
			functionStr = functionStr.replace(paramStr, str(paramValues[paramStr]))
		chi2 = 0.0
		for (x,y) in dataValues:
			fstr = functionStr.replace("x", str(x)).replace("log", "math.log")
			try:
				estimation = eval(fstr)
			except:
				return float("inf")
			try:
				estimation = estimation*(1.0+exceedingError) if estimation > y else estimation*(1.0-exceedingError)
				chi2 += (estimation - y)**2
			except:
				return float("inf")
		return chi2

	@staticmethod
	def getDictParamValues(strParamList, paramValues):
		dictParamValues = {}
		i = 0
		for param in strParamList.split(","):
			dictParamValues[param] = paramValues[i]
			i = i+1
		return dictParamValues
		
	@staticmethod
	def getParamValues(fitlogfile, parametersList):
		#return: (error, {paramStr: paramValue, ...})
		paramValues = {}

		if not os.path.isfile(fitlogfile):
                        return (None, None)
                                
		content = readFile(fitlogfile)
		error = 1e-20 #avoiding 0 division later on
		startParams = -1
		start = content.find("Sum of squared residuals is zero")
		if start < 0:
			start = content.find("all errors are zero")
			if start < 0:
				start = content.find("(reduced chisquare)")
				if start >= 0:
					start = content.find(":", start) + 1
					end = content.find("\n", start)
					error = float(content[start:end])
                """
		start = content.find("Singular matrix")
  		if start < 0:
			startParams = content.find("=======")
			charEndParams = " "
		else:
			startParams = content.rfind("resultant parameter values", 0, start)
			charEndParams = "\n"
		"""
                startParams = content.find("### EMA output ###")
                if startParams < 0:
                        startParams = content.find("resultant parameter values")
                        if startParams < 0:
                                startParams = content.find("Current set of parameters")
                charEndParams = "\n"
		if startParams >= 0:
			for parameter in parametersList:
				start = content.find(parameter, startParams) + len(parameter)
				start = content.find(" = ", start) + len(" = ")
				end = content.find(charEndParams, start)
				paramValues[parameter] = float(content[start:end])
		else:
			Debug.log(2, "estimation error: parameter values not found")
			Debug.log(2, content)
			error, paramValues = None, None
		
		start = content.rfind("Iteration")
		if start >= 0:
			start = start + len("Iteration")
			end = content.find(charEndParams, start)
			iterations = int(content[start:end])
			Debug.log(1, "iterations: {0}".format(iterations))
		else:
			Debug.log(1, "iterations: 0")

		return (error, paramValues)

	@staticmethod
	def transformFunction(functionStr, parametersList, restrictions, initialValues, startVariablesInOne):
		"""
		parameter a_i with initial value v_i is transformed to a'_i with initial value v'_i such that:
			- w/o constraints:
				- startVariablesInOne:		a_i => v_i * a'_i; v'_i = 1.0
				. not startVariablesInOne: 	a_i => a'_i; v'_i = v_i
			- with constraint >= l_i:   
				- startVariablesInOne:		a_i => (v_i-l_i)*abs(a'_i)+l_i; v'_i = 1.0
				. not startVariablesInOne: 	a_i => abs(a'_i)+l_i; v'_i = v_i-l_i
		"""
		fitFunctionStrToUse = functionStr
		if startVariablesInOne:
			for paramStr in parametersList:
				if restrictions[paramStr].has_key(">="):
					offset = restrictions[paramStr][">="]
					fitFunctionStrToUse = fitFunctionStrToUse.replace(paramStr, "(({0}-{1})*abs({2})+{1})".format(initialValues[paramStr], offset, paramStr))
				else:
					fitFunctionStrToUse = fitFunctionStrToUse.replace(paramStr, "({0}*{1})".format(initialValues[paramStr], paramStr))
		else:
			for paramStr in parametersList:
				if restrictions[paramStr].has_key(">="):
					offset = restrictions[paramStr][">="]
					fitFunctionStrToUse = fitFunctionStrToUse.replace(paramStr, "(abs({2})+{1})".format(initialValues[paramStr], offset, paramStr))
			
		return fitFunctionStrToUse

	@staticmethod
	def transformFunctionResults(paramValues, parametersList, restrictions, initialValues, startVariablesInOne):
		if startVariablesInOne:
			for paramStr in parametersList:
				if restrictions[paramStr].has_key(">="):
					offset = restrictions[paramStr][">="]			
					paramValues[paramStr] = (initialValues[paramStr]-offset)*abs(paramValues[paramStr]) + offset
				else:
					paramValues[paramStr] = initialValues[paramStr] * paramValues[paramStr]
		else:
			for paramStr in parametersList:
				if restrictions[paramStr].has_key(">="):
					offset = restrictions[paramStr][">="]			
					paramValues[paramStr] = abs(paramValues[paramStr]) + offset
				
			
	@staticmethod
	def runEstimation(fitFunction, datafile, workingFolder, useLogTransformation, datafileValues=None, maxNumberIter=0):
		#Marquardt-Levenberg algorithm
		
		#loading (x y) values
		content = readFile(datafile)
		if datafileValues == None: 
			datafileValues = []
		for line in content.split("\n"):
			if line != "":
				values = line.split("\t")
				datafileValues.append((float(values[0]), float(values[1])))
		workingFolder = getCanonicalPath(workingFolder)
		scriptfile = workingFolder + "gnuplot.script"
		parametersDict = {}
		fitFunction.generateParams(parametersDict)
		parametersList = parametersDict.keys()
		parametersStr = reduce(lambda x, y: x + "," + y, parametersList)
		fitFunctionStrLog = fitFunction.getExpr(True)
		fitFunctionStrNormal = fitFunction.getExpr(False)
		fitFunctionStrBase = fitFunctionStrLog if useLogTransformation else fitFunctionStrNormal
		restrictions = fitFunction.getConstraints(positiveParams = True)

		Debug.log(1, "fitting function: {0}".format(fitFunctionStrNormal))
		if useLogTransformation:
			Debug.log(1, "log scale: {0}".format(fitFunctionStrLog))
		
		bestEstimation = None
		
		for start_a0 in range(-4,5):
			for startVariablesInOne in [True, False]:
				initialValues = {}
				for paramStr in parametersList:
					if paramStr[0] == "a":
						initialValues[paramStr] = 10**start_a0 #1e-4
					elif paramStr[0] == "e":
						initialValues[paramStr] = 1
					elif paramStr[0] == "b":
						initialValues[paramStr] = 2
					else:
						initialValues[paramStr] = 1

				while True:
					fitFunctionStrToUse = FunctionPredictor.transformFunction(fitFunctionStrBase, parametersList, restrictions, initialValues, startVariablesInOne)

					initialStr = reduce(lambda x, y: x + ";" + y, map(lambda paramStr: "{0}={1}".format(paramStr, "1.0" if startVariablesInOne else initialValues[paramStr]), parametersList)) + ";"
	
					f = open(scriptfile, "w")
					#f.write("L(x, inf, sup) = (sup-inf)/pi*(atan(x)+pi/2)+inf;")
					#f.write("Linv(y, inf, sup) = tan((y-inf)*pi/(sup-inf)-pi/2);")
					#f.write("FIT_LIMIT=1e-15;\n")
					if maxNumberIter>0:
						f.write("FIT_MAXITER={0};".format(maxNumberIter))
					f.write(initialStr + "\n")
					command = "fit {0} '{2}' using 1:" + ("(log($2))" if useLogTransformation else "2") + " via {1};"
					f.write(command.format(fitFunctionStrToUse, parametersStr, datafile) + "\n")
					command = "fit {0} '{2}' using 1:" + ("(log($2))" if useLogTransformation else "2") + " via {1};"
					f.write("print \"### EMA output ###\";")
					f.write(reduce(lambda x, y: x + ";" + y, map(lambda paramStr: "print \"{0} = \",{0}".format(paramStr), parametersList)) + ";")
					f.close()
					#command = "gnuplot -p -e \"load '{0}'\"".format(workingFolder + "gnuplot.script") ==> prevent gnuplot from exiting
					command = "gnuplot -e \"load '{0}'\"".format(workingFolder + "gnuplot.script")
					rm("fit.log")
					rm(workingFolder + "fit.log")
					rm(workingFolder + "fit.out2")
					os.system(command + " 2>" + workingFolder + "fit.out2")
					mv("fit.log", workingFolder)

					(error, paramValues) = FunctionPredictor.getParamValues(workingFolder + "fit.out2", parametersList)
	
					if paramValues == None:
		
						if bestEstimation == None:
							Debug.log(2, "estimation function: " + fitFunctionStrNormal)
							Debug.log(2, "estimation command: " + command)
							Debug.log(2, "estimation script:\n " + readFile(scriptfile))
							Debug.log(2, "estimation input:\n" + readFile(datafile))
							Debug.log(2, "estimation result:\n" + readFile(workingFolder + "fit.out2"))
						else:
							(error, paramValues) = bestEstimation
							Debug.log(2, "new adjustment failed {0}".format(str(paramValues)))
						break
	
					else:
						needsAdjustment = startVariablesInOne and len([ 0 for paramStr in parametersList if paramValues[paramStr] > 10 or abs(paramValues[paramStr]) < 0.1 ]) > 0
		
						copiedParamValues = [paramValues[paramStr] for paramStr in parametersList]
		
						FunctionPredictor.transformFunctionResults(paramValues, parametersList, restrictions, initialValues, startVariablesInOne)

						for paramStr in parametersList:
							initialValues[paramStr] = paramValues[paramStr]

						#compute error in relation to the original function
						error = FunctionPredictor.getEstimationError(datafileValues, fitFunctionStrNormal, paramValues)
						if bestEstimation == None or bestEstimation[0] > error:
							Debug.log(2, "Better Estimation: fn={4}, start_a0={0}, InOne={1}, error={2}, preverror={3}".format(start_a0,startVariablesInOne,error, None if bestEstimation==None else bestEstimation[0],fitFunctionStrNormal))
							bestEstimation = (error, paramValues) 

						if needsAdjustment:
							Debug.log(2, "adjusting... {0}".format(str(copiedParamValues)))
						else:
							Debug.log(2, "adjusted! {0}".format(str(copiedParamValues)))
							break		
	
		if bestEstimation == None:		
			result = (None, None, None, None, None)
		else:
			(error, paramValues) = bestEstimation
			result = (fitFunctionStrNormal, parametersStr, error, map(lambda paramStr: paramValues[paramStr], parametersList), fitFunction)

		return result

	@staticmethod
	def getPossibleFunctions():
	
		functions= []
		
		# 1) a x^a
		# 2) a x^a log_a^a(x) e com base 2
		# 3) a log_a^a(x) e com base 2
		# 4) a 
		# 5) a x^a a^(x^a)
		# 6) a x^a log_a^a(x) a^(x^a)
		# 7) a log_a^a(x) a^(x^a)
		# 8) a a^(x^a)
		# 9 a 12) mesmo de 5 a 8, com base = 2
		
		# 1)
		terms = []
		terms.append(PolyTerm("x", "a"))
		functions.append(Monomial("a", terms, "a"))

		# 2)
		#terms = []
		#terms.append(PolyTerm("x", "a"))
		#terms.append(LogTerm("x", "a", "a"))
		#functions.append(Monomial("a", terms))

		terms = []
		terms.append(PolyTerm("x", "a"))
		terms.append(LogTerm("x", 2, "a"))
		functions.append(Monomial("a", terms, "a"))
				
		# 3)
		#terms = []
		#terms.append(LogTerm("x", "a", "a"))
		#functions.append(Monomial("a", terms))

		terms = []
		terms.append(LogTerm("x", 2, "a"))
		functions.append(Monomial("a", terms, "a"))
		
		# 4)
		terms = []
		functions.append(Monomial("a", terms, "a"))

		# 5)
		terms = []
		terms.append(ExpTerm("x", "a", "a"))
		terms.append(PolyTerm("x", "a"))
		functions.append(Monomial("a", terms, "a"))

		# 6)
		terms = []
		terms.append(ExpTerm("x", "a", "a"))
		terms.append(PolyTerm("x", "a"))
		#terms.append(LogTerm("x", "a", "a"))
		terms.append(LogTerm("x", 2, "a"))
		functions.append(Monomial("a", terms, "a"))
				
		# 7)
		terms = []
		#terms.append(LogTerm("x", "a", "a"))
		terms.append(ExpTerm("x", "a", "a"))
		terms.append(LogTerm("x", 2, "a"))
		functions.append(Monomial("a", terms, "a"))

		# 8)
		terms = []
		terms.append(ExpTerm("x", "a", "a"))
		functions.append(Monomial("a", terms, "a"))

		# 9)
		terms = []
		terms.append(ExpTerm("x", 2, "a"))
		terms.append(PolyTerm("x", "a"))
		functions.append(Monomial("a", terms, "a"))

		# 10)
		terms = []
		terms.append(ExpTerm("x", 2, "a"))
		terms.append(PolyTerm("x", "a"))
		terms.append(LogTerm("x", 2, "a"))
		functions.append(Monomial("a", terms, "a"))
				
		# 11)
		terms = []
		terms.append(ExpTerm("x", 2, "a"))
		terms.append(LogTerm("x", 2, "a"))
		functions.append(Monomial("a", terms, "a"))

		# 12)
		terms = []
		terms.append(ExpTerm("x", 2, "a"))
		functions.append(Monomial("a", terms, "a"))

		return functions

	@staticmethod
	def getTieBreakerUpperLimit(parComp, parRef, fromXValue, uptoYValue, threshold):
		curX = fromXValue
		minX, maxX = curX, None 
		evals = [0, 0]
		minDiference, minVal = 0.0, None
		pars = [parRef, parComp]
		while curX < 1e9 and (maxX == None or (minX < maxX)):
			if maxX == None:
				curX = curX * 2
			else:
				curX = (minX + maxX)//2
			i = 0
			for par in pars:
				varNames = par[1].split(",")
				varNames.append("x")
				varValues = list(par[3])
				varValues.append(curX)
				evals[i], i = evalFunction(par[0], varNames, varValues), i+1
			minVal = min(evals)
			minDiference = 0.0 if minVal == 0.0 else abs(evals[1]-evals[0])/minVal
			if minDiference < threshold:
				minX = curX+1
			else:
				maxX = curX
		return (maxX, evals[0])


	@staticmethod
	def getTieBreaker(parComp, parRef, fromXValue, uptoYValue, threshold):
		x = fromXValue
		(uptoXValue, timeuptoXValue) = FunctionPredictor.getTieBreakerUpperLimit(parComp, parRef, fromXValue, uptoYValue, threshold)
		if uptoXValue == None:
			return (None, None)
		step = max(1, int((uptoXValue-fromXValue)/25000.0))
		pars = [parRef, parComp]
		evals = [0.0, 0.0]
		while True:
			#print x, evals, uptoYValue
			i = 0
			for par in pars:
				varNames = par[1].split(",")
				varNames.append("x")
				varValues = list(par[3])
				varValues.append(x)
				evals[i], i = evalFunction(par[0], varNames, varValues), i+1
			minevals = min(evals)
			error = float("inf") if minevals == 0 else abs(evals[0]-evals[1])/min(evals)
			if error >= threshold:
				return (x, evals[0])
			elif evals[0] > uptoYValue or x > uptoXValue:
				return (None, None)
			else:
				x = x+step

	@staticmethod
	def isBetterMonomial(m1, m2, error1, error2):
		#m1 is better (simpler) than m2? OCAM rule:
		# 1. less number of variable parameters
		# 2. less number of terms
		# 3. less number of fixed parameters
		# 4. greater number of integer parameters
			
		def getTermCounters(aMonomial):
			(paramVars, paramValues) = aMonomial.getParams()
			npi = 0
			for (paramName, paramValue, paramObj) in paramValues:
				if paramName != "indep" and paramName != "coef" and paramValue == math.ceil(paramValue):
					npi = npi+1

			p, t, f = len(paramVars), len(aMonomial.terms), len(paramValues)
			return (p, t, f, npi)

		inverted = False
		if error1 > error2:
			m1, m2, error1, error2, inverted = m2, m1, error2, error1, True

		(p1, t1, f1, i1) = getTermCounters(m1)
		(p2, t2, f2, i2) = getTermCounters(m2)

		if p1 < p2 or (p1 == p2 and t1 < t2) or (p1 == p2 and t1 == t2 and f1 < f2) or \
				(p1 == p2 and t1 == t2 and f1 == f2 and i1 > i2) or \
				(p1 == p2 and t1 == t2 and f1 == f2 and i1 == i2 and error1 < error2):
			return not inverted
		else:
			return inverted

	@staticmethod
	def estimateParameters(resource, datafile, workingFolder, tieBreakMaxVal, equivalenceThreshold, discreteFunctionsOnly=False, printFunctionReport=False, possibleFunctions=None):
		TIEBREAK_THRESHOLD = 0.05
		minpar = None	
		pars = [] #each par = (functionStrNormal, parametersStr, error, [values], monomial)
		withoutParameters = []
		eqNum = 0
		if possibleFunctions==None:
			functions = FunctionPredictor.getPossibleFunctions()
		else:
			functions = possibleFunctions()
		iniLen = len(functions)
		generatedFuns = {}
		while eqNum < len(functions):
			function = functions[eqNum]
		 	
		 	functionStr = function.getExpr()
			startTime = datetime.now()
			Debug.log(1, "Fitting {0}/{1}... (function = {2})".format(eqNum+1, len(functions), functionStr), printFunctionReport)
			if not generatedFuns.has_key(functionStr):
				generatedFuns[functionStr] = True
				datafileValues = []
				maxNumberIter = function.getMaxNumberIter()
				par1 = FunctionPredictor.runEstimation(function, datafile, workingFolder, True, datafileValues, maxNumberIter)
				datafileValues = []			
				par2 = FunctionPredictor.runEstimation(function, datafile, workingFolder, False, datafileValues, maxNumberIter)
				if par1[0] == None:
					par = par2
				elif par2[0] == None:
					par = par1
				else:
					par = par1 if par1[2] < par2[2] else par2
				if par[0] == None:
					Debug.log(2, "Function could not be estimated.")
					withoutParameters.append(function)
				else:
					pars.append(par)

					if (not function.allowDiscretization()) or not discreteFunctionsOnly:
						if minpar == None or par[2] < minpar[2]:
							minpar = par

					#if eqNum < iniLen:
					if function.discretize:
						estimatedParamValues = FunctionPredictor.getDictParamValues(par[1], par[3])
						for disFunction in function.generateDiscreteValues(estimatedParamValues):
							if disFunction != None:
								functions.append(disFunction)

			Debug.log(1, "... fitted in {0} ms.".format(int(round(getRunningTime(startTime)))), printFunctionReport)
			eqNum = eqNum + 1
		
		Debug.log(1, "- - - - - - - - - - - - - - - - - -", printFunctionReport)
		Debug.log(1, "Resource: {0}".format(resource).upper(), printFunctionReport)
		Debug.log(1, "- - - - - - - - - - - - - - - - - -", printFunctionReport)
		feasibleTieBreakers, infeasibleTieBreakers, equivFunctions = [], [], []
		if minpar != None:
			maxEstimationError = FunctionPredictor.getEstimationError(datafileValues, minpar[0], 
					FunctionPredictor.getDictParamValues(minpar[1], minpar[3]), equivalenceThreshold)
			for par in pars:
				if par[2] <= maxEstimationError:
					equivFunctions.append(par)
				if minpar[2] == 0.0:
					percerror = float("inf")
				else:
					percerror = (par[2] - minpar[2])/minpar[2]
				if percerror > 0:
					lastPoint = datafileValues[len(datafileValues)-1]
					if tieBreakMaxVal != 0:
						(tiebreakerVal, tiebreakerEval) = FunctionPredictor.getTieBreaker(par, minpar, lastPoint[0], tieBreakMaxVal*lastPoint[1], TIEBREAK_THRESHOLD)
					else:
						(tiebreakerVal, tiebreakerEval) = (None, None)
					functionInfo = "(tiebreak: {0}; eval = {1})".format(tiebreakerVal, tiebreakerEval)
					functionInfo = ("  +%.2f{1}: {0} {2}" % (100*percerror)).format(par, "%", functionInfo)
					if tiebreakerVal != None:
						feasibleTieBreakers.append((par[2], functionInfo))
					else:
						infeasibleTieBreakers.append((par[2], functionInfo))

		Debug.log(1, "------------------------------------------------", printFunctionReport)
		Debug.log(1, "FEASIBLE to tie break: {0} functions (using {1}% as threshold and {2} as last value multiplier)".format(len(feasibleTieBreakers), 100*TIEBREAK_THRESHOLD, tieBreakMaxVal), printFunctionReport)
		feasibleTieBreakers = sorted(feasibleTieBreakers, key=lambda x: x[0])
		for (error, functionInfo) in feasibleTieBreakers:
			Debug.log(1, functionInfo, printFunctionReport)
		Debug.log(1, "------------------------------------------------", printFunctionReport)
		Debug.log(1, "UNFEASIBLE to tie break: {0} functions (using {1}% as threshold and {2} as last value multiplier)".format(len(infeasibleTieBreakers), 100*TIEBREAK_THRESHOLD, tieBreakMaxVal), printFunctionReport)
		infeasibleTieBreakers = sorted(infeasibleTieBreakers, key=lambda x: x[0])
		for (error, functionInfo) in infeasibleTieBreakers:
			Debug.log(1, functionInfo, printFunctionReport)
		Debug.log(1, "------------------------------------------------", printFunctionReport)
		Debug.log(1, "{0} functions could not have their parameters estimated".format(len(withoutParameters)), printFunctionReport)
		for function in withoutParameters:
			Debug.log(1, "  {0}".format(function.getExpr()), printFunctionReport)
		Debug.log(1, "------------------------------------------------", printFunctionReport)
		Debug.log(1, "MINIMUM ERROR function:", printFunctionReport)
		Debug.log(1, "  {0}".format(minpar), printFunctionReport)
		Debug.log(1, "------------------------------------------------", printFunctionReport)
		Debug.log(1, "EQUIVALENT: {0} functions (using {1}% as threshold)".format(len(equivFunctions), equivalenceThreshold*100), printFunctionReport)
		equivFunctions = sorted(equivFunctions, key=lambda x: x[2])
		parSimples = None
		for par in equivFunctions:
			Debug.log(1, "  {0}".format(par), printFunctionReport)
			if parSimples == None or FunctionPredictor.isBetterMonomial(par[4], parSimples[4], par[2], parSimples[2]): 
				parSimples = par
		Debug.log(1, "------------------------------------------------", printFunctionReport)
		Debug.log(1, "BEST-GUESS function:", printFunctionReport)
		Debug.log(1, "  {0}".format(parSimples), printFunctionReport)
		Debug.log(1, "------------------------------------------------", printFunctionReport)

		return parSimples

	def loadFunction(self, tieBreakMaxVal, discardValueUnder, case = "mean", equivalenceThreshold=0.005, discreteFunctionsOnly=False, printFunctionReport=False, possibleFunctions=None):
		caseIndex = 0 if case == "best" else 1 if case == "mean" else 2 if case == "worst" else -1
		if self.F == None or self.caseF != case:
			self.F, self.caseF = None, case
			if self.nary == 1:
				estimateFunctionFile = self.tempfolder + "estimateFunction.txt"
				f = open(estimateFunctionFile, "w")
				for point in self.points:
					if point[1][caseIndex] >= discardValueUnder:
						f.write(str(point[0]) + "\t" + str(point[1][caseIndex]) + "\n")
				f.close()
				L = []
				self.getFixedValues(L)
				self.F = FunctionPredictor.estimateParameters(self.resource, estimateFunctionFile, self.tempfolder, tieBreakMaxVal, equivalenceThreshold, discreteFunctionsOnly, printFunctionReport, possibleFunctions)
				Debug.log(3, (L, self.F))
			else:
				for (val, f) in self.F:
					f.loadFunction(tieBreakMaxVal, discardValueUnder, case, equivalenceThreshold, discreteFunctionsOnly, printFunctionReport, possibleFunctions)

	def estimate(self, values, tieBreakMaxVal, discardValueUnder, case = "mean", equivalenceThreshold=0.005, discreteFunctionsOnly=False, possibleFunctions=None):
		curVal = len(values) - self.nary
		if self.nary == 1:
			self.loadFunction(tieBreakMaxVal, discardValueUnder, case, equivalenceThreshold, discreteFunctionsOnly, printFunctionReport=False, possibleFunctions=possibleFunctions)
			if self.F != None:
				x = values[curVal]
				fstr = self.F[0]
				i = 0
				for var in self.F[1]:
					fstr, i = fstr.replace(var, self.F[3][i]), i+1
				return eval(fstr)
		else:
			file = open("estimate.txt", "w")
			for (val, f) in self.F:
				estimatedValue = f.estimate(values, tieBreakMaxVal, discardTimeUnder, case, equivalenceThreshold, discreteFunctionsOnly, printFunctionReport=False, possibleFunctions=possibleFunctions)
				if estimatedValue != None:
					file.write(str(val) + "\t" + str(estimatedValue) + "\n")
			file.close()
			par = FunctionPredictor.estimateParameters(self.resource, "estimate.txt", self.tempfolder, tieBreakMaxVal, equivalenceThreshold, discreteFunctionsOnly, printFunctionReport=False, possibleFunctions=possibleFunctions)
			if par != None:
				x = values[curVal]
				fstr = self.F[0]
				i = 0
				for var in self.F[1]:
					fstr, i = fstr.replace(var, self.F[3][i]), i+1
				return eval(fstr)
			else:
				return None

	def getFunctionsOnLastVar(self, listFunctions, tieBreakMaxVal, discardValueUnder, case="mean", equivalenceThreshold=0.005, discreteFunctionsOnly=False, filterFixedValues=None, printFunctionReport=False, possibleFunctions=None):
		if self.nary == 1:
			L = []
			self.getFixedValues(L)
			includeThisFunction = True
			if filterFixedValues != None:
				includeThisFunction = False
				for t in filterFixedValues:
					if t == L:
						includeThisFunction = True
						break
			if includeThisFunction:
				self.loadFunction(tieBreakMaxVal, discardValueUnder, case, equivalenceThreshold, discreteFunctionsOnly, printFunctionReport, possibleFunctions)
				if self.F != None:
					listFunctions.append((L, self.F))
		else:
			for (val, f) in self.F:
				f.getFunctionsOnLastVar(listFunctions, tieBreakMaxVal, discardValueUnder, case, equivalenceThreshold, discreteFunctionsOnly, filterFixedValues, printFunctionReport, possibleFunctions)


class Runner:
	"""
        -----------------------------------------------------------------------------------------------------------------------
	Class for interacting with EMA features.
        -----------------------------------------------------------------------------------------------------------------------
	Author: 
		Fabiano Oliveira (fabiano.oliveira@ime.uerj.br)
	Description:
		EMA - (EM)pirical (A)nalysis of algorithms
		Python library to empirically analyze the resource usage of algorithms.
        -----------------------------------------------------------------------------------------------------------------------
        The input for EMA consists of: 
          (i)   a program A to be analyzed; 
          (ii)  a list V = v_1, v_2,..., v_N of variables on which the A's usage of resources depend; and 
          (iii) a program B, which has a valuation f: V --> Nat of V as input and produces an input I of A in which 
                the variable v_i in I has the value f(v_i) for all 1 <= i <= N. 
        Although the following steps are not mandatory, the steps in EMA processing are generally the following: 
          (1) (calibration) for all 1 <= i <= N, determination of MAX_i such that the running time and memory space of A are limited to 
              certain values for all input I in which v_i <= MAX_i. 
              This phase uses the method getSuggestedVariableValues();
          (2) (simulation) definition of S_i C {1,...,MAX_i} for all 1 <= i <= N containing the values of v_i which will be analyzed: 
              for each (e_1,..., e_N) in S_1 x ... x S_N, B is executed to generate an input I of A in which v_i = e_i 
              for all 1 <= i <= N, following the execution of A having I as input and storing the usage of resources. 
              Therefore, EMA builds a data base with |S_1| . ... . |S_N| executions. 
              This phase uses the method runSimulation();
          (3) (analysis) through non-linear regressions, estimation of a functional form to the complexity of the usage of resources. 
              For the particular case of one-variable, if T(n) is the function corresponding the usage of resource required by A
              under input in which v_1 = n, EMA will determine the parameters which minimizes the sum of squared residuals of the function
                  
              T(n) = a_0 n**a_1 a_2**(n**a_3 (log n)**a_4) (log n)**a_5 + a_6.

              This phase uses the methods getResourceUsageFunction(), plotResourceUsage(), and estimateResourceUsage().
        -----------------------------------------------------------------------------------------------------------------------
	DEPENDENCIES: It is required to have GnuPlot (version 4.6) installed on the system. For download and installation instructions, see
	              http://www.gnuplot.info/download.html
	              (for Ubuntu users, just run "sudo apt-get install gnuplot" on terminal).
        -----------------------------------------------------------------------------------------------------------------------
	DISCLAIMER NOTICE: The team in charge of EMA can not be held responsible for the correctness, completeness or quality of the
	              software. It is offered for free as-is. Therefore, users may use EMA only if they accept being totally 
	              responsible for having EMA used whatever the purpose.
        -----------------------------------------------------------------------------------------------------------------------
	CHANGE LOG:
	3.0:
		- overall better accuracy for the BEST-GUESS function.
		- fixed getting free memory (in some cases, a wrong number was being determined).
		- fixed getting the amount of memory used for a process (taking into account subprocesses now).
		- when discretizing parameters, the set of generated discrete values has been enlarged. 
		- user can determine the family of functions on which the fit will be applied.
		- fixed a formatting issue with eps.
		- option to select the maximum number of iterations for regression analysis. 
	2.6:
		- EMA waits until a real core is available to run the algorithm
		- Number of logical and physical CPUs are read from the operating system (Linux only)
		- EMA reports in screen the usage of each resource right after execution
	2.5: 
		- Fixed standard deviation calculation (divisor from 'N' to 'N-1');
		- Outlier detection and configurable removal of mean and standard deviation calculations;
		- Added the parameter 'minimum number of samples';
		- Convergence Factor can now relate to any resource, not only "Time"
		- More function formats added to the fittness procedure.
		- More initial values in distinct order of magnitudes (to offer better chances of producing a better fitting). 
		- In shared computers for running EMA, there will be a maximum number of instances of EMA allowed to concurrently run,
		  given by max{1,cores/2}.
		- More customizations for graphs: 
			- graph size, line thickness, colors, font family, and customized captions in keys; 
			- numbers like '1.2e09' now appear as '1.2x10^9'
			- plot data within a specific x and/or y range
			- application of factors to customized resources values (e.g., to plot them as real values instead of integers) 
		        - encodings for labels
	2.4: 
		- Added support for outputting graphs in eps format.
		- Old graph files are backed up whiile outputting new graphs.
		- Added support for positioning the key on graphs and changing font family/size on them
		- Fixed issues related to running EMA in Windows.
		- Reporting execution time on screen with less frequency as the execution time gets longer
	2.3: 
		- Added independent term in a monomial so that the fitting can be more accurate.
		- Used allocated memory instead of resident memory as 'used memory' for counting memory consumption (Linux only).
		- Fixed terminology (Equation ==> Function)
		- The report of functions after estimation can be now requested to be printed out in the console through a 
		  parameter (and the report layout has been improved a little bit). 
		- Cosmetic changes in the chart layout (colors, line thickness, points, headers).
		- getResourceUsageFunction() now can set the error threshold so that a function is considered equivalent to that
		  of minimum-error.

        -----------------------------------------------------------------------------------------------------------------------
	"""
	
	def __filterDataLines(self, varindexes, values, fileToSave):
		f = open(fileToSave, "w")
		f.write(self.header + "\n")
		for (lineStr, lineValues) in self.lines:
			matched = True
			for i in range(len(varindexes)):
				if lineValues[self.varCols[varindexes[i]]] != str(values[i]):
					matched = False
					break
			if matched:
				f.write(lineStr + "\n") 
		f.close()

	def __getStepsPerSec(self):
		arq = "ema.rtu" 
		try:
			rtu = int(readFile(arq))
		except:
			print "Calculating running-steps per second... "
			t0 = datetime.now()
			j = 0.0
			for i in range(16000000):
				j = j + math.sqrt(i)
			dt = datetime.now() - t0
			rtu = int(round(float(16000000) / (dt.seconds + dt.microseconds/1000000.0)))
			f = open(arq, "w")
			f.write(str(rtu) + "\n")
			f.close()
			print "done [{0}  steps/sec].".format(rtu)
		return rtu

	def __init__(self, variableNames, databaseFolder = "./database/", customResources=[], diskInputQuota=50, sharedPathForMutex="~/../ema/"):
		"""
		Args:
		    variableNames: list of variable names on which the usage of resources depend.
		    databaseFolder: folder in which input, output, and temporary files created by EMA are stored. 
		    customResources: a list [("resourceName_1", "unit_1", "scale_factor_1"), ("resourceName_2", "unit_2", "scale_factor_2"), ...] 
		      of customized resources. The amount of each customized resource used in an execution of the algorithm should be
		      written in a special file specified by <usageFilename> (see <createInstance> in method 'runSimulation' documentation).
		      The amount of a customized resource used by the program is taken as the amount reported in <usageFilename> multiplied by
                      the scale factor of the respective resource. Therefore, a scale factor of 1 indicates that the usage of a resource is
                      exactly that read in <usageFilename>.
		    diskInputQuota: disk quota (in MB) for keeping files in input folder (when the quota is exceeded, it is restored by deleting the oldest files).
		    sharedPathForMutex: a public folder with read/write file permission so that EMA can synchronize several runnings on
		      a shared environment. If the path is inexistent, no control on the amount of concurrent instances of EMA is carried out.
		"""
		sharedPathForMutex = getPlatformFileFormat(sharedPathForMutex)
		databaseFolder =  getPlatformFileFormat(databaseFolder)

		waitTurnOnSharedEnv(sharedPathForMutex)
		self.content = None
		#customResources.insert(0, ("CPU", "ms", 1))
		self.customResources = customResources
		self.resources = [("Time", "ms", 1), ("Space", "KB", 1)] + customResources
		self.LOG_FILE = "ResourceUsage.txt"
		self.debugging = os.path.isfile("debug.txt")
		self.content = None #list of values corresponding to vars
		self.resourceF = None
		self.vars = variableNames
		self.varCols = [i for i in range(len(self.vars)-1)] # ith var -> real col
		self.colVars = [i for i in range(len(self.vars)-1)] # ith real col -> var
		self.databaseFolder = getCanonicalPath(databaseFolder)
		self.inputfolder = self.databaseFolder + "in" + os.sep
		self.outputfolder = self.databaseFolder + "out" + os.sep
		self.tempfolder = self.databaseFolder + "temp" + os.sep
		mkdir(self.databaseFolder)
		mkdir(self.inputfolder)
		mkdir(self.outputfolder)
		mkdir(self.tempfolder)
		self.diskInputQuota = diskInputQuota*(1024**2)
		self.originalFreeSpace = getDiskFreeSpace(self.inputfolder, True)
		self.stepsPerSec = self.__getStepsPerSec()
		
	def __loadContent(self, discardTimeUnder = 50):
		if self.content == None:
			self.content, self.lines = [], [] 
			contentStr = readFile(self.outputfolder + self.LOG_FILE)
			# header
			lines = contentStr.split("\n")
			self.header = lines[0]
			filevars = lines[0].split("\t")
			filevars = filevars[:len(self.vars)]
			self.varCols = []
			self.colVars = [None]*len(self.vars)
			for i in range(len(self.vars)):
				for j in range(len(self.vars)):
					if filevars[j] == self.vars[i]:
						self.varCols.append(j) 
						self.colVars[j] = i   
						break
			#filevars = lines[0].split("\t")
			beginResources = len(self.vars)
			colExecStatus = beginResources + 4*(len(self.resources))
			# data
			lines = lines[1:]
			for line in lines:
				if line != "":
					linel = line.split("\t")
					if linel[colExecStatus] == "0":
						self.lines.append((line, linel))
						values = []
						for i in self.varCols:
							values.append(int(round(float(linel[i]))))
						for i in range(beginResources, colExecStatus-1, 4):
							vals = [int(round(float(linel[i]))), int(round(float(linel[i+1]))), int(round(float(linel[i+2])))]
							values.append(vals)
						if values[len(self.vars)][1] >= discardTimeUnder:
							self.content.append(values)
	
	def plotResourceUsage(self, resource, discardTimeUnder = 50, title="", mode = "windows", style="lines", showStdDev=True, 
		cases = (0,1,0), usageFunction = None, exportToFolder = "", exportToFormat="eps", appendToPlot="", multiplotTitle="",
		autoColor=False, customColors = None, keyPosition="center right", size=(1000,400), fontFamily=("Helvetica",10), lineWidth=4, 
		rangeTics=(None,None), scientificDecimals=(None,None), translations=None, labelsEncoding="utf8"):
		"""
		Generates a plot with the usage of resources. Returns a string that represent a graph for EMA.
		Args:
		    resource: resource name ("Time", "Space", or a customized name)
		    discardTimeUnder: Discard any execution for which the resource usage is below <discardTimeUnder> (in ms).
		    mode: 
		        windows = assume a graphical interface environment (the ploting is rendered using GUI objects)
		        term = assume a terminal environment (the ploting is carried out as ASCII symbols)
		    style: 
		        lines = the values are represented as points connected with line segments
		        intervals = if more than one case is to be plotted, they are connected with a vertical line
		        points = the values are represented as points
		    showStdDev: boolean value indicating whether standard deviation is to be shown
		    cases: 3-binary-tuple, indicating respectively whether the worst, mean, and best cases are to be plotted.
		    usageFunction: function of the estimated usage of resources. (See getResourceUsageFunction() method to check each function's format. 
		        If informed, the function is plotted in the same graph as the data.
		    exportToFolder: folder into which the plots will be written. When it is informed, the graph will be plotted only in the file.
		    exportToFormat: format to export (see 'set terminal' options in gnuplot).
		    appendToPlot: a string returned from plotResourceUsage() representing a graph to which the current graph should be 
		        plotted together.
		    multiplotTitle: when using multiplotting (<appendToPlot> != ''), <multiplotTitle> is a string to be prefixed in every
		        label of this graph so that each label in the union of labels remains distinct from all others. 
		    autoColor: when using multiplotting (<appendToPlot> != ''), autoColor determines if each new plot appended should 
		        have their coloring done automatically or, otherwise, should keep the original color specification of each new
		        appended plot
		    customColors: when autoColor is disabled, this changes the default colors. The value should be a dictionary
			{"green": <new color>, "blue": <new color>, "red": <new color>}
		    keyPosition: where the keys are to be placed ('X Y', where X in {'top',<'center'>,'below'} and Y='left'/'center'/<'right'>)
		    size: (width,height) of the graph
		    fontFamily: (name,size) of the font to write the labels
		    lineWidth: width of estimation curve
		    rangeTics: ((xmin,xmax),(ymin,ymax)); let a particular (min,max) range as None to let it be automatic
		    scientificDecimals: (<number of decimals for x>, <number of decimals for y>); use None to a particular number of decimals to
			let a particular axis in automatic mode
		    translations: dictionary of pairs of strings 'original --> translation' for automatic captions (e.g.: Time, Space, average, etc.)
		    labelsEncoding: encoding used in strings for labels
		"""
		def translate(text):
			if translations != None:
				if translations.has_key(text):
					return translations[text]
			return text

		def translateColor(color):
			if customColors != None:
				if customColors.has_key(color):
					return customColors[color]
			return color

		lineTypes = [None, 6, 9, 1, 2, 3, 4, 5] + [i for i in range(10, 100)]

                ciferEscape = "" if platform.system() == "Windows" else "\\"

		self.__loadContent(discardTimeUnder)
		self.__loadResourcePredictors()
		resourceId = self.__getResourceId(resource)
		resourceUnit = self.__getResourceUnit(resource)
		resourceFactor = self.__getResourceFactor(resource)

		plotId = appendToPlot[0]+1 if appendToPlot != "" else 1
		appendToPlot = appendToPlot[1] + "," if appendToPlot != "" else ""
		
		def getFixedValuesKey(values):
			key = ""
			for val in values:
				key = key + str(val) + "-"
			return key
			
		strMode = ""
		if exportToFormat == "eps":
			termType = "postscript eps solid size {0},{1} enhanced color font '{2},{3}'".format(size[0]/100,size[1]/100,fontFamily[0],2*fontFamily[1]) #size in inches = pixels/100
		else:
			termType = "pngcairo size {0},{1} enhanced font '{2},{3}'".format(size[0],size[1],fontFamily[0],fontFamily[1]) 
		extension = exportToFormat
		if exportToFolder != "":
			exportToFolder = getCanonicalPath(exportToFolder)
			mkdir(exportToFolder)
			#strMode = "set term {0} size 1000,400;set output '{1}{2}.{0}';".format(exportToFormat, exportToFolder, resource)
			#		set grid back linestyle 81; \
			#		set border 3 back linestyle 80; \

					#set style line 1 lt rgb '#A00000' lw 2 pt 1;\
					#set style line 2 lt rgb '#00A000' lw 2 pt 6;\
					#set style line 3 lt rgb '#5060D0' lw 2 pt 2;\
					#set style line 4 lt rgb '#F25900' lw 2 pt 9;\
					#set style line 80 lt rgb '#808080'; \
					#set style line 81 lt 0; \
					#set style line 81 lt rgb '#808080'; \
			outputFile = "{0}{1}.{2}".format(exportToFolder, resource, extension)
			backup(outputFile)
			strMode = "set encoding " + labelsEncoding + ";set term {0};set output '{1}';" + \
					"set xtics nomirror;" + \
					"set ytics nomirror;"
                        strMode = strMode.format(termType, outputFile)
			if scientificDecimals != None and scientificDecimals[0] != None:
				strMode = strMode + "set format x '%." + str(scientificDecimals[0]) + "t{/Symbol \\327}10^{%L}';"
			if scientificDecimals != None and scientificDecimals[1] != None:
				strMode = strMode + "set format y '%." + str(scientificDecimals[1]) + "t{/Symbol \\327}10^{%L}';"
			if rangeTics != None and rangeTics[0] != None:
				strMode = strMode + "set xrange [{0}:{1}];".format(rangeTics[0][0],rangeTics[0][1])
			if rangeTics != None and rangeTics[1] != None:
				strMode = strMode + "set yrange [{0}:{1}];".format(rangeTics[1][0],rangeTics[1][1])
			

		elif mode != "windows":
			strMode = "set term dumb;"
			
		plotterCommand = ""
	
		outfile = self.outputfolder + self.LOG_FILE
		basetempfile = self.tempfolder + self.LOG_FILE
		cmdPlot = ""
		fixedValues = []
		
		keys = {}

		for values in self.content:
			curFixedValues = values[:len(self.vars)-1]
			key = getFixedValuesKey(curFixedValues)
			if not keys.has_key(key):
				if usageFunction != None:
					fns = None
					for iEq in range(len(usageFunction)):
						if usageFunction[iEq][0] == curFixedValues:
							fns = usageFunction[iEq][1]
							break
					keys[key] = fns
				else:
					keys[key] = True
				fixedValues.append(curFixedValues)
				
		baseMeanIndex = len(self.vars) + 2 + 4*resourceId
			
		for i in range(len(fixedValues)):
			cmdPlotStr = ""
			tempfile = basetempfile + "." + str(resourceId) + "." + str(i)
			self.__filterDataLines([j for j in range(len(fixedValues[i]))], fixedValues[i], tempfile)
			serieStr = ""
			if len(fixedValues) > 1:
				for z in range(len(self.varCols)-1):
					serieStr = serieStr + "{0}={1};".format(self.vars[z], fixedValues[i][z])
				serieStr = serieStr[:len(serieStr)-1]
			if multiplotTitle != "":
				if serieStr == "":
					serieStr = multiplotTitle
				else:
					serieStr = multiplotTitle + " - " + serieStr
			serieStr = " " + serieStr if serieStr != "" else ""

			if showStdDev:
				cmdPlotStr = cmdPlotStr + "'{0}' using {2}:({7}*(" + ciferEscape + "${4}-" + ciferEscape + "${6})):({7}*(" + ciferEscape + "${4}+" + ciferEscape + "${6})) every ::1 with filledcurves lt rgb '#c9c9cf' title '" + translate("std dev") + "'," 

			if style == "lines" or style == "points":
				styleGraph = "with linespoint " if style == "lines" else ""
				if cases[0]:
					cmdPlotStr = cmdPlotStr + "'{0}' using {2}:({7}*" + ciferEscape + "${3}) every ::1  {1}title '" + translate("best") + serieStr + "' " + ("lt rgb '{2}'" if not autoColor else "").format(translateColor("green")) + " lw {1} pt {0},".format(lineTypes[plotId], lineWidth) 
				if cases[1]:
					cmdPlotStr = cmdPlotStr+ "'{0}' using {2}:({7}*" + ciferEscape + "${4}) every ::1 {1}title '" + translate("average") + serieStr + "' " + ("lt rgb '{0}'" if not autoColor else "").format(translateColor("blue")) + " lw {1} pt {0},".format(lineTypes[plotId], lineWidth)
				if cases[2]:
					cmdPlotStr = cmdPlotStr + "'{0}' using {2}:({7}*" + ciferEscape + "${5}) every ::1  {1}title '" + translate("worst") + serieStr + "' " + ("lt rgb '{2}'" if not autoColor else "").format(translateColor("red")) + " lw {1} pt {0},".format(lineTypes[plotId], lineWidth)
			
			elif style == "intervals":

				cmdPlotStr = cmdPlotStr + "'{0}' using {2}:({7}*" + ciferEscape + "${4}):({7}*" + ciferEscape + "${3}):({7}*" + ciferEscape + "${5}) every ::1 with yerrorbars title '" + serieStr + "'," 
				styleGraph = ""

			if usageFunction != None:
				fns = keys[getFixedValuesKey(fixedValues[i])]
				if fns != None:
					function = FunctionPredictor.getConcreteFunction(fns)
					eqTitle = serieStr + translate(" (est.)") if serieStr != "" else translate("estimation")
					#color = "black" if style != "intervals" else "blue"
					#cmdPlotStr = cmdPlotStr + "{0} title '{1}' lt rgb '{2}',".format(function, eqTitle, color)
					color = "lt rgb '" + translateColor("blue") + "'" if not autoColor else ""     #if style != "intervals" else "blue"
					cmdPlotStr = cmdPlotStr + "{4}*({0}) title '{1}' {2} lw {3},".format(function, eqTitle, color, lineWidth, resourceFactor)
			cmdPlot = cmdPlot + cmdPlotStr.format(tempfile, styleGraph, self.varCols[len(self.vars)-1]+1, baseMeanIndex-1, baseMeanIndex, baseMeanIndex+1, baseMeanIndex+2, resourceFactor)

		cmdPlot = cmdPlot[:len(cmdPlot)-1]
		resourceStr = translate(resource) if translate(resource) != "" else ""		 
		titleStr = translate(resource) if title == "" else title

		cmdPlot = appendToPlot + cmdPlot
		unitStr = "({0})".format(translate(resourceUnit)) if translate(resourceUnit) != "" else ""		 
		plotterCommand = "gnuplot " + ("-p " if exportToFolder == "" else "") + "-e \"set grid;set key outside {6};set title '{3}';set xlabel '{1}';set ylabel '{4} {5}';{0}plot {2}\""
		plotterCommand = plotterCommand.format(strMode, translate(self.vars[len(self.vars)-1]), cmdPlot, titleStr, 
			translate(resource), unitStr, keyPosition)
		Debug.log(1, plotterCommand + "...")

		os.system(plotterCommand)

		return (plotId, cmdPlot)

	def __loadResourcePredictors(self):
		if self.resourceF == None:
			Debug.log(1, "starting resource prediction...")
			self.resourceF = [None]*(len(self.resources))
			i, j = 0, len(self.vars)
			for (rname, runit, factor) in self.resources:
				self.resourceF[i] = FunctionPredictor(rname, None, None, len(self.vars), self.tempfolder)
				for values in self.content:
					#print "values = {0}, j = {1}, vars = {2}".format(values, j, self.vars)
					valuesToAdd = values[:len(self.vars)] + [values[j]]
					Debug.log(1, valuesToAdd)
					self.resourceF[i].addValuePoint(valuesToAdd)
				i, j = i+1, j+1
			Debug.log(1, "done.")

			
	def __getResourceId(self, resource):
		i = 0
		for (rname, unit, factor) in self.resources:
			if resource == rname:
				return i
			i = i+1
		return -1

	def __getResourceUnit(self, resource):
		resourceId = self.__getResourceId(resource)
		return self.resources[resourceId][1]

	def __getResourceFactor(self, resource):
		resourceId = self.__getResourceId(resource)
		return self.resources[resourceId][2]
			
	def estimateResourceUsage(self, resource, values, discardTimeUnder=50, equivalenceThreshold=0.005, tieBreakMaxVal=2, discreteFunctionsOnly=False, possibleFunctions=None):
		"""
		Predicts the resource usage under a given input. 
		Args:
		    resource: resource name ("Time", "Space", or a customized name)
		    values: List of variable values to be given as input. 
		    discardTimeUnder: Discard any execution for which the resource usage is below <discardTimeUnder> (in ms).
		    equivalenceThreshold: Maximum error threshold on each evaluation so that a function can be considered equivalent to that of minimum error.
		    tieBreakMaxVal: Tie break factor to be used in determining the funcions of usage of resources.
		    discreteFunctionsOnly: Boolean value indicating whether only discrete functions should be considered
		    possibleFunctions: function to return the set of functions on which the fit will proceed (if None, the function 'getPossibleFunctions()' 
		        defined in EMA module will be used -- check such a function as guidance to create your own). 
		"""
		self.__loadContent(discardTimeUnder)
		self.__loadResourcePredictors()
		resourceId = self.__getResourceId(resource)		
		return int(round(self.resourceF[resourceId].estimate(values, discardTimeUnder, tieBreakMaxVal, equivalenceThreshold, discreteFunctionsOnly, possibleFunctions)))

	def getResourceUsageFunction(self, resource, discardTimeUnder=50, case="mean", equivalenceThreshold=0.005, tieBreakMaxVal=2, discreteFunctionsOnly=False, filterFixedValues=None, printFunctionReport=False, possibleFunctions=None, maxNumberIter=0):
		"""
		Returns a function that estimates the usage of the given resource. A function consists of a list [t_1,...,t_T] of tuples, where 
	            t_j = ([pv_1,...,pv_(N-1)], (fnStr, 'p_1,p_2,...p_P', error, [v_1, v_2,...,v_P])), where
	              pv_i = this function corresponds to the usage of resource when the i-th variable value is fixed in 
	                  the value <pv_i>. In other words: if the usage of resource corresponds to the function F(var_1,...,var_N), 
	                  then t_j describes the function G(var_N) = F(pv_1,...,pv_(N-1),var_N).
	              fnStr = function string of G(var_N), where var_N is generically represented by x in <fnStr>.
	              p_i = parameter used in <fnStr>.
	              error = sum of square of residuals of <fnStr>.
	              v_i = value of parameter <p_i> in <fnStr>.

		Args:
		    resource: resource name ("Time", "Space", or a customized name)
		    discardTimeUnder: Discard any execution for which the time usage is below <discardTimeUnder> (in ms).
		    case: case type for analysis
		        worst = maximum usage
		        mean  = average usage
		        best  = minimum usage
		    equivalenceThreshold: Maximum error threshold on each evaluation so that a function can be considered equivalent to that of minimum error.
		    tieBreakMaxVal: Tie break factor to be used in determining the funcions of usage of resources.
		    discreteFunctionsOnly: Boolean value indicating whether only discrete functions should be considered. 
		    filterFixedValues: list [t_1,t_2,...], where t_i = [e_1,...,e_(N-1)] with the values of the first N-1 variables.
			When informed, only data having the first N-1 variables valued as t_i, for some i, is to be shown.		     
		    printFunctionReport: Boolean value indicating whether all candidate functions and their respective estimations must be printed in the console.
		    possibleFunctions: function to return the set of functions on which the fit will proceed (if None, the function 'getPossibleFunctions()' 
		        defined in EMA module will be used -- check such a function as guidance to create your own). 
		"""
		if printFunctionReport:
			printPhaseHeader("EMA version {0}".format(getVersion()))

		self.__loadContent(discardTimeUnder)
		self.__loadResourcePredictors()
		L = []
		resourceId = self.__getResourceId(resource)

		def getCustomizedFunctions():
			if possibleFunctions==None:
				fs = FunctionPredictor.getPossibleFunctions()
			else:
				fs = possibleFunctions()
			for f in fs:
				f.maxNumberIter = maxNumberIter
			return fs

		Debug.log(1, "")
		Debug.log(1, "***** Determining {0} functions... ***** ".format(resource.upper()))
		Debug.log(1, "")
		self.resourceF[resourceId].getFunctionsOnLastVar(L, tieBreakMaxVal, discardTimeUnder, case, equivalenceThreshold, discreteFunctionsOnly, filterFixedValues, printFunctionReport, getCustomizedFunctions)
		return L

	def __logHeaders(self):
		f = open(self.outputfolder + self.LOG_FILE, "a")
		for var in self.vars:
			f.write(var + "\t")
		for (rname, unit, factor) in self.resources:
			f.write("Min {0} ({1}){2}\tMean {0} ({1}){2}\tMax {0} ({1}){2}\tStd Dev\t".format(rname, unit,"" if factor == 1 else " [x {0}]".format(factor)))
			#f.write("Min {0} ({1})\tMean {0} ({1})\tMax {0} ({1})\tStd Dev\t".format(rname, unit,factor))
		f.write("Exec Status\tExec DateTime\n")
		f.close()

	def __logTime(self, values, mindt, meandt, maxdt, stddev, success):
		key = ""
		for val in values:
			key = key + str(val) + "\t"

		fcontent = readFile(self.outputfolder + self.LOG_FILE)
		
		startLine = fcontent.find(key)
		keyExists = startLine > 0 and fcontent[startLine-1] == "\n"
		lineStr = key
		for i in range(len(meandt)):
			lineStr = lineStr + \
				str(int(round(mindt[i]))) + "\t" + \
				str(int(round(meandt[i]))) + "\t" + \
				str(int(round(maxdt[i]))) + "\t" + \
				str(int(round(stddev[i]))) + "\t" 
		lineStr = lineStr + str(success) + "\t" + \
				datetime.now().strftime("%d/%m/%y %H:%M:%S") + "\n"
		if keyExists:
			endLine = fcontent.find("\n", startLine)
			f = open(self.outputfolder + self.LOG_FILE, "w")
			f.write(fcontent[:startLine] + fcontent[endLine+1:] + lineStr)
			f.close()			
		else:
			f = open(self.outputfolder + self.LOG_FILE, "a")
			f.write(lineStr)
			f.close()

	def __getValuesString(self, curValues):
		str = ""
		for i in range(len(self.vars)):
			if i > 0:
				str = str + ";"
			str = str + "{0}={1}".format(self.vars[i], curValues[i])
		return str

	def __getFilename(self, curValues, sampleNum, inputfolder):
		inputfolder = getCanonicalPath(inputfolder)
		filename = ""
		for i in range(len(curValues)):
			if filename != "":
				filename = filename + "_"
			filename = filename + self.vars[i] + "-" + str(curValues[i])
		filename = filename + "__S-" + str(sampleNum) + ".input"
		return inputfolder + filename

	def __getStatsRemovingOutliers(self, samples, resourcesToVerify):
		#return (minr[1..R], meanr[1..R], maxr[1..R], stddevr[1..R]) for R = |resources| 
		#(outliers in resources given by resourcesToVerify are ignored for computing the stats)
		
		def getFences(S, threshold):
			def getith(S,i):
				i = i-1
				iint = int(i)
				ifrac = i - iint
				r = S[iint] 
				if ifrac > 0:
					r = r + ifrac*(S[iint+1]-S[iint])
				return r
			S.sort()
			n = len(S)
			median = getith(S, 0.5*(n+1))
			q1 = getith(S, 0.25*(n+1))
			q3 = getith(S, 0.75*(n+1))
			iq = q3-q1
			fences = (q1-threshold*iq, q3+threshold*iq)
			return fences

		minr,meanr,maxr,stddevr = [None]*len(self.resources),[None]*len(self.resources),[None]*len(self.resources),[None]*len(self.resources)

		for r in self.resources:
			rId = self.__getResourceId(r[0])
			S = [sample[rId] for sample in samples]			
			S.sort()
			if len(samples) >= 3:
				fences = getFences(S,1.5)
				Sf = [ s for s in S if s >= fences[0] and s <= fences[1] ]
			else:
				Sf = S
			if len(Sf) < len(S):
				print " * outliers found and {2} for resource {0}: {1}".format(r[0], len(S)-len(Sf), "removed" if r[0] in resourcesToVerify else "kept")
				Debug.log(2, "{1} of outliers in sample for {0}:".format(r[0],"Removal" if r[0] in resourcesToVerify else "Simulation of removal"))
				Debug.log(2, "Before = {0}".format(S))
				Debug.log(2, "After = {0}".format(Sf))
			if not r[0] in resourcesToVerify:
				Sf = S

			minr[rId],maxr[rId] = Sf[0],Sf[-1]
			for i in range(len(meanr)):
				meanr[rId] = sum(Sf)/float(len(Sf))
			stddevr[rId] = 0.0
			if len(Sf) > 1:
				for s in Sf:
					stddevr[rId] = stddevr[rId] + (s - meanr[rId])**2
				stddevr[rId] = math.sqrt(stddevr[rId]/float(len(Sf)-1))

		return (minr,meanr,maxr,stddevr)

	def __checkCPUAndWait(self, waitForFreeCPU):
		NUM_OF_CHECK = 5
		if waitForFreeCPU:
			n = 0; alreadyFailed = False; alreadyChecked = False
			while (not alreadyChecked) or (alreadyFailed and n < NUM_OF_CHECK):
				alreadyChecked = True
				cu = Environ.getCPUUsage()
				(ccl,ccr) = getNumOfCPUs()
				cl = 25.0 if ccr == 1 else 100.0*ccr/ccl - 20.0/ccl  #100.0*(2/4) - 20.0/4
				cl = int(cl)
				if cu > cl:
					alreadyFailed = True
					n = 0
					print " * waiting until CPU usage decreases (current = {0}%, threshold = {1}%)".format(cu, cl)
					time.sleep(5)
				else:
					n = n+1
					if alreadyFailed:
						print " * checking whether CPU usage is still low... (current = {0}%, threshold = {1}%, attempt = {2}/5)".format(cu, cl, n)
						if n < NUM_OF_CHECK:						
							time.sleep(5)

	def __execute(self, timeLimit, memoryLimit, valuesLimit, curValues, createInstance, samplingConvergenceFactor, minNumOfSamples, maxNumOfSamples, discardOutliers, traceUsageOfMemoryType="allocated", waitForFreeCPU=True):
		dta = [0.0]*(len(self.resources))
		samples = []
		exitcode = 0
		minRes, meanRes, maxRes = [float("inf")]*(len(self.resources)), [0.0]*(len(self.resources)), [-1]*(len(self.resources))
		stddev = [0.0]*(len(self.resources))
		if valuesLimit != None:
			for i in range(len(curValues)):
				if curValues[i] > valuesLimit[i]:
					print(" * variable exceeded the maximum value allowed! (var = {0}, curVal = {1}, limit = {2})".format(i, curValues[i], valuesLimit[i]))
					exitcode = "resourceLimit [maxValue]"
		convergenceResource = self.__getResourceId(samplingConvergenceFactor[0])
		if exitcode == 0: 
			numSamples = 0
			oldMean, curMean, meanDeviation = None, None, None
			strMeanDeviation = " -- " 
			while (numSamples < minNumOfSamples) or ((numSamples < maxNumOfSamples) and (oldMean == None or meanDeviation == None or abs(meanDeviation) > samplingConvergenceFactor[1])):
				numSamples = numSamples+1
				inputFile = self.__getFilename(curValues, numSamples, self.inputfolder)
				usageFile = inputFile + ".usage"
				cpuFile = inputFile + ".cpu"
				parameters = []
				if os.path.isfile(inputFile) and os.path.isfile(inputFile + ".ok"):
					print(" * input instance for [{0}] -- sample {1} found!".format(self.__getValuesString(curValues), numSamples))
				else:
					nunOfDeletedFiles = freeDiskSpace(self.originalFreeSpace-self.diskInputQuota, self.inputfolder)
					if nunOfDeletedFiles > 0:
						print(" * deleted {0} old input instances for cleaning up space.".format(nunOfDeletedFiles))
					print(" * creating input instance for [{0}] -- sample {1}...".format(self.__getValuesString(curValues), numSamples))
					f = open(inputFile, "w")
					createInstance(self.vars, curValues, f, parameters, usageFile)
					fp = open(inputFile + ".parameters", "w")
					for par in parameters:
						fp.write(str(par) + " ")
					fp.close()
					fp = open(inputFile + ".ok", "w")
					fp.write(" ")
					fp.close()
					f.close()
				if self.RUN_STATEMENT != "":
					rm(usageFile) #; rm(cpuFile)
					self.__checkCPUAndWait(waitForFreeCPU)
					print(" * running '{1}' for [{0}] -- sample {2}".format(self.__getValuesString(curValues), self.RUN_STATEMENT, numSamples))
					if platform.system() == "Windows":
						str_prerunner = ""
					else:
						#str_prerunner = '/usr/bin/time -f "%U %S" -o {0} '.format(cpuFile)
						str_prerunner = "exec "
					output_redir = ""
					str_parameters = ""
					if os.path.isfile(inputFile + ".parameters"):
						str_parameters = " " + readFile(inputFile + ".parameters")
					if os.path.isfile(inputFile):
						output_redir = " <" + inputFile
					command = Command(str_prerunner + self.RUN_STATEMENT + str_parameters + output_redir)
					t0 = datetime.now()
					resultcode = command.run(timeLimit, memoryLimit, self.tempfolder)
					dt = datetime.now() - t0
					if isinstance(resultcode, basestring):
						exitcode = resultcode
					elif not isinstance(exitcode, basestring):
						exitcode = exitcode | resultcode
					dt = int(round(((dt.days*24*60*60 + dt.seconds)*1000 + dt.microseconds/1000.0)))
					sample = []
					sample.append(dt)
					dmem = command.maxUsedMemory if traceUsageOfMemoryType=="allocated" else command.maxLoadedMemory
					dmem = int(round(dmem))
					sample.append(dmem)
					samples.append(sample)
					dta[0], dta[1] = dta[0]+dt, dta[1]+dmem
					minRes[0], minRes[1], maxRes[0], maxRes[1] = min(minRes[0], dt), min(minRes[1], dmem), max(maxRes[0], dt), max(maxRes[1], dmem)
					
					contUsage = []
					#cpuUsage = 0
					#if os.path.isfile(cpuFile):
					#	contentusage = readFile(cpuFile).split()
					#	if len(contentusage) > 0:
					#		cpuUsage = int(round(1000*(float(contentusage[0])+float(contentusage[1]))))
					#contUsage.append(cpuUsage)	
					if os.path.isfile(usageFile):
						contentusage = readFile(usageFile)
						for lineusage in contentusage.split("\n"):
							if lineusage != "":
								contUsage.append(int(lineusage))
					
					for i in range(len(self.customResources)):
						usage = 0 if i >= len(contUsage) else contUsage[i]
						minRes[2+i], maxRes[2+i] = min(minRes[2+i], usage), max(maxRes[2+i], usage)
						dta[2+i] = dta[2+i] + usage
						sample.append(usage)

					strUsage = " * resource usage: " # * Resource usage: Time=[] ms; Space=[] KB; <Name1>=[*Factor1] <Unit1>"
					for i in range(len(self.resources)):
						strUsage = strUsage + "{0}=[{1}] {2}; ".format(self.resources[i][0], self.resources[i][2]*sample[i], self.resources[i][1])
					print strUsage

					if curMean == None:
						oldMean, curMean, meanDeviation = None, float(sample[convergenceResource]), None
					else:
						oldMean, curMean = curMean, curMean * (numSamples-1)/float(numSamples) + sample[convergenceResource]/float(numSamples)
						meanDeviation = (curMean-oldMean)/oldMean
						strMeanDeviation = "%.3f"%(meanDeviation*100)
						print(" * sample mean variation: {0}% ({1})".format(strMeanDeviation,samplingConvergenceFactor[0]))


			if self.RUN_STATEMENT != "":
				(minRes,meanRes,maxRes,stddev) = self.__getStatsRemovingOutliers(samples, discardOutliers)
			else:
				exitcode = "notrun"
		
		return (curValues, minRes, meanRes, maxRes, stddev, exitcode)

	def __runSimulationBackTrack(self, myValueSeries, curVar, curValues, createInstance, samplingConvergenceFactor, minNumOfSamples, maxNumOfSamples, discardOutliers, traceUsageOfMemoryType):
		if curVar > len(self.vars):
			(curValues, minRes, meanRes, maxRes, stddev, exitcode) = self.__execute(0, 0, None, curValues, createInstance, samplingConvergenceFactor, minNumOfSamples, maxNumOfSamples, discardOutliers, traceUsageOfMemoryType)
			if exitcode != "notrun":
				self.__logTime(curValues, minRes, meanRes, maxRes, stddev, exitcode)
		else:
			for i in range(1, len(myValueSeries[curVar-1])+1):
				curValues.append(myValueSeries[curVar-1][i-1])
				self.__runSimulationBackTrack(myValueSeries, curVar+1, curValues, createInstance, samplingConvergenceFactor, minNumOfSamples, maxNumOfSamples, discardOutliers, traceUsageOfMemoryType)
				curValues.pop()

	def __getCloseVariableValuesForTimeLimit(self, minVarValues, maxVarValues, timeLimit, memoryLimit, createInstance, samplingConvergenceFactor, minNumOfSamples, maxNumOfSamples, discardOutliers, gapToOptimal):
		N = len(self.vars)
		curValues = [0]*N
		curMin = [ minVarValues[i] for i in range(N) ]
		prevValues = [ curMin[i] for i in range(N) ]
		minInterval, maxInterval = None, None
		for i in range(N):
			curInterval = maxVarValues[i] - curMin[i]
			if minInterval == None or minInterval > curInterval:
				minInterval, minPos = curInterval, i
			if maxInterval == None or maxInterval < curInterval:
				maxInterval, maxPos = curInterval, i

		numOfSteps = float(int(math.log(minInterval, 2)))+1
		stepIncrement = [ (maxVarValues[i]-curMin[i]+1)/(2**(numOfSteps-1)) for i in range(N) ]
		nextStep = [ stepIncrement[i] for i in range(N) ]
		alreadytimedout = False
		for i in range(N):
			curValues[i] = 0

		while not alreadytimedout:
			for i in range(N):
				prevValues[i] = curValues[i]
				curValues[i] = curMin[i] + int(nextStep[i]) - 1

			(temp, minRes, meanRes, maxRes, stddev, exitcode) = self.__execute(timeLimit, memoryLimit, maxVarValues, curValues, createInstance, samplingConvergenceFactor, minNumOfSamples, maxNumOfSamples, discardOutliers)
			alreadytimedout = isinstance(exitcode, basestring)
			if alreadytimedout:
				minV = [ prevValues[i] if prevValues[i] != 0 else curMin[i] for i in range(N) ]
				maxV = [ curValues[i] for i in range(N) ]
				minB, maxB = minV[maxPos], maxV[maxPos]
				m = (minB+maxB)/2
				for i in range(N):
					prevValues[i] = minV[i]
					curValues[i] = int(round(minV[i] + float(m - minV[maxPos] + 1)/(maxV[maxPos]-minV[maxPos]+1)*(maxV[i]-minV[i]+1)))
				gap = 1.0
				while minB <= maxB and gap > gapToOptimal:
					(temp, minRes, meanRes, maxRes, stddev, exitcode) = self.__execute(timeLimit, memoryLimit, maxVarValues, curValues, createInstance, samplingConvergenceFactor, minNumOfSamples, maxNumOfSamples, discardOutliers)
					if isinstance(exitcode, basestring):
						maxB = m - 1
					else:
						minB = m + 1
						for i in range(N):
							prevValues[i] = curValues[i]
					if minB <= maxB:
						m = (minB+maxB)/2
						for i in range(N):
							curValues[i] = int(round(minV[i] + float(m - minV[maxPos] + 1)/(maxV[maxPos]-minV[maxPos]+1)*(maxV[i]-minV[i]+1)))
					gap = float(maxB - minB + 1)/(maxV[maxPos] - minV[maxPos] + 1)
					print "Gap: {0}%".format(int(round(100*gap)))
				for i in range(N):
					curMin[i] = prevValues[i]

			else:
				for i in range(N):
					nextStep[i] = nextStep[i] * 2
	
		return curMin

	def __checkIfApproximateTime(self, time, curValues, memoryLimit, maxVarValues, createInstance, allowFactorToApprox, gapToOptimal):

		samplingConvergenceFactor, minNumOfSamples, maxNumOfSamples, discardOutliers = ("Time",0), 1, 1, []

		(temp, minRes, meanRes, maxRes, stddev, exitcode) = self.__execute(time*(1.0+allowFactorToApprox), memoryLimit, maxVarValues, curValues, createInstance, samplingConvergenceFactor, minNumOfSamples, maxNumOfSamples, discardOutliers)
		
		if isinstance(exitcode, basestring):
			applies = False
		else:
			if meanRes[0] < time:
				meanRes[0] = meanRes[0]*(1.0+allowFactorToApprox)
			elif meanRes[0] > time:
				meanRes[0] = meanRes[0]*(1.0-allowFactorToApprox)
			applies = abs(time-meanRes[0])/float(time) <= gapToOptimal
		return applies

	def getSuggestedVariableValues(self, runstatement, timeLowerLimit, timeUpperLimit, memoryLimit, numOfPoints, minVarValues, maxVarValues, createInstance, gapToOptimal = 0.1):
		"""
		Returns a list [val_1, val_2, ..., val_N] of suggested variable values for the use in simulation. 
		Each value val_i is a list of values to be used for the i-th variable.
		A series of executions is carried out to determine these suggested values based on the following parameters.
		Args:
		    runstatement: the executable to run.
		    timeLowerLimit: minimcreateInstanceum time (in ms) to spend on each execution.
		    timeUpperLimit: maximum time (in ms) to spend on each execution.
		    memoryLimit: maximum memory (in MB) to spend on each execution.
		    numOfPoints: list [nv_1,...,nv_N], where nv_i is the number of distinct values to use for the i-th variable.
		    minVarValues: list [minv_1,...,minv_N], where minv_i is the minimum value to use for the i-th variable.
		    maxVarValues: list [maxv_1,...,maxv_N], where maxv_i is the maximum value to use for the i-th variable.
		    createInstance: Python method name to callback in order to request the creation of an input to the algorithm.
		      (More details in runSimulation() method's documentation.)
		    gapToOptimal: EMA will performe a binary search to determine the variable values for which the <timeLimit> 
		      is achieved. In practice, it is not usually required to achieve <timeLimit>, but instead to find variable values
		      for which the running time is close to <timeLimit>. EMA will find maximum variable values for which 
		      t, the running time, is such that (<timeLimit> - t)/<timeLimit> <= <gapToOptimal>.
		"""

		printPhaseHeader("EMA version {0}".format(getVersion()))

		printPhaseHeader("Finding a suitable set of values for the variables...")

		self.RUN_STATEMENT = runstatement

		suggestedFile = self.outputfolder + self.LOG_FILE + ".suggestedValues"

		if os.path.isfile(suggestedFile):
			print " * Checking whether the previously saved set of values for the variables still applies..."
			applies = True
			suggestion = []
			lines = readFile(suggestedFile).split("\n")
			for line in lines:
				if line != "":
					lineL = []
					suggestion.append(lineL)
					for val in line.split("\t"):
						lineL.append(int(val))
			curValues = [ L[0] for L in suggestion ]
			applies = self.__checkIfApproximateTime(timeLowerLimit, curValues, memoryLimit, maxVarValues, createInstance, 0.1, gapToOptimal)
			if applies:
				curValues = [ L[len(L)-1] for L in suggestion ]
				applies = self.__checkIfApproximateTime(timeUpperLimit, curValues, memoryLimit, maxVarValues, createInstance, 0.1, gapToOptimal)
		else:
			applies = False			
						
		if applies:
			print " * No new suggested values are required this time."
		else:
			print " * New suggested values are required..."
			
			samplingConvergenceFactor, minNumOfSamples, maxNumOfSamples, discardOutliers = ("Time",0), 1, 1, []

			closeValues1 = self.__getCloseVariableValuesForTimeLimit(minVarValues, maxVarValues, timeLowerLimit, memoryLimit, createInstance, samplingConvergenceFactor, minNumOfSamples, maxNumOfSamples, discardOutliers, gapToOptimal)
			closeValues2 = self.__getCloseVariableValuesForTimeLimit(minVarValues, maxVarValues, timeUpperLimit, memoryLimit, createInstance, samplingConvergenceFactor, minNumOfSamples, maxNumOfSamples, discardOutliers, gapToOptimal)
		
			suggestion = []
			for i in range(len(self.vars)):
				#stepIncrement = (closeValues2[i]/float(closeValues1[i]))**(1.0/(numOfPoints[i]-1))
				r = (closeValues2[i]-closeValues1[i])/float(numOfPoints[i]-1)
				L1 = [ int(closeValues1[i] + j * r) for j in range(numOfPoints[i]) ]
				L = []
				for e in L1:
					if len(L) == 0 or L[len(L)-1] != e:
						L.append(e)
				suggestion.append(L)

			f = open(suggestedFile, "w")
			for varValues in suggestion:
				line = ""
				for val in varValues:
					line = line + str(val) + "\t"
				f.write(line[:len(line)-1] + "\n")
			f.close()		

		printPhaseHeader("Done!")

		return suggestion

	def getFunctionString(self, resource, function, removeAdditiveConstant=False):
		resourceFactor = self.__getResourceFactor(resource)
		fnStr = function[0]
		i = 0
		for var in function[1].split(","):
			varval = function[3][i]
			if var[0] == "a" or var[0] == "c":
				varval = varval * resourceFactor
			fnStr = fnStr.replace(var, str(varval))
			i = i+1
		fnStr = fnStr.replace("x", self.vars[-1])
		if removeAdditiveConstant:
			fnStr = fnStr[:fnStr.find("+")]
		return fnStr

	def runSimulation(self, runstatement, variableValues, createInstance, samplingConvergenceFactor=("Time",0.02), minNumOfSamples=5, maxNumOfSamples=float("inf"), appending=True, discardOutliers=["Time","Space"], traceUsageOfMemoryType="allocated"):
		"""
		Runs a series of instances of input, storing the usage of resources for each instance.
		Args:
		    runstatement: the executable to run.
		    variableValues: a list [S_1,...,S_N], where S_i is a list of values (as defined in the simulation phase);
		    createInstance: Python method name to callback in order to request the creation of an input to the algorithm.
		      The method interface should be:
		        def <createInstance>(variableNames, variableValues, standardInput, parameters, usageFilename), where
		            variableNames = list [var_1, var_2, ..., var_N] of variable names;
		            variableValues = list [val_1, val_2, ..., val_N] of the corresponding variablle values, i.e, var_i = val_i for 1 <= i <= N;
		            standardInput = a file object. All content written to this file will be redirected to the algorithm as standard input;
		            parameters = a list [par_1, par_2, ..., par_p] of parameters to be used for starting <runstatement>;
		      	    usageFilename = a file name into which the usage of cutomized resources (if any) is to be written. In this file,
		      	      the usage of each resource should be reported in a single line following the same order of customized resources
		      	      provided in <customResources>.
		      This method must create an instance of input for the running of <runstatement>. The execution will be 

		          <runstatement> par_1 par_2 ... par_p < <standardInput filename>

		    samplingConvergenceFactor: (<resource>, <convergence factor>) several samples are to be sequentially executed and the mean of 
			the <resource> usage is updated after every new execution. This sampling process goes on while
			(i) the number of samples is less than <minNumOfSamples>; or 
		    	(ii) an execution produces a variation of the <resource> usage sample mean which is greater than <samplingConvergenceFactor> and
		    	     the number of samples is less than or equal to <maxNumOfSamples>
		    minNumOfSamples: minimum number of samples for each variable valuation.
		    maxNumOfSamples: maximum number of samples for each variable valuation.
		    discardOutliers: a list of resources for which outliers should be discarded for computing the stats. 
                        A value is considered an outlier if it is out of the interval [median-1.5*IQR;median+1.5*IQR], 
		        where IQR stands for interquatile range.
		    appending: Boolean value indicating whether the usage of resources are to be appended to the file (appending=False will reset 
		    	the usage of resource -- previous values are backed up for convenience).
		    traceUsageOfMemoryType: type of memory to trace the usage ("allocated" (requested memory), "loaded" (resident memory))
		"""

		printPhaseHeader("EMA version {0}".format(getVersion()))

		printPhaseHeader("Collecting the usage of resources...")

		self.RUN_STATEMENT = runstatement
		appending = appending and os.path.isfile(self.outputfolder + self.LOG_FILE)
		
		if os.path.isfile(self.outputfolder + self.LOG_FILE) and not appending:
			print "Cleaning up previous collected data first..."
			backup(self.outputfolder + self.LOG_FILE)
			
		if not os.path.isfile(self.outputfolder + self.LOG_FILE):
			self.__logHeaders()
			
		t0G = datetime.now()

		self.__runSimulationBackTrack(variableValues, 1, [], createInstance, samplingConvergenceFactor, minNumOfSamples, maxNumOfSamples, discardOutliers, traceUsageOfMemoryType)

		dtG = datetime.now() - t0G
		dtG = (dtG.days*24*60*60 + dtG.seconds)
		print ">>> lasted ", dtG, " seconds"
		printPhaseHeader("Done!")
