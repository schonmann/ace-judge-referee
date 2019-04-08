import sys, os, django, subprocess
import others.Analisador_Exercicio
from multiprocessing import Pool
path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if path not in sys.path:
	sys.path.append("/home/ubuntu/workspace") #here store is root folder(means parent).
os.environ['DJANGO_SETTINGS_MODULE'] = 'ACE.settings'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ACE.settings")
django.setup()

from main.models import ExecutionStatus, ExerciciosEnviados, Exercicios, ExerciciosTurma
from main.forms import ExecutionStatusForm
##from uploads.resposta_correta

def VerificaDisponibilidade(complexidade = 0, criacao = 0, obj = None):
	if not ExecutionStatus.objects.all():
		status = ExecutionStatusForm()
		status.status_analise = 0
		status.status_correcao = 0
	 	status.status_correcao_maratona = 0
		status.status_analise_maratona = 0
		status.em_analise_assinc = 0
		status.save()
	
	status = ExecutionStatus.objects.last()
	
	status.status_analise = 0
	
	print "OK1"
	
	#if status.status_analise == 1 or status.status_correcao == 1 or status.status_analise_maratona == 1 or status.status_correcao_maratona == 1:
	#	print status.status_analise
	#	print status.status_correcao
	#	print status.status_analise_maratona
	#	print status.status_correcao_maratona
	
	#else:
	if criacao == 1:
		if complexidade == 1:
			status.status_analise = 1
			status.save()
			if obj:
				gerador_id = Exercicios.objects.filter(ex_id=obj.idd)
				for lll in gerador_id:
					ger_ent = lll.gerador_de_entrada
				#others.Analisador_Exercicio.CorrigeExercicioCriacao(ger_ent, obj.resposta_correta)
				others.Analisador_Exercicio.CriaRunSimulation_Complexidade(obj.resposta_correta, ger_ent, obj.num_pontos, obj.tempo_limite_comp)
				others.Analisador_Exercicio.ExecutaRunSimulationAssincCriacao(obj)
				#resposta_analise = others.Analisador_Exercicio.CorrigeExercicio(gerador_id.last().gerador_de_entrada, obj.resposta_correta)
				#agora.status = resposta_analise
				#agora.save()
				#resposta_complexidade = others.Analisador_Exercicio.CorrigeComplexidade(analise.last().gerador_de_entrada, )
				
		else:
			status.status_correcao = 1
			status.save()
				
			
	else:
		print "OK2"
		status.status_correcao = 1
		status.save()
		#COLOCAR FILTER NO SELECT ABAIXO PARA SELECIONAR APENAS EXERCICIOS AINDA NAO CORRIGIDOS
		#sel = ExerciciosEnviados.objects.order_by('hora_envio').exclude(hora_envio__isnull=True)
		#sel2 = sel.order_by('hora_envio').filter(status='NE')
		#FAZER SELECT PARA DETERMINAR O EXERCICIO QUE DEVE SER EXECUTADO AGORA;
		#agora = sel.last()
		#VERIFICAR SE UMA MARATONA ESTA EM ANDAMENTO, CASO POSITIVO, EXECUTAR APENAS EXERCICIOS DA MESMA;
		#SE NAO HOUVER MARATONA, EXECUTAR EXERCICIOS DE CORRECAO PRIMEIRO, DEPOIS OS DE ANALISE;
		analise = Exercicios.objects.filter(ex_id=obj.ex_id_f)
		ex_turma = ExerciciosTurma.objects.filter(idd = obj.ex_id_f, nome_exercicio = obj.nome_exercicio, extra_id = obj.extra_id, nome_turma = obj.turma)
		print "INDO CRIAR O RUNSIMULATION!"
		for lll in analise:
			ger_ent = lll.gerador_de_entrada
		for lll in ex_turma:
			num_pontos = lll.num_pontos
			tempo_comp = lll.tempo_limite_comp
			comp_correta = lll.complexidade_correta
		print comp_correta
		print "AAAAAAAAAAAAAAASSSSSSSSSSSSSSSSDDDDDDDDDDDDDDD"
		others.Analisador_Exercicio.CriaRunSimulation_Complexidade(obj.arquivo_resposta, ger_ent, num_pontos, tempo_comp)
		others.Analisador_Exercicio.CriaRunAnalysis_Correcao(comp_correta)
		others.Analisador_Exercicio.ExecutaRunSimulationAssinc(obj)
		#if analise.last().analise_comp==1:
		#	if analise.last().gerador_de_entrada != None:
		#resposta_analise = others.Analisador_Exercicio.CorrigeExercicio(analise.last().gerador_de_entrada, analise.last().resposta_correta, agora.arquivo_resposta)
		#agora.status = resposta_analise
		#agora.save()
		#resposta_complexidade = others.Analisador_Exercicio.CorrigeComplexidade(analise.last().gerador_de_entrada, )
		#else:
		#	if analise.last().gerador_de_entrada != None:
		#		resposta_analise = others.Analisador_Exercicio.CorrigeExercicio(analise.last().gerador_de_entrada, analise.last().resposta_correta, agora.arquivo_resposta)
		#		agora.status = resposta_analise
		#		agora.save()
		#VERIFICAR TEMPO MINIMO QUE O EMA DEMORA PARA VERIFICAR A COMPLEXIDADE EXATA.
		status.status_correcao = 0
		status.save()
	print "OK3"