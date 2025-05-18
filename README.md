# Bleb Annotator Tool 🔨

This tool is used to annotate point location of blebs. 


## Installation 📦
Run the following command to install virutal environment:

`conda create --prefix ./venv -y python=3.9.19`

Activate the environment:

`conda activate ./venv`

Install Packages:

`pip install -r requirements.txt`


## Bleb Annotations 🩺

Annotation is handled in the tools with the help of `AnnotationConfiguration` class. The class holds a list of `BlebAnnotation` objects which stores the point indices, coordinates and the annotator name.


## Usage 🦮
To use the tool, the user have to re-structure the mesh objects in the directory. Say, we have a 'test.obj' file; to annotate it using the tool, create a directory [say, test], rename the object to 'mesh.obj' and move it in the folder.

It is important to structure it in the aforementioned way, as the tools saves annotation files in the same directory the mesh object is in.


## Handy-Features ✨

1. **Auto-save history**: whenever the user opens a mesh, the tool auto-saves the previous annotation configuration with timestamp.


## How to run the annotate? 📝

After successfully finisihing the instally, simply run the following command and get annotating:

`python main.py`

Here's a video guide of annotation process:

https://github.com/user-attachments/assets/9b8a7477-a0da-4a94-a2ec-1513bd27afc0

