import numpy as np

from fat_eval.fatigue_materials.hardess_convertion_functions import HRC2HV
abaqus_fields = ["SDV_HARDNESS"]


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

    def __getitem__(self, val):
        data = {}
        for label, values in self.data.items():
            data[label] = values[val]
        return SteelData(data)

    def __len__(self):
        return len(next(iter(self.data.items()))[1])

    @property
    def HV(self):
        return HRC2HV(self.SDV_HARDNESS)


if __name__ == '__main__':
    print(SteelData({"SDV_HARDNESS": 63}).HV)
    steel_data = SteelData({"SDV_HARDNESS": np.array([62, 63, 64, 65]),
                            "SDV_AUSTENITE": np.array([0.18, 0.19, 0.20, 21])})

    print(steel_data[1:3].HV)
