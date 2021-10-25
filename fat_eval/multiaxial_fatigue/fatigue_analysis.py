import sys

import numpy as np

from fat_eval.multiaxial_fatigue.criteria import criteria
from fat_eval.materials.fatigue_materials import materials
from fat_eval.materials.hardess_convertion_functions import HRC2HV
from fat_eval.multiaxial_fatigue.evaluation import evaluate_effective_stress
from abaqus_python_interface import ABQInterface, OdbWritingError
from fat_eval.utilities.steel_data import abaqus_fields


class StressFieldError(ValueError):
    pass


def perform_fatigue_analysis(fatigue_analysis_data, cpus=1):
    abq = ABQInterface(fatigue_analysis_data.abaqus, output=False)
    stress_history = None
    for i, cyclic_stress in enumerate(fatigue_analysis_data.cyclic_stresses):
        print("Reading cyclic stresses " + str(i+1))
        stress = abq.read_data_from_odb(odb_file_name=cyclic_stress.odb_file_name, field_id='S',
                                        step_name=cyclic_stress.step_name,
                                        frame_number=int(cyclic_stress.frame_number),
                                        set_name=cyclic_stress.element_set,
                                        instance_name=cyclic_stress.instance)*cyclic_stress.factor
        if stress_history is None:
            points, components = stress.shape
            stress_history = np.zeros((len(fatigue_analysis_data.cyclic_stresses), points, components))
        if stress.shape != stress_history[i, :, :].shape:
            raise StressFieldError("The stress in *cyclic_stress " + str(i+1) + " has wrong shape")

        stress_history[i, :, :] = stress

    for k, static_stress in enumerate(fatigue_analysis_data.static_stresses, 1):
        print("Reading static stresses " + str(k))
        stress = abq.read_data_from_odb(odb_file_name=static_stress.odb_file_name, field_id='S',
                                        step_name=static_stress.step_name,
                                        frame_number=int(static_stress.frame_number),
                                        set_name=static_stress.element_set,
                                        instance_name=static_stress.instance)*static_stress.factor

        for i in range(len(fatigue_analysis_data.cyclic_stresses)):
            try:
                stress_history[i, :, :] += stress
            except ValueError:
                raise StressFieldError("Problems when adding the stress field in *static_stress " + str(k)
                                       + " to the stress history")
    heat_treatment = fatigue_analysis_data.heat_treatment
    heat_treatment_data = {}
    for heat_treatment_field in abaqus_fields:
        print("Reading " + heat_treatment_field)
        field = abq.read_data_from_odb(
            odb_file_name=heat_treatment.odb_file_name,
            field_id=heat_treatment_field,
            step_name=heat_treatment.step_name,
            frame_number=heat_treatment.frame_number,
            set_name=heat_treatment.element_set,
            instance_name=heat_treatment.instance)
        if field.shape[0] != stress_history.shape[1]:
            raise StressFieldError("The field " + heat_treatment_field + "  in " + str(heat_treatment.odb_file_name)
                                   + " has a different shape than the stress field")
        heat_treatment_data[heat_treatment_field] = field
    criterion = criteria[fatigue_analysis_data.effective_stress]
    if cpus is None:
        cpus = 1
    try:
        print("Evaluating criterion " + criterion.name + " at " + str(stress_history.shape[1]) + " positions")
        print("\tThis might take a while...")
        s = evaluate_effective_stress(stress_history, fatigue_analysis_data.material, criterion.evaluate, cpus,
                                      **heat_treatment_data)
    except ValueError as e:
        print("Problem when evaluating the criterion " + criterion.name)
        print("\t" + str(e))
        sys.exit()

    for output_step in fatigue_analysis_data.output_data:
        print("Writing data to the odb file " + str(output_step.odb_file_name))
        if not output_step.odb_file_name.is_file():
            abq.create_empty_odb_from_odb(new_odb_filename=output_step.odb_file_name,
                                          odb_to_copy=fatigue_analysis_data.static_stresses[0].odb_file_name)
        frame_number = output_step.frame_number
        output_odb_steps = abq.get_steps(output_step.odb_file_name)
        if frame_number != -1:
            if output_step.step_name in output_odb_steps:
                frames = abq.get_frames(output_step.odb_file_name, step_name=output_step.step_name)
            else:
                frames = []
            if len(frames):
                frame_number = frames[-1]
            else:
                frame_number = 0

        for i in range(s.shape[1]):
            try:
                abq.write_data_to_odb(s[:, i], criterion.variables[i], output_step.odb_file_name,
                                      step_name=output_step.step_name, instance_name=output_step.instance,
                                      frame_number=frame_number, set_name=output_step.element_set,
                                      field_description=criterion.field_descriptions[i])
            except OdbWritingError as e:
                print("Problem when writing the fatigue field " + criterion.variables[i] + " to the odb file "
                      + str(output_step.odb_file_name))
                print('\t', e)
    print("Done")
