import subprocess
import codecs
from uuid import uuid4
import os

# write file with content
def write_to_temp_file(content, ext):
    name = str(uuid4())
    path = get_temp_file_path(name=name)
    fpath = '{0}.{1}'.format(path, ext)
    with codecs.open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
    return name

# clear temp file
def clear_temp_file(name):
    if '..' in name or name in ['*', '']:
        raise Exception('Security exception')
    subprocess.call(['rm', '{0}*'.format(get_temp_file_path(name=name))])

def get_temp_file_path(dir='', name = None):
    _dir = os.path.join('/tmp/ace', dir)
    try:
        os.makedirs(_dir)
    except OSError:
        if not os.path.isdir(_dir):
            raise    
    return os.path.join(_dir, name) if name else _dir

def get_executable_path(name):
    return get_temp_file_path(dir='executable')

def get_simulation_problem_file_path(problem_id):
    dir = os.path.join('simulation', 'problems', problem_id)
    return get_temp_file_path(dir=dir, name='solution')

def get_simulation_problem_submission_file_path(problem_id, submission_id):
    dir = os.path.join('simulation', 'problems', problem_id, 'submissions', submission_id)
    return get_temp_file_path(dir=dir, name='solution')

def get_simulation_problem_submission_graphs_path(problem_id, submission_id):
    dir = os.path.join('simulation', 'problems', problem_id, 'submissions', submission_id, 'graphs')
    return get_temp_file_path(dir=dir)