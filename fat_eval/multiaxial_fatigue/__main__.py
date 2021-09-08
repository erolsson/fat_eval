import argparse
import pathlib
import sys

from collections import defaultdict, namedtuple

from abaqus_python_interface import OdbReadingError

from fatigue_analysis import perform_fatigue_analysis


class KeywordData:
    def __init__(self, parameters, keyword_name):
        self.keyword_name = keyword_name
        self.parameters = parameters
        self.data = []


class OdbData:
    """
    Small helper class to handle
    """
    def __init__(self, keyword_data):
        def read_keyword_parameter(parameter_name, optional=False, default=None):
            try:
                return keyword_data.parameters[parameter_name]
            except KeyError:
                if optional:
                    return default
                raise FatigueFileReadingError("The parameter {par} is mandatory for the keyword *"
                                              "{keyword}".format(par=parameter_name, keyword=keyword_data.keyword_name))
        self.odb_file_name = pathlib.Path(read_keyword_parameter("odb_file")).expanduser()
        self.step_name = read_keyword_parameter("step", optional=True, default=None)
        self.frame_number = read_keyword_parameter("frame", optional=True, default=-1)
        self.element_set = read_keyword_parameter("element_set", optional=True, default='')
        self.instance = read_keyword_parameter("instance", optional=True, default=None)
        self.factor = float(read_keyword_parameter("factor", optional=True, default=1.))


class FatigueFileReadingError(ValueError):
    pass


FatigueAnalysisData = namedtuple("FatigueAnalysisData", ["abaqus", "effective_stress", "material", "cyclic_stresses",
                                                         "static_stresses", "output_data", "heat_treatment"])


def parse_fatigue_file(fatigue_file):
    def read_mandatory_parameter(keyword_data, parameter_name):
        try:
            return keyword_data.parameters[parameter_name]
        except KeyError:
            raise FatigueFileReadingError(f"The parameter {par} is mandatory for the keyword "
                                          f"{keyword}".format(par=parameter_name, keyword=keyword_data.keyword_name))
    keywords = defaultdict(list)
    keyword = None

    with open(fatigue_file, 'r') as input_file:
        file_lines = input_file.readlines()
        for i, line in enumerate(file_lines, 1):
            line = line.replace(' ', '').rstrip()
            if not line.startswith('**') and len(line):
                line = line.replace(' ', '').rstrip()
                words = line.split(',')
                if line.startswith('*'):
                    keyword = words[0][1:].lower()
                    parameters = words[1:]
                    parameter_dict = {}
                    for parameter in parameters:
                        par_words = parameter.split("=")
                        parameter_dict[par_words[0]] = par_words[1]
                    keywords[keyword].append(KeywordData(parameter_dict, keyword))
                elif keyword is not None:
                    keywords[keyword][-1].data.append(line)
                else:
                    raise FatigueFileReadingError("The data line \n\t{0} \ncannot appear at line {1} of the "
                                                  "file".format(line, i))
    # Sanity check of the inputs, only one abaqus and one effective_stress keyword are allowed to appear in the file
    mandatory_single_keywords = ['abaqus', 'effective_stress', 'heat_treatment']
    for keyword in mandatory_single_keywords:
        if len(keywords[keyword]) != 1:
            raise FatigueFileReadingError(f"The keyword *{keyword} is mandatory and must appear only once "
                                          f"in the file".format(keyword=keyword))

    mandatory_keywords = ['cyclic_stress']
    for keyword in mandatory_keywords:
        if len(keywords[keyword]) == 0:
            raise FatigueFileReadingError(f"The keyword *{keyword} is mandatory and must in the "
                                          f"file".format(keyword=keyword))

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
    def argparse_check_path(path):
        if "=" in path:
            path = path.split("=")[1]
        path = pathlib.Path(path).expanduser()
        if not path.is_file():
            raise argparse.ArgumentTypeError("{0} is not a valid path to a file".format(path))
        return path

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
