"""
A nice script example on how not to code
"""
import re
import os


def get_version():

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../setup.py'), 'r') as f:
        filedata = f.read()

    return re.search("version=\"([0-9.]+)\"", filedata).group(1)


def increase_version(filename, key, old_version):

    major, minor, patch = old_version.split('.')
    new_version = ".".join([major, minor, str(int(patch)+1)])

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../' + filename), 'r') as f:
        filedata = f.read()
    filedata = filedata.replace(
        "{}\"{}\"".format(key, old_version), "{}\"{}\"".format(key, new_version))

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../' + filename), 'w') as f:
        f.write(filedata)


if __name__ == "__main__":
    version = get_version()
    increase_version("setup.py", "version=", version)
    increase_version("docs/conf.py", "version = ", version)
    increase_version("docs/conf.py", "release = ", version)
    print(version)
