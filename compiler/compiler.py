import os
from languages import *
from exceptions import *
import subprocess
from storage import storage

def compile_cpp(fid):
    path = storage.get_temp_file_path(name=fid)
    output = subprocess.call(['g++', '-lm', '-lcrypt', '-O2', '-pipe', '{0}.cpp'.format(path), '-o', path])
    if output != 0:
        raise CompileError('Failed to compile: {0}'.format(output))
    return path

def compile_python(fid):
    path = storage.get_temp_file_path(name=fid)

def compile_java():
    return ''

def compile_c(fid):
    path = storage.get_temp_file_path(name=fid)
    code = subprocess.call(['gcc', '{0}.c'.format(path), '-o', path])
    if code != 0:
        raise CompileError('Failed to compile. Code = {0}'.format(code))
    return path

# string, string
def compile(solution, language):

    lang_upper = language.upper()

    if lang_upper not in language_extension:
        raise UnsupportedLangError('Invalid programming language!')

    solution_id = storage.write_to_temp_file(content=solution, ext=language_extension[lang_upper])

    if lang_upper == C:
        return compile_c(solution_id)
    if lang_upper == CPP:
        return compile_cpp(solution_id)
    if lang_upper == PYTHON:
        return compile_python(solution_id)
    if lang_upper == JAVA:
        return compile_java(solution_id)
        
    raise UnsupportedLangError('Invalid programming language!')
