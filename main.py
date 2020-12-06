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
            type='direct', routing_key='submit')),
        Queue(
            os.environ.get('ANALYSIS_QUEUE', 'analysis-queue'),
            exchange=Exchange(os.environ.get('ANALYSIS_QUEUE','analysis-exchange'),
            type='direct', routing_key='submit'))]
            
@app.task(serializer='json')
def analyze(id, problem_id, solution, language, input_generator, asymptotic_function, asymptotic_notation):
    
    print("""
    SUBMISSION: {0}\n
    PROBLEM ID: {1}\n
    LANGUAGE: {2}\n
    INPUT GENERATOR: {3}\n
    ASYMPTOTIC FUNCTION: {4}\n
    ASYMPTOTIC NOTATION: {5}\n
    """.format(id, problem_id, solution, language, input_generator, asymptotic_function, asymptotic_notation))

    try:
        solution_exe_path = compiler.compile(solution, language)
        simulation_result = analyzer.verdict(id, answer_key_exe_path, input_generator_exe_path, asymptotic_function, asymptotic_notation)
        
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
def simulate(problem_id, judge_answer_key_program, judge_answer_key_program_language, input_generator, input_generator_language, asymptotic_function, asymptotic_notation):

    print("""
    SUBMISSION:{0}
    JUDGE ANSWER KEY PROGRAM: {1}
    JUDGE ANSWER KEY PROGRAM LANGUAGE: {2}
    INPUT GENERATOR: {3}
    INPUT GENERATOR LANGUAGE: {4}
    ASYMPTOTIC FUNCTION: {5}
    ASYMPTOTIC NOTATION: {6}
    """.format(problem_id, judge_answer_key_program, judge_answer_key_program_language, input_generator, input_generator_language, asymptotic_function, asymptotic_notation))

    try:
        answer_key_exe_path = compiler.compile(judge_answer_key_program, judge_answer_key_program_language)
        input_generator_exe_path  = compiler.compile(input_generator, input_generator_language)
        simulation_result = analyzer.verdict(problem_id, answer_key_exe_path, input_generator_exe_path, asymptotic_function, asymptotic_notation)

        return {
            'problemId': problem_id,
            'simulationVerdict': simulation_result,
        }
    except exceptions.CompileError:
        return {
            'problemId': problem_id,
            'simulationVerdict': {
                'verdict': 'COMPILE_ERROR'
            }
        }
    except exceptions.UnsupportedLangError:
        return {
            'problemId': problem_id,
            'simulationVerdict': {
                'verdict': 'COMPILE_ERROR'
            }
        }

@app.task(serializer='json')
def verdict(id, solution, language, judge_input, judge_output):

    print("""SUBMISSION: {0}
    SOLUTION: {1}
    LANGUAGE: {2}
    JUDGE INPUT: {3}
    JUDGE OUTPUT: {4}
    """.format(id, solution, language, judge_input, judge_output))

    try:
        path = compiler.compile(solution, language)
        
        print('Path: %s' % path)

        print('Starting judging "%s"...' % id)
        judge_result = judge.verdict(executable_path=path, input=judge_input, expected_output=judge_output)
        print('Judge complete! %s' % judge_result)

        return {
            'submissionId': id,
            'judgeVerdict': judge_result,
        }

    except exceptions.CompileError:
        return {
            'submissionId': id,
            'judgeVerdict': judge.verdict(compile_error=True),
        }
    except exceptions.UnsupportedLangError:
        return {
            'submissionId': id,
            'judgeVerdict': judge.verdict(compile_error=True),
        }