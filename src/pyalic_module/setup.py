"""Setup pyalic module"""
import os
from setuptools import setup, find_packages

with open("../../README.md", "r", encoding='utf-8') as readme_file:
    readme = readme_file.read()


def requirements():
    """Get current requirements"""
    with open(os.path.join(os.path.dirname(__file__), "requirements.txt"), 'r', encoding='utf-8') as f:
        return [line.strip() for line in f.readlines()]


setup(
    name='pyalic',
    version='1.0.0',
    author='Yarosvet',
    description="Licensing system module which allows you to manage access to your products with ease",
    long_description_content_type="text/markdown",
    long_description=readme,
    url="https://github.com/Yarosvet/Pyalic",
    packages=find_packages(include=['pyalic', 'pyalic.*']),
    install_requires=[*requirements()],
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: GNU Lesser General Public License v2 (LGPLv2)",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ]
)
