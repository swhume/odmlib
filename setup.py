from setuptools import setup
import pathlib

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()
# in setup:
# install_requires=[packages needed for the install to work]
# entry_points={ "console_scripts":=["realpython"=reader.__main__:main",] }

setup(
    name='odmlib',
    version='0.1.0',
    packages=['tests', 'odmlib', 'odmlib.odm_2_0', 'odmlib.odm_1_3_2', 'odmlib.odm_1_3_2.rules', 'odmlib.define_2_0',
              'odmlib.define_2_1'],
    url='https://github.com/swhume/odmlib',
    license='MIT',
    author='Sam Hume',
    author_email='swhume@gmail.com',
    description='Work with ODM as Python objects',
    log_description=README,
    long_description_content_type="text/markdown",
    include_package_data=True
    install_requires=[
        "xmlschema>=1.3.1",
        "validators>=0.18.1",
        "Cerberus>=1.3.2",
        "pathvalidate>=2.3.1",
        "setuptools>=44.1.1"
    ]
)
