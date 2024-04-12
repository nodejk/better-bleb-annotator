import typing
import os
import enum


from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import viewer_2 as viewer
from AnnotationConfiguration import AnnotationConfiguration, get_annotation_configuration
from ApplicationMode import ApplicationMode


class MainWindow(QMainWindow):
    
    annotator_name: typing.Optional[str]
    mode: ApplicationMode
    annotation_configuration: typing.Optional[AnnotationConfiguration]

    open_button: QPushButton
    add_annotation_button: QPushButton
    delete_annotation_button: QPushButton
    done_button: QPushButton
    save_button: QPushButton
    annotation_file_name: QLabel

    def __init__(self):
        super(MainWindow, self).__init__()

        self.mode = ApplicationMode.SHOW
        self.annotation_configuration = None

        self.get_annotator_name()
        self.set_window()

        self.propagation = viewer.Propagation()

        self.input_folder = None
        self.tools = self.init_tools()
        self.viewer = viewer.VTKWidget(
            self.input_folder, 
            self.propagation, 
            None,
            self.annotator_name,
        )

        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.tools)
        self.main_layout.addWidget(self.viewer.vtkWidget)

        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(self.main_layout)

        self.show()


    def get_annotator_name(self):
        name, ok = QInputDialog.getText(self, 'alert!', 'enter your name to annotate the data')

        while name == '':
            name, ok = QInputDialog.getText(self, 'alert!', 'enter your name to annotate the data')

        self.annotator_name = name


    def set_window(self):
        self.setWindowTitle('Bleb Annotator')
        self.resize(1000, 800)
        self.move(int((QDesktopWidget().width() - self.width()) / 2),
                  int((QDesktopWidget().height() - self.height()) / 2))
    

    def init_tools(self):

        self.annotation_file_name = QLabel(f'Currently opened: {None}')
        self.annotation_file_name.show()

        self.open_button = QPushButton('open folder')
        self.open_button.clicked.connect(self.open_mesh_folder)
        
        self.add_annotation_button = QPushButton('add annotation')
        self.add_annotation_button.clicked.connect(self.add_annotation)
        self.add_annotation_button.setEnabled(False)

        self.delete_annotation_button = QPushButton('delete annotation')
        self.delete_annotation_button.clicked.connect(self.delete_annotation)
        self.delete_annotation_button.setEnabled(False)

        self.done_button = QPushButton('done')
        self.done_button.clicked.connect(self.done)
        self.done_button.setEnabled(False)

        self.save_button = QPushButton('save')
        self.save_button.clicked.connect(self.save)
        self.save_button.setEnabled(False)

        tools_out = QWidget()
        layout_out = QVBoxLayout()

        tools = QWidget()
        layout = QHBoxLayout()
        
        layout.addWidget(self.open_button)
        layout.addWidget(self.add_annotation_button)
        layout.addWidget(self.delete_annotation_button)
        layout.addWidget(self.done_button)
        layout.addWidget(self.save_button)

        tools.setLayout(layout)

        layout_out.addWidget(self.annotation_file_name)
        layout_out.addWidget(tools)
        
        tools_out.setLayout(layout_out)

        return tools_out


    def save(self,):
        annotation_config = self.viewer.get_annotation_config()
        annotation_config.save_config(self.input_folder)

        dialog = QMessageBox(self)

        dialog.setWindowTitle('alert!')
        dialog.setText(f'annotation saved to {self.input_folder}')

        dialog.exec_()


    def add_annotation(self,):
        self.mode = ApplicationMode.ADD

        self.open_button.setEnabled(False)
        self.add_annotation_button.setEnabled(False)
        self.delete_annotation_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.done_button.setEnabled(True)

        self.viewer.add()


    def delete_annotation(self,):
        self.mode = ApplicationMode.DELETE

        self.open_button.setEnabled(False)
        self.add_annotation_button.setEnabled(False)
        self.delete_annotation_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.done_button.setEnabled(True)

        self.viewer.delete()
    
    def done(self,):
        self.mode = ApplicationMode.SHOW

        self.open_button.setEnabled(True)
        self.add_annotation_button.setEnabled(True)
        self.delete_annotation_button.setEnabled(True)
        self.save_button.setEnabled(True)

        self.done_button.setEnabled(False)

        self.viewer.show()


    def open_mesh_folder(self):

        input_folder = QFileDialog.getExistingDirectory(self)

        if input_folder != '':
            self.viewer.init_data()
            self.input_folder = input_folder
            mesh_path, annotation_config_path = self.get_input_paths(input_folder)

            valid: bool = self.check_if_folder_valid()

            if valid == False:
                return
            
            self.annotation_configuration = get_annotation_configuration(
                annotation_config_path, self.get_mesh_name(input_folder)
            )

            self.annotation_file_name.setText(f'Currently opened: {self.get_mesh_name(input_folder)}')

            self.main_layout.removeWidget(self.viewer.vtkWidget)

            self.annotation_configuration.save_current_annotation_config(self.input_folder)
            
            self.viewer = viewer.VTKWidget(
                mesh_path, 
                self.propagation, 
                self.annotation_configuration,
                self.annotator_name,
            )
            self.main_layout.addWidget(self.viewer.vtkWidget)

            self.add_annotation_button.setEnabled(True)
            self.delete_annotation_button.setEnabled(True)


    @staticmethod
    def get_input_paths(path: str):
        mesh_path = f'{path}/mesh.obj'
        annotation_configuration_path = f'{path}/annotation.json'

        if os.path.isfile(annotation_configuration_path):
            return mesh_path, annotation_configuration_path
        
        return mesh_path, None
    

    @staticmethod
    def get_mesh_name(folder_path: str):
        return folder_path.split('/')[-1]


    def check_if_folder_valid(self, ):
        mesh_path, _ = MainWindow.get_input_paths(self.input_folder)

        if os.path.isfile(mesh_path) == False:
            message_box = QMessageBox(self)
            
            message_box.setWindowTitle('alert')
            message_box.setText(f'the folder is not valid. {mesh_path} does not have mesh.obj')

            message_box.exec_()

            return False
        return True
