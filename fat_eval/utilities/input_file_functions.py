import argparse
import pathlib
from collections import defaultdict


class FatigueFileReadingError(ValueError):
    pass


class KeywordData:
    def __init__(self, parameters, keyword_name):
        self.keyword_name = keyword_name
        self.parameters = parameters
        self.data = []


class OdbData:
    """
    Small helper class to handle data to be read from and to an odb-file
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
        self.field = read_keyword_parameter("field", optional=True, default="S")


def read_input_file(input_file):
    keywords = defaultdict(list)
    keyword = None

    with open(input_file, 'r') as input_file:
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
    return keywords


def argparse_check_path(path):
    if "=" in path:
        path = path.split("=")[1]
    path = pathlib.Path(path).expanduser()
    if not path.is_file():
        raise argparse.ArgumentTypeError("{0} is not a valid path to a file".format(path))
    return path
