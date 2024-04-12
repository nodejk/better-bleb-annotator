import typing
import json
import os


class BlebAnnotation:
    __x: float
    __y: float
    __z: float

    __index: int

    __annotated_by: str

    def __init__(self, x, y, z, index, annotated_by):
        self.__x = x
        self.__y = y
        self.__z = z

        self.__index = index

        self.__annotated_by = annotated_by


    def get_point(self,) -> typing.Tuple[float, float, float]:
        return (self.__x, self.__y, self.__z)
    

    def get_index(self,) -> int:
        return self.__index
    

    def set_annotator_name(self, annotator_name: str) -> None:
        self.__annotated_by = annotator_name
    

    def get_annotator_name(self, ) -> str:
        return self.__annotated_by
    
    def __str__(self) -> str:
        return f'index: {self.__index} ({self.__x}, {self.__y}, {self.__z} annotated_by: {self.__annotated_by})'

    def __dict__(self,) -> dict:
        return {
            'x': self.__x,
            'y': self.__y,
            'z': self.__z,
            'index': self.__index,
            'annotated_by': self.__annotated_by,
        }
    

class AnnotationConfiguration:
    __annotations: typing.Dict[str, BlebAnnotation]
    __file_name: str

    def __init__(self, 
        annotations: typing.Dict[str, BlebAnnotation], 
        file_name: str,
    ):
        
        self.__annotations = {}
        for key, val in annotations.items():
            self.__annotations[key] = BlebAnnotation(**val)
        self.__file_name = file_name


    def add_point(
        self, 
        points: typing.Tuple[float, float, float], 
        annotated_by: str,
        index: int,
    ):
        _temp = BlebAnnotation(
            x=points[0],
            y=points[1],
            z=points[2],
            index=int(index),
            annotated_by=annotated_by,
        )
        self.__annotations[str(index)] = _temp


    def get_file_name(self,) -> str:
        return self.__file_name
    

    def get_annotations(self,) -> typing.List[BlebAnnotation]:
        temp: typing.List[BlebAnnotation] = []

        for _, val in self.__annotations.items():
            temp.append(val)

        return temp
    
    def save_current_annotation_config(self, output_path):
        temp = {}

        for key, val in self.__annotations.items():
            temp[key] = val.__dict__()

        config = {
            'file_name': self.__file_name,
            'annotations': temp,
        }

        output_file_path = os.path.normpath(output_path)

        with open(output_file_path, 'w', encoding='utf-8') as file:
            json.dump(config, file, ensure_ascii=False, indent=4)


    def print(self,):
        for key, val in self.__annotations.items():
            print(val)

def get_annotation_configuration(
        json_path: typing.Optional[str], 
    ) -> AnnotationConfiguration:
    
    try:
        with open(json_path, 'r') as file:
            output = json.load(file)            
            return AnnotationConfiguration(**output)
    except Exception:
        raise Exception(f'file: {file} not found')
