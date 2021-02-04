from lib import EMA
from storage.stream import redirect_stdout_to
import storage.storage
import parser
import os
from utils.command import run_command_timeout
from sympy import *
import re

COMPLEXITY_O = "O"
COMPLEXITY_LITTLE_O = "o"
COMPLEXITY_THETA = "THETA"
COMPLEXITY_OMEGA = "OMEGA"
COMPLEXITY_LITTLE_OMEGA = "LITTLE_OMEGA"


# Tests if the target function matches the asymptote
def matches_asymptote(problem_variable, asymptotic_expression, asymptotic_notation, target_function):
    target_expression_s = S(target_function['full_expression'])
    asymptotic_expression_s = S(asymptotic_expression)

    if len(target_expression_s.free_symbols) != 1 or len(target_expression_s.free_symbols) != len(asymptotic_expression_s.free_symbols):
        raise Exception('Expressions are invalid')

    target_expression_symbol = list(target_expression_s.free_symbols)[0]
    asymptotic_expression_symbol = list(asymptotic_expression_s.free_symbols)[0]

    x = symbols(problem_variable)
    fx = target_expression_s.subs(target_expression_symbol, x)
    gx = asymptotic_expression_s.subs(asymptotic_expression_symbol, x)

    print "FX: ", fx
    print "GX: ", gx

    try:
        lim = limit(fx/gx, x, oo, '+-')

        print "LIMIT VALUE: ", lim
        
        if lim == oo:
            return asymptotic_notation in [COMPLEXITY_LITTLE_OMEGA, COMPLEXITY_OMEGA]
        elif lim == 0:
            return asymptotic_notation in [COMPLEXITY_LITTLE_O, COMPLEXITY_O]
        elif ask(Q.real(lim)):
            return asymptotic_notation in [COMPLEXITY_THETA, COMPLEXITY_OMEGA, COMPLEXITY_O]
    except ValueError as v:
        # indeterminate limit
        print v
        return None

def is_same_function(fna, fnb):
    return fna['full_expression'] == fnb['full_expression']

def get_simulation_result(runner, problem_id, input_generator_exe_path=None, answer_key_exe_path=None, resource="Time", submission_id=None, problem_variable=None):
    # Compute EMA's simulation results for the problem
    minNumOfSamples = 1
    maxNumOfSamples = 5
    minVarValues = [1]
    maxVarValues = [1e6]
    numOfPoints = [15]
    timeLowerLimit = 100
    timeUpperLimit = 15000

    # we run the input generator executable passing the value of N to stdin :)
    def createInput(variableNames, variableValues, standardInput, parameters, usageFilename):
        n_value = variableValues[0]
        input = "%s\n" % n_value
        run_command_timeout(input_generator_exe_path, input=input, stdout=standardInput)

    path = storage.storage.get_simulation_problem_submission_file_path(problem_id, submission_id) if submission_id else storage.storage.get_simulation_problem_file_path(problem_id)
    with open(path, 'w+') as file:
        @redirect_stdout_to(file)
        def run_simulation():
            suggestedVarValues = runner.getSuggestedVariableValues(runstatement=answer_key_exe_path, timeLowerLimit=timeLowerLimit, timeUpperLimit=timeUpperLimit, memoryLimit=200, 
                            numOfPoints=numOfPoints, minVarValues=minVarValues, maxVarValues=maxVarValues, 
                            createInstance=createInput)
            runner.runSimulation(runstatement=answer_key_exe_path, variableValues=suggestedVarValues, createInstance=createInput,
                    samplingConvergenceFactor=(resource,0.01), minNumOfSamples=minNumOfSamples, maxNumOfSamples=maxNumOfSamples, 
                    discardOutliers=[res[0] for res in runner.resources], appending=False)
        run_simulation()
        file.seek(0)
        return parser.parse_simulation_result(file.read())

def get_analysis_result(runner, problem_id, resource="Time", submission_id=None, problem_variable=None):
    # Compute EMA's analysis results for the problem
    name = '%s/%s' % (problem_id, submission_id) if submission_id else problem_id
    path = storage.storage.get_simulation_problem_submission_file_path(problem_id, submission_id) if submission_id else storage.storage.get_simulation_problem_file_path(problem_id)
    with open(path, 'w+') as file:
        @redirect_stdout_to(file)
        def run_analysis():
            fn = runner.getResourceUsageFunction(resource, discardTimeUnder=10, case='mean', equivalenceThreshold=0.01,
                            tieBreakMaxVal=0, discreteFunctionsOnly=False, printFunctionReport=True)
            titleStr = runner.getFunctionString(resource,fn[-1][1],True)
            exportToFolder = storage.storage.get_simulation_problem_submission_graphs_path(problem_id, submission_id) if submission_id else storage.storage.get_simulation_problem_graphs_path(problem_id)
            runner.plotResourceUsage(resource, title=titleStr, mode="windows", style=("points"), cases = (0,1,0), 
		        usageFunction=fn, exportToFolder=exportToFolder, exportToFormat="png")

        run_analysis()
        file.seek(0)
        return parser.parse_analysis_result(file.read(), problem_variable)

def get_problem_variable_from_asymptotic_expression(asymptotic_expression):
    idx = re.search(r'[a-z]', asymptotic_expression, re.I).start()
    return asymptotic_expression[idx]

# Computes the analysis verdict for the problem :)
def verdict(problem_id, answer_key_exe_path, input_generator_exe_path, asymptotic_expression, asymptotic_notation, submission_id=None, asymptotic_variable="x"):
    resource = "Time"

    databaseFolder = './emafiles/%s/submissions/%s' % (problem_id, submission_id) if submission_id else './emafiles/%s/' % problem_id
    try:
        os.makedirs(databaseFolder)
    except OSError:
        if not os.path.isdir(databaseFolder):
            raise    

    runner = EMA.Runner(asymptotic_variable, databaseFolder=databaseFolder, customResources=[])

    problem_variable = get_problem_variable_from_asymptotic_expression(asymptotic_expression)
    
    simulation_result = get_simulation_result(runner, problem_id, input_generator_exe_path, answer_key_exe_path, resource, submission_id, problem_variable)
    analysis_result = get_analysis_result(runner, problem_id, resource, submission_id, problem_variable)

    success = False
    for equivalent_function in analysis_result['equivalent_functions']:
        if matches_asymptote(problem_variable, asymptotic_expression, asymptotic_notation, equivalent_function):
            equivalent_function['chosen'] = True
            if is_same_function(equivalent_function, analysis_result['best_guess_function']):
                analysis_result['best_guess_function']['chosen'] = True
            if is_same_function(equivalent_function, analysis_result['minimum_error_function']):
                analysis_result['minimum_error_function']['chosen'] = True
            success = True
    
    if success:
        return {
            'verdict': 'CORRECT_COMPLEXITY' if submission_id else 'READY',
            'simulation_output': simulation_result,
            'analysis_output': analysis_result,
        }

    return {
        'verdict': 'WRONG_COMPLEXITY',
        'simulation_output': simulation_result,
        'analysis_output': analysis_result,
    }
