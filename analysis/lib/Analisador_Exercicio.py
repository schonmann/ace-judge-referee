# -*- coding: utf-8 -*-

import sys, os, django, subprocess
import others.GetComplexidades
import math
import string
path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if path not in sys.path:
	sys.path.append("/home/ubuntu/workspace") #here store is root folder(means parent).
os.environ['DJANGO_SETTINGS_MODULE'] = 'ACE.settings'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ACE.settings")
django.setup()

from main.models import Exercicios, ExerciciosEnviados, ExecutionStatus, ExerciciosTurma

def VerificaComplexidade(mn, k):
	ok = ''
	if mn == "n^2" or mn == "N^2" or mn == "n**2" or mn == "N**2":
		bg = others.GetComplexidades.compN2()
		if k == bg:
			ok = "n^2"
	elif mn == "n^3" or mn == "N^3" or mn == "n**3" or mn == "N**3":
		bg = others.GetComplexidades.compN3()
		if k == bg:
			ok = "n^3"
	elif mn == "n^4" or mn == "N^4" or mn == "n**4" or mn == "N**4":
		bg = others.GetComplexidades.compN4()
		if k == bg:
			ok = "n^4"
	elif mn == "n" or mn == "N" or mn == "n^1" or mn == "N**1" or mn == "n**1" or mn == "N^1":
		bg = others.GetComplexidades.compN()
		if k == bg:
			ok = "n"
	elif mn == "nlogn" or mn == "nlog(n)" or mn == "n*log(n)" or mn == "NlogN":
		bg = others.GetComplexidades.compNlogN()
		if k == bg:
			ok = "nlogn"
	return ok

def GetDatabaseFolder(arquivo_enviado):
	for i in range(len(arquivo_enviado)-1, 0, -1):
		if arquivo_enviado[i] == '/':
			return arquivo_enviado[:i]
			
def CriaRunAnalysis_Correcao(comp_correta):
	print "CRIANDO O RUNANALYSIS"
	with open("others/RunAnalysisTemplate.py") as f:
		with open("others/RunAnalysisWeb.py", "w+") as f1:
			for line in f:
				if "##complexidade_flag" in line:
					print "INSIDE!"
					comp_correta2 = comp_correta.split(', ')
					for comp in comp_correta2:
						if '*' in comp: 
							partss = comp.split('*')
						else:
							partss = comp
						parts = []
						parts.append(partss)
						print parts
						for j in parts:
							print j[0]
							print j
							if j[0].isdigit():
								if len(j) == 9 and j[2].isdigit():
									s = '\tterms.append(EMA.ExpTerm("x", ' + str(j[:3]) + ',' + str(j[7]) + "))"
									f1.write(s + "\n")
									f1.write('\tm = EMA.Monomial("a", terms, "a"); m.discretize = False\n')
									f1.write("\tfunctions.append(m)\n")
									f1.write("\tterms = []\n")
								elif len(j) == 9:
									s = 'terms.append(EMA.ExpTerm("x", ' + str(j[0]) + ',' + str(j[-4:-1]) + "))"
									f1.write(s + "\n")
									f1.write('m = EMA.Monomial("a", terms, "a"); m.discretize = False\n')
									f1.write("functions.append(m)\n")
									f1.write("terms = []\n")
								elif len(j) == 7:
									s = '\tterms.append(EMA.ExpTerm("x", ' + str(j[0]) + ',' + str(j[5]) + "))"
									f1.write(s + "\n")
									f1.write('\tm = EMA.Monomial("a", terms, "a"); m.discretize = False\n')
									f1.write("\tfunctions.append(m)\n")
									f1.write("\tterms = []\n")
								else:
									s = '\tterms.append(EMA.ExpTerm("x", ' + str(j[:3]) + ',' + str(j[-4:-1]) + "))"
									f1.write(s + "\n")
									f1.write('\tm = EMA.Monomial("a", terms, "a"); m.discretize = False\n')
									f1.write("\tfunctions.append(m)\n")
									f1.write("\tterms = []\n")
							elif j[0] == 'n':
								if len(j) == 5:
									s = '\tterms.append(EMA.PolyTerm("x", ' + str(j[-3:]) + "))"
									f1.write(s + "\n")
									f1.write('\tm = EMA.Monomial("a", terms, "a"); m.discretize = False\n')
									f1.write("\tfunctions.append(m)\n")
									f1.write("\tterms = []\n")
								elif len(j) == 3:
									s = '\tterms.append(EMA.PolyTerm("x", ' + str(j[2]) + "))"
									f1.write(s + "\n")
									f1.write('\tm = EMA.Monomial("a", terms, "a"); m.discretize = False\n')
									f1.write("\tfunctions.append(m)\n")
									f1.write("\tterms = []\n")
							else:
								if len(j) == 8:
									s = '\tterms.append(EMA.LogTerm("x", 2, ' + str(j[7]) + "))"
									f1.write(s + "\n")
									f1.write('\tm = EMA.Monomial("a", terms, "a"); m.discretize = False\n')
									f1.write("\tfunctions.append(m)\n")
									f1.write("\tterms = []\n")
								elif len(j) == 10:
									s = '\tterms.append(EMA.LogTerm("x", 2, ' + str(j[-3:]) + "))"
									f1.write(s + "\n")
									f1.write('\tm = EMA.Monomial("a", terms, "a"); m.discretize = False\n')
									f1.write("\tfunctions.append(m)\n")
									f1.write("\tterms = []\n")
				else:
					f1.write(line)

