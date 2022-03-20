from setuptools import setup
import pathlib

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    name='odmlib',
    version='0.1.4',
    packages=['odmlib', 'tests', 'odmlib.odm_1_3_2', 'odmlib.odm_1_3_2.rules', 'odmlib.define_2_0',
              'odmlib.define_2_0.rules', 'odmlib.define_2_1', 'odmlib.define_2_1.rules', 'odmlib.ct_1_1_1',
              'odmlib.dataset_1_0_1', ],
    url='https://github.com/swhume/odmlib',
    license='MIT',
    author='Sam Hume',
    author_email='swhume@gmail.com',
    description='Work with ODM as Python objects',
    long_description=README,
    long_description_content_type="text/markdown",
    include_package_data=True,
    install_requires=[
        "xmlschema>=1.10.0",
        "validators>=0.18.2",
        "Cerberus>=1.3.4",
        "pathvalidate>=2.3.1"
    ]
)
