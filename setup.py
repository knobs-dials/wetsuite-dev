from setuptools import setup, find_packages

setup(
    name='wstest',
    version='0.0.10',
    url='https://github.com/scarfboy/wet-test.git',
    author='scarfboy',
    author_email='scarfboy@gmail.com',
    description='Install test',
    packages=['wetsuite'],    
    install_requires=['numpy >= 1.11.1', 'matplotlib >= 1.5.1', 'spacy', 'spacy-transformers', 'requests'], # merely suggested: 'easyocr', 
)
