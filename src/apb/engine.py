import os
import uuid
import base64
import yaml

import shutil

PLAYBOOKS_DIR = 'playbooks'
ROLES_DIR = 'roles'

DAT_DIR = 'dat'
DAT_PATH = os.path.join(os.path.dirname(__file__), DAT_DIR)

SPEC_FILE = 'apb.yml'
EX_SPEC_FILE = 'ex.apb.yml'
EX_SPEC_FILE_PATH = os.path.join(DAT_PATH, EX_SPEC_FILE)

DOCKERFILE = 'Dockerfile'
EX_DOCKERFILE = 'ex.Dockerfile'
EX_DOCKERFILE_PATH = os.path.join(DAT_PATH, EX_DOCKERFILE)

SPEC_LABEL = 'com.redhat.apb.spec'
VERSION_LABEL = 'com.redhat.apb.version'


def load_dockerfile(df_path):
    with open(df_path, 'r') as dockerfile:
        return dockerfile.readlines()


def load_example_specfile():
    with open(EX_SPEC_FILE_PATH, 'r') as spec_file:
        return spec_file.readlines()


def write_dockerfile(dockerfile, destination, force):
    touch(destination, force)
    with open(destination, 'w') as outfile:
        outfile.write(''.join(dockerfile))


def write_specfile(spec_file, destination, force):
    touch(destination, force)
    with open(destination, 'w') as outfile:
        outfile.write(''.join(spec_file))


def insert_encoded_spec(dockerfile, encoded_spec_lines):
    apb_spec_idx = [i for i, line in enumerate(dockerfile)
                    if SPEC_LABEL in line][0]
    if not apb_spec_idx:
        raise Exception(
            "ERROR: %s missing from dockerfile while inserting spec blob" %
            SPEC_LABEL
        )

    # Set end_spec_idx to a list of all lines ending in a quotation mark
    end_spec_idx = [i for i, line in enumerate(dockerfile)
                    if line.endswith('"\n')]

    # Find end of spec label if it already exists
    if end_spec_idx:
        for correct_end_idx in end_spec_idx:
            if correct_end_idx > apb_spec_idx:
                end_spec_idx = correct_end_idx
                del dockerfile[apb_spec_idx+1:end_spec_idx+1]
                break

    split_idx = apb_spec_idx + 1
    offset = apb_spec_idx + len(encoded_spec_lines) + 1

    # Insert spec label
    dockerfile[split_idx:split_idx] = encoded_spec_lines

    # Insert newline after spec label
    dockerfile.insert(offset, "\n")

    return dockerfile


def gen_spec_id(spec, spec_path):
    new_id = str(uuid.uuid4())
    spec['id'] = new_id

    with open(spec_path, 'r') as spec_file:
        lines = spec_file.readlines()
        insert_i = 1 if lines[0] == '---' else 0
        id_kvp = "id: %s\n" % new_id
        lines.insert(insert_i, id_kvp)

    with open(spec_path, 'w') as spec_file:
        spec_file.writelines(lines)


def is_valid_spec(spec):
    # TODO: Implement
    # NOTE: spec is a loaded spec
    return True


def load_spec_dict(spec_path):
    with open(spec_path, 'r') as spec_file:
        return yaml.load(spec_file.read())


def load_spec_str(spec_path):
    with open(spec_path, 'r') as spec_file:
        return spec_file.read()


# NOTE: Splits up an encoded blob into chunks for insertion into Dockerfile
def make_friendly(blob):
    line_break = 76
    count = len(blob)
    chunks = count / line_break
    mod = count % line_break

    flines = []
    for i in range(chunks):
        fmtstr = '{0}\\\n'

        # Corner cases
        if chunks == 1:
            # Exactly 76 chars, two quotes
            fmtstr = '"{0}"\n'
        elif i == 0:
            fmtstr = '"{0}\\\n'
        elif i == chunks - 1 and mod == 0:
            fmtstr = '{0}"\n'

        offset = i * line_break
        line = fmtstr.format(blob[offset:(offset + line_break)])
        flines.append(line)

    if mod != 0:
        # Add incomplete chunk if we've got some left over,
        # this is the usual case
        flines.append('{0}"'.format(blob[line_break * chunks:]))

    return flines


def touch(fname, force):
    if os.path.exists(fname):
        os.utime(fname, None)
        if force:
            os.remove(fname)
            open(fname, 'a').close()
    else:
        open(fname, 'a').close()


def update_dockerfile(spec_path, dockerfile_path):
    # TODO: Defensively confirm the strings are encoded
    # the way the code expects
    blob = base64.b64encode(load_spec_str(spec_path))
    dockerfile_out = insert_encoded_spec(
        load_dockerfile(dockerfile_path), make_friendly(blob)
    )

    write_dockerfile(dockerfile_out, dockerfile_path, False)
    print('Finished writing dockerfile.')


def cmdrun_init(**kwargs):
    print("Initializing current directory for an APB")
    current_path = kwargs['base_path']
    apb_name = kwargs['name']
    project = os.path.join(current_path, apb_name)

    if os.path.exists(project):
        if not kwargs['force']:
            raise Exception('ERROR: Project directory: [%s] found and force option not specified' % project)
        shutil.rmtree(project)

    os.mkdir(project)

    spec_path = os.path.join(project, SPEC_FILE)
    playbooks_path = os.path.join(project, PLAYBOOKS_DIR)
    roles_path = os.path.join(project, ROLES_DIR)
    dockerfile_path = os.path.join(os.path.join(project, DOCKERFILE))

    if os.path.exists(spec_path) and not kwargs['force']:
        raise Exception('ERROR: Spec file: [%s] found and force option not specified' % spec_path)

    specfile_out = load_example_specfile()
    write_specfile(specfile_out, spec_path, kwargs['force'])

    dockerfile_out = load_dockerfile(EX_DOCKERFILE_PATH)
    write_dockerfile(dockerfile_out, dockerfile_path, kwargs['force'])

    if os.path.exists(playbooks_path):
        if not kwargs['force']:
            raise Exception('ERROR: Playbooks dir: [%s] was found and force option not specified. Forcing a reinit will recreate the directory.' % playbooks_path)
        shutil.rmtree(playbooks_path)

    os.mkdir(playbooks_path)

    if os.path.exists(roles_path):
        if not kwargs['force']:
            raise Exception('ERROR: Roles dir: [%s] was found and force option not specified. Forcing a reinit will recreate the directory.' % role_path)
        shutil.rmtree(roles_path)

    os.mkdir(roles_path)


def cmdrun_prepare(**kwargs):
    project = kwargs['base_path']
    spec_path = os.path.join(project, SPEC_FILE)
    dockerfile_path = os.path.join(os.path.join(project, DOCKERFILE))

    if not os.path.exists(spec_path):
        raise Exception('ERROR: Spec file: [ %s ] not found' % spec_path)

    try:
        spec = load_spec_dict(spec_path)
    except Exception as e:
        print('ERROR: Failed to load spec!')
        raise e

    # ID specfile if it hasn't already been done
    if 'id' not in spec:
        gen_spec_id(spec, spec_path)

    if not is_valid_spec(spec):
        fmtstr = 'ERROR: Spec file: [ %s ] failed validation'
        raise Exception(fmtstr % spec_path)

    update_dockerfile(spec_path, dockerfile_path)


def cmdrun_build(**kwargs):
    raise Exception('ERROR: BUILD NOT YET IMPLEMENTED!')
