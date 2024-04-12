from functools import partial
import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import enum

import scipy.spatial as ss
import numpy as np
import time
import copy
import _thread
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import *


from ApplicationMode import ApplicationMode
from AnnotationConfiguration import AnnotationConfiguration


class Radiologist(enum.Enum):
    DANIEL = 'danielbehme'
    ANASTASIOS = 'anastasios'


INPUT_MODEL = None
UPDATE = False
PICKED_POINT_INDEX = []
PICKED_POINT_ACTOR = []
APART_POINT_INDEX = []
PATH_POINT_INDEX = []
PICKED_PATH_ACTOR = []

KDTREE = None
POINTS = []

RED = (204, 10, 10)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

COLORS = vtk.vtkUnsignedCharArray()
COLORS.SetNumberOfComponents(3)
COLORS.SetName('colors')

PROPAGATION = None


class MouseInteractorPickingActor(vtk.vtkInteractorStyleTrackballCamera):
    __mode: ApplicationMode
    annotation_config: AnnotationConfiguration
    current_annotator: str

    def __init__(self, annotation_config, current_annotator):
        self.__mode = ApplicationMode.SHOW
        self.annotation_config = annotation_config
        self.current_annotator = current_annotator
        self.AddObserver("LeftButtonPressEvent", self.leftButtonPressEvent, 0)


    def picking(self,):
        self.GetInteractor().GetPicker().Pick(
            self.GetInteractor().GetEventPosition()[0],
            self.GetInteractor().GetEventPosition()[1],
            0,
            self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
        )

        distance, index = KDTREE.query(self.GetInteractor().GetPicker().GetPickPosition())

        if distance > 0.5:
            return None
        else:
            return index
    
    
    def set_mode_to_show(self):
        self.__mode = ApplicationMode.SHOW


    def set_mode_to_add(self):
        self.__mode = ApplicationMode.ADD


    def set_mode_to_delete(self):
        self.__mode = ApplicationMode.DELETE


    def get_sphere(
            self, 
            index: int, 
            point, 
            radius, 
            annotated_by, 
            color
        ):
        sphereSource = vtk.vtkSphereSource()
        sphereSource.SetCenter(point)
        sphereSource.SetRadius(radius)

        sphereMapper = vtk.vtkPolyDataMapper()
        sphereMapper.SetInputConnection(sphereSource.GetOutputPort())

        sphereActor = vtk.vtkActor()
        sphereActor.index = index
        sphereActor.SetMapper(sphereMapper)
        sphereActor.GetProperty().SetColor(color)
    
        return sphereActor

 
    def init_annotation_configuration(self):
        for annotation in self.annotation_config.get_annotations():

            point = POINTS[annotation.get_index()]

            if annotation.get_annotator_name() == Radiologist.ANASTASIOS.value:
                actor = self.get_sphere(
                    annotation.get_index(), 
                    point, 
                    0.3, 
                    annotation.get_annotator_name(), 
                    BLUE,
                )
            else:
                actor = self.get_sphere(
                    annotation.get_index(), 
                    point, 
                    0.3, 
                    annotation.get_annotator_name(), 
                    GREEN,
                )

            self.GetInteractor()\
            .GetRenderWindow()\
            .GetRenderers()\
            .GetFirstRenderer()\
            .AddActor(actor)


    def leftButtonPressEvent(self, obj, event):
        global PICKED_POINT_INDEX, POINTS

        index = self.picking()

        if self.__mode == ApplicationMode.SHOW:
            self.OnLeftButtonDown()
            return
        
        if index is None:
            self.OnLeftButtonDown()
            return
        
        if self.__mode == ApplicationMode.ADD:
            PICKED_POINT_INDEX.append(index)

            actor = self.get_sphere(index, POINTS[index], 0.3, self.current_annotator, BLUE)

            self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer().AddActor(actor)

            self.annotation_config.add_point(
                points=POINTS[index],
                annotated_by=self.current_annotator,
                index=index,
            )

        elif self.__mode == ApplicationMode.DELETE:
            picker = vtk.vtkPicker()
            click_pos = self.GetInteractor().GetEventPosition()
            renderer = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()

            picker.Pick(click_pos[0], click_pos[1], 0, renderer)

            actor = picker.GetActor()
                
            if actor and (actor.GetProperty().GetAmbientColor() == BLUE or actor.GetProperty().GetAmbientColor() == GREEN):
                renderer.RemoveActor(actor)

                self.annotation_config.remove_annotation_by_index(actor.index)

        else:
            raise NotImplementedError(f'mode {self.__mode.value} not implemented')
        
        self.OnLeftButtonDown()

        return
    

    def get_selected_actors(self,):
        actors = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer().GetActors()

        for actor in actors:
            point_color = actor.GetProperty().GetAmbientColor()
            if point_color == BLUE:
                print(f'actor: {POINTS[actor.index]}')


    def get_annotation_config(self,) -> AnnotationConfiguration:
        return self.annotation_config


