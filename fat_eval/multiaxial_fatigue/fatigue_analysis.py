import itertools
import sys

import numpy as np

import multiprocesser

from fat_eval.multiaxial_fatigue.criteria import criteria
from fat_eval.multiaxial_fatigue.evaluation import evaluate_effective_stress
from abaqus_python_interface import ABQInterface, OdbWritingError
from fat_eval.utilities.steel_data import abaqus_fields


class StressFieldError(ValueError):
    pass


def perform_fatigue_analysis(fatigue_analysis_data, cpus=1):
    abq = ABQInterface(fatigue_analysis_data.abaqus)
    read_odb_jobs = []
    for read_job in itertools.chain(fatigue_analysis_data.cyclic_stresses, fatigue_analysis_data.static_stresses):
        kw_args = {
            "odb_file_name": read_job.odb_file_name,
            "field_id": "S",
            "step_name": read_job.step_name,
            "frame_number": int(read_job.frame_number),
            "set_name": read_job.element_set,
            "instance_name": read_job.instance,
            "coordinate_system": read_job.coordinate_system,
            "deform_system": read_job.deform_system
        }
        read_odb_jobs.append((abq.read_data_from_odb, [], kw_args))

    heat_treatment = fatigue_analysis_data.heat_treatment
    for heat_treatment_field in abaqus_fields:
        kw_args = {
            "odb_file_name": heat_treatment.odb_file_name,
            "field_id": heat_treatment_field,
            "step_name": heat_treatment.step_name,
            "frame_number": heat_treatment.frame_number,
            "set_name": heat_treatment.element_set,
            "instance_name": heat_treatment.instance
        }
        read_odb_jobs.append((abq.read_data_from_odb, [], kw_args))
    print("Reading " + str(len(read_odb_jobs)) + " fields from odb files using " + str(min(len(read_odb_jobs), cpus))
          + " cpus")
    odb_fields = multiprocesser.multi_processer(read_odb_jobs, cpus=cpus, timeout=1e9, delay=0.)

    stress_history = None
    for i, cyclic_stress in enumerate(fatigue_analysis_data.cyclic_stresses):
        stress = odb_fields[i]*cyclic_stress.factor
        if stress_history is None:
            points, components = stress.shape
            stress_history = np.zeros((len(fatigue_analysis_data.cyclic_stresses), points, components))
        if stress.shape != stress_history[i, :, :].shape:
            raise StressFieldError("The stress in *cyclic_stress " + str(i + 1) + " has wrong shape")

        stress_history[i, :, :] = stress

    for k, static_stress in enumerate(fatigue_analysis_data.static_stresses):
        stress = odb_fields[k + len(fatigue_analysis_data.cyclic_stresses)]*static_stress.factor
        for i in range(len(fatigue_analysis_data.cyclic_stresses)):
            try:
                stress_history[i, :, :] += stress
            except ValueError:
                raise StressFieldError("Problems when adding the stress field in *static_stress " + str(k + 1)
                                       + " to the stress history")
    heat_treatment = fatigue_analysis_data.heat_treatment
    heat_treatment_data = {}
    for i, heat_treatment_field in enumerate(abaqus_fields):
        field = odb_fields[i + len(fatigue_analysis_data.cyclic_stresses) + len(fatigue_analysis_data.static_stresses)]
        if field.shape[0] != stress_history.shape[1]:
            raise StressFieldError("The field " + heat_treatment_field + "  in " + str(heat_treatment.odb_file_name)
                                   + " has a different shape than the stress field")
        heat_treatment_data[heat_treatment_field] = field
    criterion = criteria[fatigue_analysis_data.effective_stress]

    if cpus is None:
        cpus = 1
    try:
        print("Evaluating criterion " + criterion.name + " at " + str(stress_history.shape[1]) + " positions using "
              + str(cpus) + " cpus")
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
