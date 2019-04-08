import sys, os, django, subprocess
sys.path.append("/home/pedro/Documentos/ACE") #here store is root folder(means parent).
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ACE.settings")
django.setup()

from main.models import Exercicios

def createRunSimulationFile(cmd_st):
	with open("RunSimulation.py") as f:
    		with open("RunSimulationWeb.py", "w+") as f1:
        		for line in f:
				#print repr(line)
				if line == "##cmd_flag\r\n":
					new_cmd_line = "cmd = \"" + cmd_st + "\"\r\n"
					f1.write(new_cmd_line)
				else: 
                			f1.write(line)

#def createRunAnalysisFile(cmd_st):


def extractsComplexity(path):
	fp = open(fpath, 'w+')
	fp.write(subprocess.check_output(["python","RunAnalysis.py"]))
	fp.close()
	fp = open(fpath, 'r')
	for line in fp:
		print line

execs = Exercicios.objects.last()
executable = Exercicios.objects.last().resposta_correta
executable_st = 'python /home/pedro/Documentos/ACE/' + str(executable)
fpath = os.path.expanduser('~/Documentos/ACE/results/output/analysis.txt')

if executable_st[-3:] == '.py':
	createRunSimulationFile(executable_st)
	subprocess.call(["python","RunSimulationWeb.py"])
	extractsComplexity(fpath)
	executable = 'SUCCESS'
	execs.nome_exercicio = 'TESTE NOME'
	execs.save()
