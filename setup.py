from setuptools import setup, find_packages

setup(
    name='wetsuite',
    version='0.0.10',
    url='https://github.com/scarfboy/wetsuite.git',
    author='scarfboy',
    author_email='scarfboy@gmail.com',
    description='Install test',
    packages=['datasets'],
    package_dir={"": "src", "datasets":"src/datasets"},
    install_requires=['numpy >= 1.11.1', 'matplotlib >= 1.5.1', 'spacy', 'spacy-transformers', 'requests'], # merely suggested: 'easyocr', 
    extras_require={
        'spacy-cpu': 'spacy',
        'spacy-cuda110': 'spacy[cuda110]',
        'fastlang': ['spacy_fastlang','fasttext'],
        'ocr':'easyocr',
        # all?
    },
)
