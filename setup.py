from setuptools import setup, find_packages

setup(
    name = 'md',
    version = '0.1',
    packages = find_packages(exclude=('tests',)),
    scripts = ['bin/pytest'],
    test_suite='tests.all',
    tests_require = ['docutils>=0.5'],

    author = 'Medium',
    author_email = 'ben.weaver@coptix.com',
    description = 'A collection of Python utilities.',
    license = 'BSD',
    keywords = 'utilities transaction transactions fluid dynamic',
    url = 'http://thisismedium.com/foo'
)
