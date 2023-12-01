"""Setup pyalic module"""
import os
from setuptools import setup, find_packages


def requirements():
    """Get current requirements"""
    with open(os.path.join(os.path.dirname(__file__), "requirements.txt"), 'r', encoding='utf-8') as f:
        return [line.strip() for line in f.readlines()]


setup(
    name='pyalic',
    version='1.0.0',
    packages=find_packages(include=['pyalic', 'pyalic.*']),
    install_requires=[*requirements()]
)
