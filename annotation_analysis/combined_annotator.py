import enum
import typing
import math
import copy
import os

import glob
import shutil

from annotation_configuration import (
    BlebAnnotation,
    get_annotation_configuration, 
    AnnotationConfiguration
)


class Radiologist(enum.Enum):
    DANIEL = 'danielbehme'
    ANASTASIOS = 'anastasios'
    

def get_distance_between_two_bleb_annotations(
        bleb_annotation_1: BlebAnnotation, 
        bleb_annotation_2: BlebAnnotation,
    ):
    distance_squared_sum = 0

    for coord in zip(bleb_annotation_1.get_point(), bleb_annotation_2.get_point()):
        distance_squared_sum += (coord[0] - coord[1]) ** 2

    return math.sqrt(distance_squared_sum)


def is_annotation_config_similar(
        annotation_config_1: AnnotationConfiguration, 
        annotation_config_2: AnnotationConfiguration,
        threshold: float
    ) -> bool:

    if len(annotation_config_1.get_annotations()) != \
            len(annotation_config_2.get_annotations()):
        return False

    origin_bleb = BlebAnnotation(0, 0, 0, -1, None)


    bleb_annotations_1 = annotation_config_1.get_annotations()
    bleb_annotations_2 = annotation_config_2.get_annotations()

    bleb_annotations_1.sort(key=lambda x: get_distance_between_two_bleb_annotations(origin_bleb, x))
    bleb_annotations_2.sort(key=lambda x: get_distance_between_two_bleb_annotations(origin_bleb, x))


    for bleb_1, bleb_2 in zip(bleb_annotations_1, bleb_annotations_2):

        print(f'comparing: {bleb_1} {bleb_2} {get_distance_between_two_bleb_annotations(bleb_1, bleb_2)}')

        if get_distance_between_two_bleb_annotations(bleb_1, bleb_2) >= threshold:
            return False
        
    return True


def is_bleb_annotation_similar(
        bleb_annotation_1: BlebAnnotation,
        bleb_annotation_2: BlebAnnotation,
    ):

    distance_between_blebs = get_distance_between_two_bleb_annotations(
        bleb_annotation_1,
        bleb_annotation_2,
    )

    if distance_between_blebs < 1:
        return True
    
    return False


def get_folder_name(folder_path: str):
    return folder_path.split('/')[-1]


def get_all_annotation_names(root_path):
    all_mesh_paths = glob.glob(f'{root_path}/*/mesh.obj')

    all_mesh_folders = [i.replace('/mesh.obj', '') for i in all_mesh_paths]

    return [get_folder_name(i) for i in all_mesh_folders]


def make_dir_if_not_exist(dir_path: str):
    if os.path.isdir(dir_path) is False:
        os.mkdir(dir_path)


def condense_bleb_annotation(
        annotation_config: AnnotationConfiguration,
        distance_threshold: float,
        annotated_by: str, 
    ) -> AnnotationConfiguration:
    '''
        removes redundant bleb annotations.
    '''

    all_bleb_annotations: typing.List[BlebAnnotation] = annotation_config.get_annotations()
    combined_annotations: typing.List[BlebAnnotation] = []

    while len(all_bleb_annotations) != 0:

        bleb_annotation = all_bleb_annotations.pop(0)

        combined_annotations.append(bleb_annotation)

        all_bleb_annotations = [
            i for i in all_bleb_annotations 
            if get_distance_between_two_bleb_annotations(i, bleb_annotation) >= distance_threshold
        ]

    
    new_configuration = AnnotationConfiguration({}, annotation_config.get_file_name())
    
    for _temp in combined_annotations:
        new_configuration.add_point(
            points=_temp.get_point(), 
            annotated_by=annotated_by,
            index=_temp.get_index(),
        )

    return new_configuration


def combine_annotations(
        annotation_configs: typing.List[AnnotationConfiguration],
        file_name: str
    ) -> AnnotationConfiguration:


    temp = AnnotationConfiguration({}, file_name)

    for annotation in annotation_configs:
        for bleb_annotation in annotation.get_annotations():
            temp.add_point(
                bleb_annotation.get_point(), 
                bleb_annotation.get_annotator_name(), 
                bleb_annotation.get_index(),
            )

    return temp

