from collections import namedtuple

import numpy as np

from multiprocesser import multi_processer


class SteelData:
    """
    Small helper class for handling different steel properties like hardness and retained austenite when
    evaluating different fatigue criteria
    """
    def __init__(self, data):
        self.data = data

    def __getattribute__(self, item):
        try:
            return object.__getattribute__(self, "data")[item]
        except KeyError:
            return object.__getattribute__(self, item)

    def __reduce_ex__(self, protocol):
        return self.__class__, (self.data, )


def evaluate_effective_stress(stress_history, material, criterion, cpus=1, **steel_data):
    """
    Function for evaluating different effective fatigue stresses using multiple cpus
    :param stress_history:  3d - numpy_array with the stress history, first index represent the time, second index the
                            points and the third index the stress components
    :param steel_data:      keyword arguments for providing needed data of the steel to determine material properties
    :param material:        instance of a material class that contains functions for material parameters needed
                            in the effective stress calculation based on steel data
    :param criterion        the criterion to be evaluated, current implemented criteria can be imported from
                            fat_eval.multiaxial_fatigue.criteria
    :param cpus             The number of cpus used for the evaluation
    :returns                A numpy array with effective fatigue stress values
    """

    steel_data_list = [{}]*cpus
    stress_history_chuncks = np.array_split(stress_history, cpus, axis=1)
    for field_name, data in steel_data.items():
        field_data = np.array_split(data, cpus)
        for i in range(cpus):
            steel_data_list[i][field_name] = field_data[i]
    steel_data = []
    for data in steel_data_list:
        steel_data.append(SteelData(data))
    job_list = [(criterion,  [stress, data, material], {}) for stress, data in zip(stress_history_chuncks, steel_data)]
    results = multi_processer(job_list, cpus=cpus, delay=0, timeout=1e9)

    return np.vstack(results)


def main():
    """
    Function for testing the functionality in-place
    :return nothing:
    """
    from fat_eval.materials.fatigue_materials import SS2506
    from fat_eval.multiaxial_fatigue.criteria import haigh
    num_points = 3000

    stress_history = np.zeros((4, num_points, 6))
    hv = np.zeros(num_points) + 750
    austenite = np.zeros(num_points)
    evaluate_effective_stress(stress_history, SS2506, haigh, hv=hv, austenite=austenite, cpus=8)


if __name__ == '__main__':
    main()