def CriaRunSimulation_Complexidade(arquivo_enviado, import_gerador, numPoints, timeUpLimit, createInstance="GeraEntrada", dbFolder="/db/exercicio", minValues=None, maxValues=None, timeLowLimit=None, maxNumSamples=None):
	new_name = ''
	with open("others/RunSimulationTemplate.py") as f:
    		with open("others/RunSimulationWeb.py", "w+") as f1:
        		for line in f:
					if line == "##cmd_flag\r\n":
						cmd = ""
						if (str(arquivo_enviado)[-3:] == '.py'):
							for k in str(arquivo_enviado):
								if k==' ':
									new_name += '\ '
								else:
									new_name += str(k)
							cmd = "python" + ' ' + str(new_name)
						elif (str(arquivo_enviado)[-4:] == '.cpp'):
							aux = subprocess.Popen(["g++", str(arquivo_enviado), '-o', 'enviado'])
							aux.wait()
							cmd = "./enviado"
						new_cmd_line = "cmd = \"" + cmd + "\"\r\n"
						f1.write(new_cmd_line)
					elif line == "##il_flag\r\n":
						new_cmd_line = "ilflag = " + '"' + str(import_gerador)[:34] + '"' + "\r\n"
						f1.write(new_cmd_line)
					elif line == "##import_flag\r\n":
						new_cmd_line = "import " + str(import_gerador)[34:-3] + " as library" + "\r\n"
						f1.write(new_cmd_line)
					elif line == "\t##gerador_flag\r\n":
						new_cmd_line = "\tlibrary." + "GeraEntrada(N, standardInput)" + "\r\n"
						f1.write(new_cmd_line)
					elif line == "##createInstance_flag\r\n":
						# INFORMAR FUNÇÃO PARA CRIAÇÃO DE ENTRADAS.
						#new_cmd_line = "library.GeraEntrada(N, standardInput)\r\n"
						#f1.write(new_cmd_line)
						pass
					elif line == "##databaseFolder_flag\r\n":
						#new_cmd_line = GetDatabaseFolder(arquivo_enviado) + "output"
						#new_cmd_line = GetDatabaseFolder("/main/assets/folder/here/sun.py") + "output"
						#new_cmd_line = dbFolder + "\r\n"
						#f1.write(new_cmd_line)
						pass
					elif line == "##minVarValues_flag\r\n":
						if minValues == None:
							f1.write("minVarValues = [1]" + "\r\n")
						else:
							f1.write("minVarValues = " + str(minValues) + "\r\n")
					elif line == "##maxVarValues_flag\r\n":
						if maxValues == None:
							f1.write("maxVarValues = [1e9]" + "\r\n")
						else:
							f1.write("maxVarValues = " + str(maxValues) + "\r\n")
					elif line == "##numOfPoints_flag\r\n":
						if numPoints == None:
							f1.write("numOfPoints = [10]" + "\r\n")
						else:
							f1.write("numOfPoints = [" + str(numPoints) + "]\r\n")
					elif line == "##timeLowerLimit_flag\r\n":
						if timeLowLimit == None:
							f1.write("timeLowerLimit = 500" + "\r\n")
						else:
							f1.write("timeLowerLimit = " + str(timeLowLimit) + "\r\n")
					elif line == "##timeUpperLimit_flag\r\n":
						if timeUpLimit == None:
							f1.write("timeUpperLimit = 10000" + "\r\n")
						else:
							f1.write("timeUpperLimit = " + str(timeUpLimit) + "\r\n")
					elif line == "##maxNumSamples_flag\r\n":
						if maxNumSamples == None:
							f1.write("maxNumOfSamples = 30" + "\r\n")
						else:
							f1.write("maxNumOfSamples = " + str(maxNumSamples) + "\r\n")
					else: 
						f1.write(line)

