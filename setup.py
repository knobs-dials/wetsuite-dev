from setuptools import setup, find_packages

setup(
    name='wetsuite',
    version='0.0.10',
    classifiers=['Development Status :: 2 - Pre-Alpha', 'Programming Language :: Python :: 3', 'Topic :: Text Processing :: Linguistic'],
    url='https://github.com/scarfboy/wetsuite.git',
    author='scarfboy',
    author_email='scarfboy@gmail.com',
    description='Wetsuite',
    packages=['wetsuite.datasets', 'wetsuite.helpers', 'wetsuite.phrases', 'wetsuite.datacollect', 'wetsuite.extras'],
    package_dir={"": "src"},
    python_requires=">=3",
    install_requires=['requests', 'numpy >= 1.11.1', 'matplotlib >= 1.5.1', 'spacy', 'spacy-transformers', 'dateutil' ],
    extras_require={
        'spacy-cpu':'spacy',
        'spacy-cuda80':'spacy[cuda80]',
        'spacy-cuda90':'spacy[cuda90]','spacy-cuda91':'spacy[cuda91]','spacy-cuda92':'spacy[cuda92]',
        'spacy-cuda100':'spacy[cuda100]','spacy-cuda101':'spacy[cuda101]','spacy-cuda102':'spacy[cuda102]','spacy-cuda110':'spacy[cuda110]',
        'spacy-cuda111':'spacy[cuda111]','spacy-cuda112':'spacy[cuda112]','spacy-cuda113':'spacy[cuda113]','spacy-cuda114':'spacy[cuda114]','spacy-cuda115':'spacy[cuda115]','spacy-cuda116':'spacy[cuda116]','spacy-cuda117':'spacy[cuda117]',
        'fastlang': ['spacy_fastlang','fasttext'],
        'ocr':'easyocr',
        # all?
    },
)
