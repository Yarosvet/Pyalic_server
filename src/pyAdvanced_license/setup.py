from setuptools import setup, find_packages

setup(
    name='pyAdvanced_license',
    version='1.0.0',
    packages=find_packages(include=['pyAdvanced_license', 'pyAdvanced_license.*']),
    install_requires=[
        'requests>=2.31.0'
    ]
)
