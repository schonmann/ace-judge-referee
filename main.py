from __future__ import absolute_import
from kombu import Exchange, Queue
from celery import Celery
from compiler import compiler
from judgement import judge
from analysis import analyzer
from compiler import exceptions
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
            type='direct', routing_key='submit'))]


@app.task(serializer='json')
def simulate(id, judge_input, judge_output, judge_answer_key_program, judge_answer_key_program_language, input_generator, input_generator_language, complexities, bigoNotation):

    print("SUBMISSION:")
    print(id)
    print("JUDGE INPUT:")
    print(judge_input)
    print("JUDGE OUTPUT:")
    print(judge_output)
    print("JUDGE ANSWER KEY PROGRAM:")
    print(judge_answer_key_program)
    print("JUDGE ANSWER KEY PROGRAM LANGUAGE:")
    print(judge_answer_key_program_language)
    print("INPUT GENERATOR:")
    print(input_generator)
    print("INPUT GENERATOR LANGUAGE:")
    print(input_generator_language)
    print("COMPLEXITIES:")
    print(complexities)
    print("BIGONOTATION:")
    print(bigoNotation)

    try:
        answer_key_exe_path = compiler.compile(judge_answer_key_program, judge_answer_key_program_language)
        input_generator_exe_path  = compiler.compile(input_generator, input_generator_language)
        
        print('Answer key program path: %s' % answer_key_exe_path)
        print('Input generator path: %s' % input_generator_exe_path)
        
        print('Starting simulation "%s"...' % id)
        simulation_result = analyzer.verdict(id, answer_key_exe_path, input_generator_exe_path, complexities, bigoNotation)
        print('Analysis complete! %s' % simulation_result)

        return {
            'problemId': id,
            'simulationVerdict': simulation_result,
        }
    except exceptions.CompileError:
        return {
            'problemId': id,
            'simulationVerdict': {
                'verdict': 'COMPILE_ERROR'
            }
        }
    except exceptions.UnsupportedLangError:
        return {
            'problemId': id,
            'simulationVerdict': {
                'verdict': 'COMPILE_ERROR'
            }
        }

@app.task(serializer='json')
def verdict(id, solution, language, judge_input, judge_output, input_generator, complexities, bigoNotation):

    print("SUBMISSION:")
    print(id)
    print("SOLUTION:")
    print(solution)
    print("LANGUAGE:")
    print(language)
    print("JUDGE INPUT:")
    print(judge_input)
    print("JUDGE OUTPUT:")
    print(judge_output)
    print("INPUT GENERATOR:")
    print(input_generator)
    print("COMPLEXITIES:")
    print(complexities)
    print("BIGONOTATION:")
    print(bigoNotation)

    try:
        path = compiler.compile(solution, language)
        
        print('Path: %s' % path)

        print('Starting judging "%s"...' % id)
        judge_result = judge.verdict(executable_path=path, input=judge_input, expected_output=judge_output)
        print('Judge complete! %s' % judge_result)

        # print('Starting analyzing "%s"...' % id)
        # analysis_result = analyzer.verdict(executable_path=path, complexities=complexities, input_generator=input_generator)
        # print('Analysis complete! %s' % analysis_result)
        analysis_result = 'CORRECT_COMPLEXITY'

        return {
            'submissionId': id,
            'judgeVerdict': judge_result,
            'analyzerVerdict': {
                'verdict': analysis_result
            }
        }

    except exceptions.CompileError:
        return {
            'submissionId': id,
            'judgeVerdict': judge.verdict(compile_error=True),
            'analyzerVerdict': None
        }
    except exceptions.UnsupportedLangError:
        return {
            'submissionId': id,
            'judgeVerdict': judge.verdict(compile_error=True),
            'analyzerVerdict': None
        }