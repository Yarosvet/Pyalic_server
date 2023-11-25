from setuptools import setup, find_packages

setup(
    name='pyalic',
    version='1.0.0',
    packages=find_packages(include=['pyalic', 'pyalic.*']),
    install_requires=[
        'requests>=2.31.0'
    ]
)
