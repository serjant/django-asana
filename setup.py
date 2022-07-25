#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import sys

from setuptools import setup, Command

extra = {}

# -*- Python 3 -*-
is_py3k = sys.version_info[0] == 3

# -*- Distribution Meta -*-
NAME = "django-asana"

re_meta = re.compile(r"__(\w+?)__\s*=\s*(.*)")
re_vers = re.compile(r"VERSION\s*=\s*\((.*?)\)")
re_doc = re.compile(r'^"""(.+?)"""')


def rq(s):
    return s.strip("\"'")


def add_default(m):
    attr_name, attr_value = m.groups()
    return ((attr_name, rq(attr_value)),)


def add_version(m):
    v = list(map(rq, m.groups()[0].split(", ")))
    return (("VERSION", ".".join(v[0:3]) + "".join(v[3:])),)


def add_doc(m):
    return (("doc", m.groups()[0]),)


pats = {re_meta: add_default, re_vers: add_version, re_doc: add_doc}
here = os.path.abspath(os.path.dirname(__file__))
meta_fh = open(os.path.join(here, "djasana/__init__.py"))
try:
    meta = {}
    for line in meta_fh:
        if line.strip() == "# -eof meta-":
            break
        for pattern, handler in pats.items():
            m = pattern.match(line.strip())
            if m:
                meta.update(handler(m))
finally:
    meta_fh.close()


packages, package_data = [], {}
root_dir = os.path.dirname(__file__)
if root_dir != "":
    os.chdir(root_dir)
src_dir = "djasana"


def fullsplit(path, result=None):
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == "":
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)


SKIP_EXTENSIONS = [".pyc", ".pyo", ".swp", ".swo"]


def is_unwanted_file(filename):
    return any(filename.endswith(skip_ext) for skip_ext in SKIP_EXTENSIONS)


for dirpath, dirnames, filenames in os.walk(src_dir):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith("."):
            del dirnames[i]
    parts = fullsplit(dirpath)
    package_name = ".".join(parts)
    for filename in filenames:
        if filename.endswith(".py"):
            packages.append(package_name)
        elif is_unwanted_file(filename):
            pass
        else:
            relative_path = []
            while ".".join(parts) not in packages:
                relative_path.append(parts.pop())
            relative_path.reverse()
            path = os.path.join(*relative_path)
            package_files = package_data.setdefault(".".join(parts), [])
            package_files.extend([os.path.join(path, f) for f in filenames])


class RunTests(Command):
    description = "Run the django test suite from the tests dir."
    user_options = []
    extra_env = {}
    extra_args = []

    def run(self):
        for env_name, env_value in self.extra_env.items():
            os.environ[env_name] = str(env_value)

        this_dir = os.getcwd()
        testproj_dir = os.path.join(this_dir, "tests")
        os.chdir(testproj_dir)
        sys.path.append(testproj_dir)
        from django.core.management import execute_from_command_line

        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
        prev_argv = list(sys.argv)
        try:
            sys.argv = [__file__, "test"] + self.extra_args
            execute_from_command_line(argv=sys.argv)
        finally:
            sys.argv = prev_argv

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass


class QuickRunTests(RunTests):
    extra_env = dict(SKIP_RLIMITS=1, QUICKTEST=1)


class CIRunTests(RunTests):
    @property
    def extra_args(self):
        toxinidir = os.environ.get("TOXINIDIR", "")
        return [
            "--with-coverage3",
            "--cover3-xml",
            "--cover3-xml-file=%s" % (os.path.join(toxinidir, "coverage.xml"),),
            "--with-xunit",
            "--xunit-file=%s" % (os.path.join(toxinidir, "nosetests.xml"),),
            "--cover3-html",
            "--cover3-html-dir=%s" % (os.path.join(toxinidir, "cover"),),
        ]


this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.rst")) as f:
    long_description = f.read()

# setup__(
#     name=NAME,
#     version=meta["VERSION"],
#     description=meta["doc"],
#     author=meta["author"],
#     author_email=meta["contact"],
#     packages=packages,
#     package_data=package_data,
#     cmdclass={"test": RunTests, "quicktest": QuickRunTests, "citest": CIRunTests},
#     **extra
# )

setup()
