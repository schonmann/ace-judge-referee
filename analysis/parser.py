import re
from exceptions import EmpyricalAnalysisParseError

def sanitize_fn_section(fn_section):
    return fn_section.strip().replace(' ', '').replace(',Monomial()', '') .split('\n')

def parse_simulation_result(buffer):
    print('asdasd')

def normalize_fn_str(fn_str):
    toople = eval(fn_str)
    return {
        'expression': toople[0],
        'parameters': toople[1].split(','),
        'error': toople[2],
        'values': toople[3],
    }

def parse_minimum_error_fn(buffer):
    pattern = r"(?s)MINIMUM ERROR function:(.*?)------------------------------------------------"
    matches = re.findall(pattern, buffer)
    if len(matches) == 0:
        raise EmpyricalAnalysisParseError('error parsing minimum error function: no matches')
    fns = sanitize_fn_section(matches[0])
    if len(fns) == 0:
        raise EmpyricalAnalysisParseError('error parsing minimum error function: empty function array')
    return normalize_fn_str(fns[0])

def parse_equivalent_fns(buffer):
    pattern = r"(?s)EQUIVALENT.*threshold\)(.*?)------------------------------------------------"
    matches = re.findall(pattern, buffer)
    if len(matches) == 0: 
        raise EmpyricalAnalysisParseError('error parsing equivalent functions: no matches')
    fns = sanitize_fn_section(matches[0])
    if len(fns) == 0:
        raise EmpyricalAnalysisParseError('error parsing equivalent functions: empty function array')
    return map(normalize_fn_str, fns)

def parse_best_guess_fn(buffer):
    pattern = r"(?s)BEST-GUESS function:(.*?)------------------------------------------------"
    matches = re.findall(pattern, buffer)
    if len(matches) == 0:
        raise EmpyricalAnalysisParseError('error parsing best guess function: no matches')
    fns = sanitize_fn_section(matches[0])
    if len(fns) == 0:
        raise EmpyricalAnalysisParseError('error parsing best guess function: empty function array')
    return normalize_fn_str(fns[0])

def parse_analysis_result(buffer):
    return {
        'minimum_error_function': parse_minimum_error_fn(buffer),
        'equivalent_functions': parse_equivalent_fns(buffer),
        'best_guess_function': parse_best_guess_fn(buffer),
    }