import pathlib
from setuptools import setup

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    name='fat_eval',
    version='0.0.1',
    packages=['fat_eval', 'fat_eval.materials', 'fat_eval.weakest_link', 'fat_eval.weakest_link.FEM_functions',
              'fat_eval.multiaxial_fatigue'],
    url='',
    license='',
    long_description=README,
    long_description_content_type="text/markdown",
    install_requires=["numpy", "abaqus_python_interface"],
    author='erolsson',
    author_email='erolsson@kth.se',
    description='',
    entry_points={"console_scripts":
                  ["evaluate_fatigue_stress=fat_eval.multiaxial_fatigue.__main__:main"]}
)
