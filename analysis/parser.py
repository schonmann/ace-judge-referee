import re
from exceptions import EmpyricalAnalysisParseError
import sympy

def get_sympy_globals():
    global_vars = globals().copy()
    global_vars.update(vars(sympy))
    return global_vars

def sanitize_fn_section(fn_section):
    return fn_section.strip().replace(' ', '').replace(',Monomial()', '') .split('\n')

def parse_simulation_result(buffer):
    print('asdasd')

def get_fn_full_expression(fn):
    full_expression = fn['expression']
    for idx, param in enumerate(fn['parameters']):
        full_expression = full_expression.replace(param, str(fn['values'][idx]))
    return full_expression

def normalize_fn_str(fn_str):
    toople = eval(fn_str)
    fn = {
        'expression': toople[0],
        'parameters': toople[1].split(','),
        'error': toople[2],
        'values': toople[3],
    }
    x = sympy.symbols('x')
    fn['full_expression'] = get_fn_full_expression(fn)
    fn['latex_expression'] = sympy.latex(eval(fn['full_expression'], get_sympy_globals(), locals()))
    return fn

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