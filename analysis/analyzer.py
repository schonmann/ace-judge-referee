from lib import EMA
from storage.stream import redirect_stdout_to
import storage.storage
import parser
from utils.command import run_command_timeout

# Tests if the target function matches the asymptote
def matches_asymptote(asymptotic_function, asymptotic_notation, target_function):
    return True

def get_simulation_result(runner, problem_id, input_generator_exe_path=None, answer_key_exe_path=None, resource="Time"):
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

    path = storage.storage.get_simulation_file_path(problem_id)
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

def get_analysis_result(runner, problem_id, resource="Time"):
    # Compute EMA's analysis results for the problem
    path = storage.storage.get_analysis_file_path(problem_id)
    with open(path, 'w+') as file:
        @redirect_stdout_to(file)
        def run_analysis():
            fn = runner.getResourceUsageFunction(resource, discardTimeUnder=10, case='mean', equivalenceThreshold=0.005,
                            tieBreakMaxVal=0, discreteFunctionsOnly=False, printFunctionReport=True)
            titleStr = runner.getFunctionString(resource,fn[-1][1],True)
        run_analysis()
        file.seek(0)
        return parser.parse_analysis_result(file.read())

def verdict(problem_id, answer_key_exe_path, input_generator_exe_path, asymptotic_function, asymptotic_notation):
    # Get EMA's verdict for the problem
    resource = "Time"
    
    runner = EMA.Runner(["N"], databaseFolder="./emafiles/%s/" % problem_id, customResources=[])
    
    simulation_result = get_simulation_result(runner, problem_id, input_generator_exe_path, answer_key_exe_path, resource)
    analysis_result = get_analysis_result(runner, problem_id, resource)

    for equivalent_function in analysis_result['equivalent_functions']:
        if matches_asymptote(asymptotic_function, asymptotic_notation, equivalent_function):
            return {
                'verdict': 'READY',
                'simulation_result': simulation_result,
                'analysis_result': analysis_result
            }

    return {
        'verdict': 'WRONG_COMPLEXITY',
        'simulation_result': simulation_result,
        'analysis_result': analysis_result
    }
