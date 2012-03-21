#!/usr/bin/env python
# -*- coding: UTF8 -*-
#
#   lithography_preprocessor.py - preprocess a PNG image for 2-photon 
#     lithography 
#
#     this program allows the user to choose a png image to be written, define
#     the wafer rotation and origin, and output a series of coordinates to be
#     exposed.
#
#   AUTHOR: Douglas Watson <douglas@watsons.ch>
#
#   DATE: started on 21 March 2012
#
#   LICENSE: GNU GPL
#
#################################################

'''
lithography_preprocessor.py
---------------------------

This little piece of software is designed to process png images into position
instructions for the Loncar lab's home-made two-photon lithography machine.

Briefly, the input is a black-and-white png image (and user-defined
dimensions), and the output are locations of pixels to expose. The software
performs two functions. The first is to import a PNG picture and convert it
into a 2D array of true-false values (true being 'expose', false being 'do not
expose'). The second is to assign, for each of these pixels, a spatial
position, in the coordinate system of the stage, and from there output the 3D
coordinates of each point to be exposed.

The interface is built using Traits UI. Most of this file is dedicated to
defining the interface. The actual operations on pictures are found in
png_toolkit.py (for importing and conversion of pictures) and XXX.

'''

__title__ = 'Lithography preprocessor'
__version__ = '0.1 alpha'

from mpl_figure_editor import MPLFigureEditor, Figure
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm

from enthought.traits.api import HasTraits, Float, Instance, Button, String, \
        File, Trait
from enthought.traits.ui.api import View, Item, Group, HGroup, Spring, HSplit, \
        Label
import enthought.traits.ui

##############################
# Helpers 
##############################

# My own librairies
from png_toolkit import path_to_array

def nonzero_validator(object, name, value):
    ''' Verify that value is non-zero. '''

    # Coerce to float:
    value = float(value)

    if value == 0:
        print "bleh"
        raise ValueError("%s cannot be zero" % name)
    else:
        return float(value)

##############################
# Classes 
##############################

class Preview2D(HasTraits):
    
    '''
    A matplotlib plot. Used both for the 2D and 3D plots.

    '''

    figure = Instance(Figure, ())

    traits_view = View(Item('figure', editor=MPLFigureEditor(),
                            width=400,
                            height=300,
                            show_label=False),
                        resizable=True,
                        )

    def __init__(self):
        super(Preview2D, self).__init__()

        self.ax = self.figure.add_subplot(111)
        self.ax.set_aspect('equal')
        self.ax.hold(False)

    def plot_array(self, array, length, width):
        ''' Draw the array, with appropriately scaled axes '''

        lx = length/2
        ly = width/2
        self.ax.imshow(array, cmap=cm.gray, interpolation='nearest',
                      extent=[-lx, lx, -ly, ly])
        self.figure.canvas.draw()

class Preview3D(Preview2D):

    '''
    A 3D matplotlib plot
    '''

    def __init__(self):
        super(Preview3D, self).__init__()

        self.ax = self.figure.add_subplot(111, projection='3d')

class ImageConfig(HasTraits):
    '''
    Defines the image to be written, and extra information (size).

    '''

    path = File('/home/douglas/research/lno/lithography/' +
                  'raster_lithography/220px-Tux.png')
    preview = Instance(Preview2D)
    width = Trait(10, nonzero_validator)  # in um
    height = Trait(10, nonzero_validator) # in um
    update = Button

    traits_view = View(
                Group(Item(name='path'),
                      Item(name='width', label='Width [um]'),
                      Item(name='height', label='Height [um]'),
                      Item(name='update', show_label=False, springy=False),
                      label='Picture configuration',
                      show_border=True,
                     )
                    )

    def _update_fired(self):
        ''' Update the 2D image preview. 
        
        This functions reads in the picture and plots the preview '''

        data = path_to_array(self.path)
        self.preview.plot_array(data, self.width, self.height)

class Referential(HasTraits):
    ''' 
    Defines three points of the wafer plane in the referential of the stage.

    These are used to calculate the orientation of the wafer, relative to the
    stage, and use that to establish a 'wafer coordinate system', to convert
    points on the wafer plane to points in the space of the stage.

    '''

    Ox = Float
    Oy = Float
    Oz = Float

    Ax = Float(1.0)
    Ay = Float
    Az = Float

    Bx = Float
    By = Float(1.0)
    Bz = Float

    recalculate = Button

    traits_view = View(
                Group(Item(name='Ox'),
                      Item(name='Ax'),
                      Item(name='Bx'),
                      Item(name='Oy'),
                      Item(name='Ay'),
                      Item(name='By'),
                      Item(name='Oz'),
                      Item(name='Az'),
                      Item(name='Bz'),
                      Spring(),
                      Spring(),
                      Item(name='recalculate', show_label=False),
                      label='Wafer reference points [um]',
                      show_border=True,
                      orientation='vertical',
                      columns=3)
                )

class MainWindow(HasTraits):
    '''
    Contains all the components of the interface:
        - A column of config (picture file and size, referential settings)
        - A 2D preview of the image to draw, in the referential of the wafer
        - A 3D preview of the points to expose, in the ref. of the stage
        - An export button, to export the coordinates of the points to expose

    '''

    image_config = Instance(ImageConfig)
    stage_config = Instance(Referential)
    preview2D = Instance(Preview2D)
    preview3D = Instance(Preview3D)
    export_data = Button

    traits_view = View(
        HSplit(
            Group(
                Item('image_config', style='custom', show_label=False,
                     springy=True),
                Item('stage_config', style='custom', show_label=False,
                    springy=True),
                Item('export_data', show_label=False, springy=False)
            ),
            Item('preview2D', style='custom', show_label=False),
            Item('preview3D', style='custom', show_label=False),
        ),
        resizable=True,
        title="%s v. %s" % (__title__, __version__),
    )

##############################
# Main program 
##############################

if __name__ == '__main__':

    # Create objects saved between several components
    preview2D = Preview2D()
    preview3D = Preview3D()
    image_config = ImageConfig(preview=preview2D)

    mainwindow = MainWindow(image_config=image_config, 
                            stage_config=Referential(),
                            preview2D=preview2D, 
                            preview3D=preview3D
                           )

    mainwindow.configure_traits()