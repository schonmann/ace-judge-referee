import os

from languages import *
from uuid import uuid4
from exceptions import *
import subprocess

# write file with content
def _write_to_temp_file(solution, language):
    fid = str(uuid4())
    ext = language_extension[language]
    path = _get_temp_file_path(fid)
    fpath = '{0}.{1}'.format(path, ext)
    with open(fpath, 'w') as f:
        f.write(solution)
    return fid

# clear temp file
def _clear_temp_file(fid):
    if '..' in fid or fid in ['*', '']:
        raise Exception('Securibrty exception')
    subprocess.call(['rm', '{0}*'.format(_get_temp_file_path(fid))])

def _get_temp_file_path(fid):
    try:
        os.makedirs('/tmp/ace')
    except OSError:
        if not os.path.isdir('/tmp/ace'):
            raise    
    return '/tmp/ace/{0}'.format(fid)

def _compile_cpp(fid):
    path = _get_temp_file_path(fid)
    output = subprocess.call(['g++', '-lm', '-lcrypt', '-O2', '-pipe', '{0}.cpp'.format(path), '-o', path])
    if output != 0:
        raise Exception('Failed to compile: {0}'.format(output))
    return path

def _compile_python():
    return ''

def _compile_java():
    return ''

def _compile_c(fid):
    path = _get_temp_file_path(fid)
    code = subprocess.call(['gcc', '{0}.c'.format(path), '-o', path])
    if code != 0:
        raise CompileError('Failed to compile. Code = {0}'.format(code))
    return path

# string, string
def compile(solution, language):

    lang_upper = language.upper()

    if lang_upper not in language_extension:
        raise UnsupportedLangError('Invalid programming language!')

    solution_id = _write_to_temp_file(solution, lang_upper)

    if lang_upper == C:
        return _compile_c(solution_id)
    if lang_upper == CPP:
        return _compile_cpp(solution_id)
    if lang_upper == PYTHON:
        return _compile_python(solution_id)
    if lang_upper == JAVA:
        return _compile_java(solution_id)
        
    raise UnsupportedLangError('Invalid programming language!')
