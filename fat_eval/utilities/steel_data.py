from fat_eval.materials.hardess_convertion_functions import HRC2HV
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

    @property
    def HV(self):
        return HRC2HV(self.SDV_HARDNESS)


if __name__ == '__main__':
    print(SteelData({"SDV_HARDNESS": 63}).HV)