class VTKWidget:
    mouse_actor: MouseInteractorPickingActor

    def __init__(self, 
            filename, 
            propagation, 
            annotation_configuration: AnnotationConfiguration,
            current_annotator: str,
        ):
        global INPUT_MODEL, PICKED_POINT_INDEX, POINTS, KDTREE, PROPAGATION

        PROPAGATION = propagation

        self.vtkWidget = QVTKRenderWindowInteractor()

        self.ren = vtk.vtkRenderer()
        self.ren.SetBackground(1, 1, 1)
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)

        iren = self.vtkWidget.GetRenderWindow().GetInteractor()

        if filename is not None and annotation_configuration is not None:
            INPUT_MODEL = vtk.vtkOBJReader()
            INPUT_MODEL.SetFileName(filename)
            INPUT_MODEL.Update()

            for i in range(INPUT_MODEL.GetOutput().GetNumberOfPoints()):
                COLORS.InsertNextTypedTuple(RED)

            INPUT_MODEL.GetOutput().GetPointData().SetScalars(COLORS)
            INPUT_MODEL.GetOutput().Modified()

            p = [0.0, 0.0, 0.0]
            for i in range(INPUT_MODEL.GetOutput().GetNumberOfPoints()):
                INPUT_MODEL.GetOutput().GetPoint(i, p)
                POINTS.append(tuple(p))

            KDTREE = ss.KDTree(POINTS)

            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(INPUT_MODEL.GetOutputPort())

            actor = vtk.vtkActor()
            actor.SetMapper(mapper)

            self.ren.AddActor(actor)

            def rendering_apart(obj, event):
                global UPDATE
                INPUT_MODEL.GetOutput().GetPointData().SetScalars(COLORS)
                INPUT_MODEL.GetOutput().Modified()
                
            self.ren.AddObserver('StartEvent', rendering_apart)

            self.mouse_actor = MouseInteractorPickingActor(
                annotation_configuration, current_annotator
            )
            self.mouse_actor.SetDefaultRenderer(self.ren)
            iren.SetInteractorStyle(self.mouse_actor)
            
            self.mouse_actor.init_annotation_configuration()

        iren.Initialize()
        iren.Start()


    def add(self):
        global PICKED_POINT_INDEX
        self.mouse_actor.set_mode_to_add()
    

    def show(self):
        self.mouse_actor.set_mode_to_show()
        self.mouse_actor.get_selected_actors()


    def delete(self):
        self.mouse_actor.set_mode_to_delete()

    def get_annotation_config(self,) -> AnnotationConfiguration:
        return self.mouse_actor.get_annotation_config()


    def init_data(self):
        global INPUT_MODEL, UPDATE, PICKED_POINT_INDEX, PICKED_POINT_ACTOR, APART_POINT_INDEX, PATH_POINT_INDEX
        global PICKED_PATH_ACTOR, KDTREE, POINTS, COLORS, PROPAGATION

        INPUT_MODEL = None
        UPDATE = False
        PICKED_POINT_INDEX.clear()
        PICKED_POINT_ACTOR.clear()
        APART_POINT_INDEX.clear()
        PATH_POINT_INDEX.clear()
        PICKED_PATH_ACTOR.clear()

        KDTREE = None
        POINTS.clear()

        COLORS = vtk.vtkUnsignedCharArray()
        COLORS.SetNumberOfComponents(3)
        COLORS.SetName('colors')

        PROPAGATION = None


class Propagation(QThread):

    def __init__(self):
        QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self) -> None:
        global PATH_POINT_INDEX, APART_POINT_INDEX, UPDATE

        picked_points = []
        for i in PATH_POINT_INDEX:
            for j in i:
                picked_points.append(j)


        for sp in APART_POINT_INDEX:

            nn_index = []

            cellidlist = vtk.vtkIdList()
            INPUT_MODEL.GetOutput().GetPointCells(sp, cellidlist)
            for i in range(cellidlist.GetNumberOfIds()):
                cell = INPUT_MODEL.GetOutput().GetCell(cellidlist.GetId(i))
                for e in range(cell.GetNumberOfEdges()):
                    edge = cell.GetEdge(e)
                    pointidlist = edge.GetPointIds()
                    if pointidlist.GetId(0) != sp and pointidlist.GetId(1) != sp:
                        nn_index.append(pointidlist.GetId(0))
                        nn_index.append(pointidlist.GetId(1))
                        break

            nn_index = {}.fromkeys(nn_index).keys()

            for p in nn_index:
                if_pushback = True

                for ep in APART_POINT_INDEX:
                    if p == ep:
                        if_pushback = False
                        break

                for pp in picked_points:
                    if p == pp:
                        if_pushback = False
                        break

                if if_pushback is True:
                    APART_POINT_INDEX.append(p)
                    print('append', len(APART_POINT_INDEX))

        UPDATE = True
        print('segmentation finished!')