def extrairComplexidade(path):
	fp = open(fpath, 'w+')
	fp.write(subprocess.check_output(["python","RunAnalysis.py"]))
	fp.close()
	fp = open(fpath, 'r')
	for line in fp:
		print line

def ExtrairSaidaGerador(nome_prog):
	if(str(nome_prog)[-3:] == '.py'):
		for jojo in range(8000):
			verificador = subprocess.check_output(["python",str(str(nome_prog))])
			
	#RECOLOCAR COMPATIBILIDADE COM C++
	#elif (str(nome_prog)[-4:] == '.cpp'):
	#	aux = subprocess.Popen(["g++", str(nome_prog), '-o', 'gerador'])
	#	aux.wait()
	#	verificador = subprocess.check_output(["./gerador"])
	return verificador
		
def ExtrairSaidaPrograma(nome_prog, verificador):
	if (str(nome_prog)[-3:] == '.py'):
		ps1 = subprocess.Popen(["python", str(nome_prog)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdout = ps1.communicate(verificador)
	elif (str(nome_prog)[-4:] == '.cpp'):
		ps1 = subprocess.Popen(["g++", str(nome_prog), '-o', 'resposta'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		ps1.wait()
		ps4 = subprocess.Popen(["./resposta"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdout = ps4.communicate(verificador)
	else:
		return 'LN'
	return stdout

def CorrigeExercicioCriacao(gerador, arquivo_resposta):
	verificador = ExtrairSaidaGerador(gerador)
	resposta = ExtrairSaidaPrograma(arquivo_resposta, verificador)
	if enviado == 'LN':
		return 'LN'				#Linguagem nao reconhecida
	if (enviado[1]!=''):
		return 'ER'				#Erro de execucao
	if (resposta[0]==enviado[0]):
		return 'ES'				#Resposta Correta
	else:
		return "EE" 			#Resposta Errada
		
def CorrigeExercicio(gerador, arquivo_resposta, arquivo_enviado):
	verificador = ExtrairSaidaGerador(gerador)
	resposta = ExtrairSaidaPrograma(arquivo_resposta, verificador)
	enviado = ExtrairSaidaPrograma(arquivo_enviado, verificador)
	if enviado == 'LN':
		return 'LN'				#Linguagem nao reconhecida
	if (enviado[1]!=''):
		return 'ER'				#Erro de execucao
	if (resposta[0]==enviado[0]):
		return 'ES'				#Resposta Correta
	else:
		return "EE" 			#Resposta Errada

def CriaStringCompEMA(mn):
	new_mn = "a0*" + str(mn) + "+c1"
	new_mn = string.replace(new_mn, "lg(n)", "(log(x)/log(2))")
	new_mn = string.replace(new_mn, "lgn", "(log(x)/log(2))")
	new_mn = string.replace(new_mn, 'n', "x")
	new_mn = string.replace(new_mn, '^', "**")
	#mn.replace("", "**")
	return new_mn

def CorrigeComplexidade(arquivo_enviado):
	if (str(arquivo_enviado)[-3:] == '.py'):
		cmd = "python" + str(arquivo_enviado)
		CriaRunSimulation_Complexidade(cmd)
	elif (str(arquivo_enviado)[-4:] == '.cpp'):
		cmd = "./enviado"
		CriaRunSimulation_Complexidade(cmd)
	else:
		return "Linguagem nao reconhecida"
	extrairComplexidade()
	# TERMINAR EXTRACAO DE COMPLEXIDADE
	
def ExecutaRunSimulationAssincCriacao(obj):
	status = ExecutionStatus.objects.last()
	status.em_analise_assinc = 1
	status.save()
	print "INDO PARA SIMULAÇÃO"
	obj.status_criacao = 'SI'
	obj.save()
	mmm = 0
	ps1 = subprocess.check_output(["python", "others/RunSimulationWeb.py"])
	print ps1
	g = open("Sigma.txt", "w+")
	g.write(ps1)
	print "INDO PARA ANALISE"
	obj.status_criacao = 'AN'
	obj.save()
	full_file = ""
	try:
		full_file = subprocess.check_output(["python", "others/RunAnalysisWebCria.py"])
	except:
		pass
	print full_file
	obj.analise_EMA = full_file
	print "FIM ANALISE"
	met = full_file.split('\n')
	for i in range(len(met)-1):
		if ("BEST-GUESS" in met[i] and mmm == 0):
			print met[i+1]
			mmm = 1
			g = met[i+1].split(', ')[2]
			k = met[i+1].split(' (')[1]
			k = k.split(', ')[0]
			k = k[1:]
			k = k[:-1]
			print k
			print g
			ok = ''
			new_mn = ''
			ds = obj.complexidade_correta.split(', ')
			print ds
			for mn in ds:
				'''if mn == "n^2" or mn == "N^2" or mn == "n**2" or mn == "N**2":
					bg = others.GetComplexidades.compN2()
					if k == bg:
						ok = "n^2"
				if mn == "n^3" or mn == "N^3" or mn == "n**3" or mn == "N**3":
					bg = others.GetComplexidades.compN3()
					if k == bg:
						ok = "n^3"
				if mn == "n^4" or mn == "N^4" or mn == "n**4" or mn == "N**4":
					bg = others.GetComplexidades.compN4()
					if k == bg:
						ok = "n^4"
				if mn == "n" or mn == "N" or mn == "n^1" or mn == "N**1" or mn == "n**1" or mn == "N^1":
					bg = others.GetComplexidades.compN()
					if k == bg:
						ok = "n"
				if mn == "nlogn" or mn == "nlog(n)" or mn == "n*log(n)" or mn == "NlogN":
					bg = others.GetComplexidades.compNlogN()
					if k == bg:
						ok = "nlogn"'''
				new_mn = CriaStringCompEMA(mn)
				print "NEW_MN = " + str(new_mn)
				if k == new_mn:
					ok = mn
			if ok != '':
				print "ENTREI OK"
				obj.status_criacao = 'CC'
				obj.threshold = math.sqrt(float(g))/int(obj.num_pontos)
				print "NUM PONTOS: " + str(obj.num_pontos)
				print "THRESHOLD: " + str(obj.threshold)
				print "TOLERANCIA: " + str(obj.tolerancia)
				obj.complexidade_calculada = ok
				obj.testador = 1
				obj.save()
			else:
				obj.status_criacao = 'CE'
				obj.save()
	status.em_analise_assinc = 0
	status.status_analise = 0
	status.save()
	
def ExecutaRunSimulationAssinc(obj):
	status = ExecutionStatus.objects.last()
	correto = ExerciciosTurma.objects.filter(nome_turma=obj.turma, idd=obj.ex_id_f, extra_id=obj.extra_id)
	for i in correto:
		print "EXTRA ID: " + str(i.extra_id)
		comp_corr = i.complexidade_calculada
		num_pontos = i.num_pontos
		threshold = i.threshold
		tolerancia = (float(i.tolerancia)/100) + 1
		print comp_corr
		status.em_analise_assinc = 1
		status.save()
		print "INDO PARA SIMULAÇÃO"
		obj.status = 'SI'
		obj.save()
		mmm = 0
		ps1 = subprocess.check_output(["python", "others/RunSimulationWeb.py"])
		print ps1
		g = open("Sigma.txt", "w+")
		g.write(ps1)
		print "INDO PARA ANALISE"
		obj.status_criacao = 'AN'
		obj.save()
		full_file = subprocess.check_output(["python", "others/RunAnalysisWeb.py"])
		print full_file
		obj.analise_EMA = full_file
		print "FIM ANALISE"
		met = full_file.split('\n')
		for i in range(len(met)-1):
			if (("%" in met[i] and "function" not in met[i]) or ("BEST-GUESS" in met[i-1])):
				print met[i]
				g = met[i].split(', ')[2]
				k = met[i].split(' (')[1]
				k = k.split(', ')[0]
				k = k[1:]
				k = k[:-1]
				print k
				print g
				new_comp_corr = CriaStringCompEMA(comp_corr)
				print "NEW_COMP_CORR = " + str(new_comp_corr)
				#ok = VerificaComplexidade(comp_corr, k)
				ENB = math.sqrt(float(g))/int(num_pontos)
				print "ENB ENVIADO: " + str(ENB)
				print "NUM PONTOS: " + str(num_pontos)
				print "TOLERANCIA: " + str(tolerancia)
				print "THRESHOLD: " + str(threshold)
				if ENB <= (threshold*tolerancia):
					print "ENTREI OK"
					obj.status = 'CC'
					break
				else:
					print "ENTREI ERRADO"
					obj.status = 'CE'
	print obj.status
	print obj.extra_id
	obj.save()