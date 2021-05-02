from setuptools import setup, find_packages

DEPENDENCIES = [
    'pandas',
    'dash',
    'dash-bootstrap-components',
    'dash-daq',
    'dash-auth',
    'cryptography',
    'gunicorn'
]

with open("README.md", "r") as f:
    readme = f.read()


setup(
    name='px_speedread',
    version='1.0.0',
    description='PX Method Speed-Reading Performance Tracker',
    long_description=readme,
    author='Krzysztof Czarnecki',
    author_email='kjczarne@gmail.com',
    install_requires=DEPENDENCIES
)