def process(
        data_root_path: str,
        agreed_annotation_path: str,
        disagreed_annotation_path: str,
        all_annotations: typing.List[str],
        threshold: float,
    ):


    for annotation in all_annotations:
        mesh_path = f'{root_path}/radiologist_annotated_cada_vessel_dataset_anastasios/{annotation}/mesh.obj'

        radiologist_anastasios_annotation_path = f'{data_root_path}/radiologist_annotated_cada_vessel_dataset_anastasios/{annotation}/annotation.json'
        radiologist_daniel_annotation_path = f'{data_root_path}/radiologist_annotated_cada_vessel_dataset_daniel/{annotation}/annotation.json'

        anastasios_annotation = get_annotation_configuration(radiologist_anastasios_annotation_path)
        daniel_annotation = get_annotation_configuration(radiologist_daniel_annotation_path)

        condensed_daniel_config: AnnotationConfiguration = \
            condense_bleb_annotation(daniel_annotation, threshold, Radiologist.DANIEL.value)
        
        condensed_anastasios_config: AnnotationConfiguration = \
            condense_bleb_annotation(anastasios_annotation, threshold, Radiologist.ANASTASIOS.value)
        
        annotation_config_similar: bool = (
            condensed_anastasios_config, condensed_daniel_config, threshold
        )

        output_mesh_path = None
        combined_annotation_config: AnnotationConfiguration = combine_annotations(
            [condensed_anastasios_config, condensed_daniel_config], annotation,
        )

        if (is_annotation_config_similar(
                condensed_anastasios_config, condensed_daniel_config, 2
            ) is False
        ):
            
            output_disagreed_folder = os.path.join(disagreed_annotation_path, annotation)
            
            make_dir_if_not_exist(output_disagreed_folder)

            annotation_disagreed_output_path = os.path.join(output_disagreed_folder, 'annotation.json')
            combined_annotation_config.save_current_annotation_config(annotation_disagreed_output_path)
            
            output_mesh_path = f'{output_disagreed_folder}/mesh.obj'
        else:
            output_agreed_folder = os.path.join(agreed_annotation_path, annotation)
            make_dir_if_not_exist(output_agreed_folder)

            annotation_agreed_output_path = os.path.join(output_agreed_folder, 'annotation.json')
            combined_annotation_config.save_current_annotation_config(annotation_agreed_output_path)


            output_mesh_path = f'{output_agreed_folder}/mesh.obj'

        shutil.copyfile(mesh_path, output_mesh_path)


if __name__ == '__main__':

    root_path = '/Users/new_horizon/better-bleb-annotator'

    radiologist_anastasios = f'{root_path}/radiologist_annotated_cada_vessel_dataset_anastasios'
    radiologist_daniel = f'{root_path}/radiologist_annotated_cada_vessel_dataset_daniel'

    all_annotations = get_all_annotation_names(radiologist_anastasios)

    all_annotations.sort()

    assert len(all_annotations) == 110

    combined_annotation_path = '/Users/new_horizon/better-bleb-annotator/combined_annotation'

    agreed_annotation_path = f'{combined_annotation_path}/agreed_annotations'
    disagreed_annotation_path = f'{combined_annotation_path}/disagreed_annotations'

    threshold = 0.9

    process(
        data_root_path=root_path,
        agreed_annotation_path=agreed_annotation_path,
        disagreed_annotation_path=disagreed_annotation_path,
        all_annotations=all_annotations,
        threshold=threshold,
    )
    # vessel_name = 'A130_R_vessel'

    # radiologist_anastasios_annotation_path = f'{radiologist_anastasios}/{vessel_name}/annotation.json'
    # radiologist_daniel_annotation_path = f'{radiologist_daniel}/{vessel_name}/annotation.json'

    # print(f'{radiologist_daniel_annotation_path}')
    # print(f'{radiologist_anastasios_annotation_path}')

    # anastasios_annotations = get_annotation_configuration(radiologist_anastasios_annotation_path)
    # daniel_annotations = get_annotation_configuration(radiologist_daniel_annotation_path)


    # print(get_distance_between_two_bleb_annotations(
    #     anastasios_annotations.get_annotations()[0],
    #     daniel_annotations.get_annotations()[0],
    # ))
    # print(anastasios_annotations.get_annotations())

    # print(daniel_annotations.get_annotations())


    

