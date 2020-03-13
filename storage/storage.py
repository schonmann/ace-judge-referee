import subprocess
import codecs
from uuid import uuid4
import os

# write file with content
def write_to_temp_file(content, ext):
    name = str(uuid4())
    path = get_temp_file_path(name)
    fpath = '{0}.{1}'.format(path, ext)
    with codecs.open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
    return name

# clear temp file
def clear_temp_file(name):
    if '..' in name or name in ['*', '']:
        raise Exception('Security exception')
    subprocess.call(['rm', '{0}*'.format(get_temp_file_path(name))])

def get_temp_file_path(name):
    try:
        os.makedirs('/tmp/ace')
    except OSError:
        if not os.path.isdir('/tmp/ace'):
            raise    
    return '/tmp/ace/{0}'.format(name)