import re
from exceptions import EmpyricalAnalysisParseError
from utils.number import round_decimals_up
import sympy

PARAMETER_TYPE_CONSTANT="c"
PARAMETER_TYPE_EXPONENT="e"
PARAMETER_TYPE_COEFFICIENT="a"

def sanitize_fn_section(fn_section):
    return fn_section.strip().replace(' ', '').replace(',Monomial()', '') .split('\n')

def parse_simulation_result(buffer, problem_variable=None):
    print('asdasd')

def get_fn_full_expression(fn):
    full_expression = fn['expression']
    for idx, param in enumerate(fn['parameters']):
        full_expression = full_expression.replace(param, str(fn['values'][idx]))
    return full_expression

def get_fn_full_expression(fn):
    full_expression = fn['expression']
    for idx, param in enumerate(fn['parameters']):
        full_expression = full_expression.replace(param, str(fn['values'][idx]))
    return full_expression

def get_fn_full_asymptiotic_expression(fn):
    expression = sympy.S(fn['expression'])
    for idx, param in enumerate(fn['parameters']):
        value = fn['values'][idx]
        param_type = param[0]
        if param_type == PARAMETER_TYPE_CONSTANT:
            value = 0
        elif param_type == PARAMETER_TYPE_COEFFICIENT:
            value = 1
        elif param_type == PARAMETER_TYPE_EXPONENT:
            value = round_decimals_up(value, 1)
        expression = expression.subs(param, value)
    expression_with_theta = sympy.sympify("Theta(expr)", locals={'expr': expression })
    return str(expression_with_theta)

def normalize_fn_str(fn_str, problem_variable=None):
    variable = sympy.var(problem_variable if problem_variable else 'x')
    toople = eval(fn_str)
    fn = {
        'expression': str(sympy.S(toople[0]).subs("x", variable)),
        'parameters': toople[1].split(','),
        'error': toople[2],
        'values': toople[3],
        'chosen': False,
    }

    fn['full_expression'] = get_fn_full_expression(fn)
    fn['full_asymptotic_expression'] = get_fn_full_asymptiotic_expression(fn)

    fn['latex_expression'] = sympy.latex(sympy.S(fn['full_expression']))
    fn['latex_asymptotic_expression'] = sympy.latex(sympy.S(fn['full_asymptotic_expression']))

    return fn

def parse_minimum_error_fn(buffer, problem_variable=None):
    pattern = r"(?s)MINIMUM ERROR function:(.*?)------------------------------------------------"
    matches = re.findall(pattern, buffer)
    if len(matches) == 0:
        raise EmpyricalAnalysisParseError('error parsing minimum error function: no matches')
    fns = sanitize_fn_section(matches[0])
    if len(fns) == 0:
        raise EmpyricalAnalysisParseError('error parsing minimum error function: empty function array')
    return normalize_fn_str(fns[0], problem_variable)

def parse_equivalent_fns(buffer, problem_variable=None):
    pattern = r"(?s)EQUIVALENT.*threshold\)(.*?)------------------------------------------------"
    matches = re.findall(pattern, buffer)
    if len(matches) == 0: 
        raise EmpyricalAnalysisParseError('error parsing equivalent functions: no matches')
    fns = sanitize_fn_section(matches[0])
    if len(fns) == 0:
        raise EmpyricalAnalysisParseError('error parsing equivalent functions: empty function array')
    return map(lambda fn: normalize_fn_str(fn, problem_variable), fns)

def parse_best_guess_fn(buffer, problem_variable=None):
    pattern = r"(?s)BEST-GUESS function:(.*?)------------------------------------------------"
    matches = re.findall(pattern, buffer)
    if len(matches) == 0:
        raise EmpyricalAnalysisParseError('error parsing best guess function: no matches')
    fns = sanitize_fn_section(matches[0])
    if len(fns) == 0:
        raise EmpyricalAnalysisParseError('error parsing best guess function: empty function array')
    return normalize_fn_str(fns[0], problem_variable)

def parse_analysis_result(buffer, problem_variable=None):
    return {
        'minimum_error_function': parse_minimum_error_fn(buffer, problem_variable),
        'equivalent_functions': parse_equivalent_fns(buffer, problem_variable),
        'best_guess_function': parse_best_guess_fn(buffer, problem_variable),
    }