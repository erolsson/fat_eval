import argparse
import pathlib
import sys

from collections import namedtuple

from abaqus_python_interface import OdbReadingError

from fat_eval.multiaxial_fatigue.fatigue_analysis import perform_fatigue_analysis
from fat_eval.utilities.input_file_functions import FatigueFileReadingError, read_input_file, OdbData
from fat_eval.utilities.input_file_functions import argparse_check_path

FatigueAnalysisData = namedtuple("FatigueAnalysisData", ["abaqus", "effective_stress", "material", "cyclic_stresses",
                                                         "static_stresses", "output_data", "heat_treatment"])


def parse_fatigue_file(fatigue_file):
    def read_mandatory_parameter(keyword_data, parameter_name):
        try:
            return keyword_data.parameters[parameter_name]
        except KeyError:
            raise FatigueFileReadingError(f"The parameter {par} is mandatory for the keyword "
                                          f"{keyword}".format(par=parameter_name, keyword=keyword_data.keyword_name))

    valid_keywords = {"abaqus", "effective_stress", "heat_treatment", "cyclic_stress", "static_stress", "write_to_odb"}
    mandatory_keywords = ['cyclic_stress', 'abaqus']
    mandatory_single_keywords = ['abaqus', 'effective_stress', 'heat_treatment']
    keywords = read_input_file(
        input_file=fatigue_file,
        valid_keywords=valid_keywords,
        mandatory_keywords=mandatory_keywords,
        mandatory_single_keywords=mandatory_single_keywords
    )

    abq = read_mandatory_parameter(keywords["abaqus"][0], "abq")
    effective_stress = read_mandatory_parameter(keywords["effective_stress"][0], "criterion")
    material = read_mandatory_parameter(keywords["effective_stress"][0], "material")
    cyclic_stresses = [OdbData(stress_step) for stress_step in keywords["cyclic_stress"]]
    static_stresses = [OdbData(stress_step) for stress_step in keywords["static_stress"]]
    output_data = [OdbData(output) for output in keywords["write_to_odb"]]
    heat_treatment = OdbData(keywords["heat_treatment"][0])
    return FatigueAnalysisData(abq, effective_stress, material, cyclic_stresses, static_stresses, output_data,
                               heat_treatment)


def main():
    parser = argparse.ArgumentParser(description="Run effective fatigue stress evaluations based on abaqus simulations")
    parser.add_argument("input_file", type=argparse_check_path,
                        help="Path to the file defining the fatigue evaluation")
    parser.add_argument("--cpus", type=int, help="Number of cpu cores used for the simulations")
    args = parser.parse_args()
    try:
        fatigue_analysis_data = parse_fatigue_file(args.input_file)
    except FatigueFileReadingError as e:
        print("Problems when reading the file" + str(args.input_file))
        print(e)
        sys.exit(1)
    try:
        perform_fatigue_analysis(fatigue_analysis_data, cpus=args.cpus)
    except OdbReadingError as e:
        print("Problems when reading odb files when performing fatigue analysis")
        print(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
