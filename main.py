from __future__ import absolute_import
from kombu import Exchange, Queue
from celery import Celery
from compiler import compiler
from judgement import judge
from analysis import analyzer
from compiler import exceptions
from utils.command import run_command_timeout
import traceback
import sys
import celeryconfig
import json

import os

app = Celery('main', 
    broker=os.environ.get('BROKER_URL','amqp://guest@localhost//'),
    backend=os.environ.get('BACKEND_URL', 'rpc://'),
    enable_utc=True)

app.conf.task_queues= [
        Queue(
            os.environ.get('SUBMISSION_QUEUE', 'submission-queue'), 
            exchange=Exchange(os.environ.get('SUBMISSION_EXCHANGE','submission-exchange'), 
            type='direct', routing_key='submit')),
        Queue(
            os.environ.get('SIMULATION_QUEUE', 'simulation-queue'), 
            exchange=Exchange(os.environ.get('SIMULATION_EXCHANGE','simulation-exchange'), 
            type='direct', routing_key='submit')),
        Queue(
            os.environ.get('ANALYSIS_QUEUE', 'analysis-queue'),
            exchange=Exchange(os.environ.get('ANALYSIS_QUEUE','analysis-exchange'),
            type='direct', routing_key='submit'))]
            
@app.task(serializer='json')
def analyze(submission_id, problem_id, solution, solution_language, input_generator, input_generator_language, asymptotic_expression, asymptotic_notation):
    
    try:
        solution_exe_path = compiler.compile(solution, solution_language)
        input_generator_exe_path  = compiler.compile(input_generator, input_generator_language)
        analyzer_results = analyzer.verdict(problem_id, solution_exe_path, input_generator_exe_path, asymptotic_expression, asymptotic_notation, submission_id)

        return {
            'submissionId': submission_id,
            'problemId': problem_id,
            'analysisVerdict': analyzer_results,
        }
    except (exceptions.CompileError, exceptions.UnsupportedLangError) as e:
        return {
            'submissionId': submission_id,
            'problemId': problem_id,
            'analysisVerdict': {
                'verdict': 'COMPILE_ERROR'
            }
        }
    except Exception as e:
        print e
        return {
            'submissionId': submission_id,
            'problemId': problem_id,
            'analysisVerdict': {
                'verdict': 'GENERIC_ERROR'
            }
        }

@app.task(serializer='json')
def simulate(problem_id, judge_answer_key_program, judge_answer_key_program_language, input_generator, input_generator_language, asymptotic_expression, asymptotic_notation, judge_input):
    try:
        answer_key_exe_path = compiler.compile(judge_answer_key_program, judge_answer_key_program_language)
        input_generator_exe_path  = compiler.compile(input_generator, input_generator_language)
        simulation_result = analyzer.verdict(problem_id, answer_key_exe_path, input_generator_exe_path, asymptotic_expression, asymptotic_notation)

        generated_output, stderr = run_command_timeout(answer_key_exe_path, judge_input)

        return {
            'problemId': problem_id,
            'simulationVerdict': simulation_result,
            'generatedOutput': generated_output,
        }
    except (exceptions.UnsupportedLangError, exceptions.CompileError):
        return {
            'problemId': problem_id,
            'simulationVerdict': {
                'verdict': 'COMPILE_ERROR'
            },
            'generatedOutput': None,
        }
    except Exception as e:
        traceback.print_exc()
        return {
            'problemId': problem_id,
            'simulationVerdict': {
                'verdict': 'GENERIC_ERROR'
            },
            'generatedOutput': None,
        }

@app.task(serializer='json')
def verdict(submission_id, solution, language, judge_input, judge_output):

    try:
        path = compiler.compile(solution, language)
        
        print('Path: %s' % path)
        print('Starting judging "%s"...' % submission_id)

        judge_result = judge.verdict(executable_path=path, input=judge_input, expected_output=judge_output)

        print('Judge complete! %s' % judge_result)

        return {
            'submissionId': submission_id,
            'judgeVerdict': judge_result,
        }

    except (exceptions.CompileError, exceptions.UnsupportedLangError):
        return {
            'submissionId': submission_id,
            'judgeVerdict': {
                'verdict': 'COMPILE_ERROR'
            },
        }
    except Exception as e:
        print e
        return {
            'submissionId': submission_id,
            'judgeVerdict': {
                'verdict': 'GENERIC_ERROR'
            },
        }