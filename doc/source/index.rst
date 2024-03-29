:Author: Marie-Dominique Van Damme
:Version: 1.0
:License: --
:Date: 07/03/2021


Welcome to TrackLib’s documentation!
=======================================

*tracklib library provide a variety of tools, operators and functions to manipulate GPS trajectories.*

:Source Code: https://github.com/umrlastig/tracklib

|travis| |codecov| |rtd| 

.. |travis| image:: https://travis-ci.org/umrlastig/tracklib.svg?branch=main
                  :alt: Travis build status
                  :target: https://travis-ci.org/github/umrlastig/tracklib
.. |codecov| image:: https://codecov.io/gh/umrlastig/tracklib/branch/main/graph/badge.svg
                   :alt: Code coverage
                   :target: https://app.codecov.io/gh/umrlastig/tracklib
.. |rtd| image:: https://readthedocs.org/projects/tracklib/badge/?version=latest
               :alt: Documentation status
               :target: https://tracklib.readthedocs.io/en/latest/?badge=latest



Background
**************

More and more datasets of GPS trajectories are now available and they are studied very frequently in many scientific domains. 
Python libraries for trajectories are available to load, simplify, interpolate, summarize and visualize them. 
But there is no Python library that would contain all these basic functionality.  

Furthermore, adding analytical features on a observation or on all observation of a trajectory (function of coordinates or timestamp) 
is, in general, a complex and a boring task. So, to make it easier, *Tracklib* module offers a multitude of operators 
and functions to simplify the creation of analytical features on a GPS traces. 


Among tracklib main functionalities
*************************************

* Structured data to store GPS data
* Load GPS data from files (GPS, CSV) or from databse
* Operation classes for manipulating track
* Propose generic method to simplify a track. For example (Douglas Peucker, Visvalingram algorithms or kernel Filter (Gaussian, Uniform, Dirac, etc.)).

    .. figure:: ./img/generate_random.png
	   :width: 450px
	   :align: center
	   
	   Figure 1 : Simplify with a gaussian filter

* Resample, interpolation and smoothing functions

	.. figure:: ./img/smooth.gif
	   :width: 450px
	   :align: center

       Figure 2 : Resample with MODE_SPLINE_SPATIAL
	   
	   
* Ploting speed profil

	.. figure:: ./img/Profil_vitesse_spatial_1.png
	   :width: 550px
	   :align: center

* Summarize GPS information into a grid

 	.. figure:: ./img/grille_avg_speed.png
	   :width: 550px
	   :align: center
  

Examples
**********

* See quick start for a first example
* Further examples of *tracklib* use-cases can be found in the *example* folder: SpeedProfil.py, Interpolation.py, LoadFromDatabase.py




.. toctree::
   :maxdepth: 1
   :caption: Tutorials

   install
   quickstart
   convention
   
.. toctree::
   :maxdepth: 1
   :caption: User Guide

   loading
   coreconcept
   operator
   mapmatching
   simplify
   summarize
..   interpolation





.. TODO :

.. * Documentation interne

.. Qu'est-ce que j'ai comme fonction pour lire une trace ?

.. > u.search("read")

.. -----------------------------------------------------
.. TRACKLIB FUNCTIONS: 11
.. -----------------------------------------------------
.. GPSTime getReadFormat
.. GPSTime readTimestamp
.. GPSTime readUnixTime
.. GPSTime setReadFormat
.. Track readFromCSV
.. Track readFromDataBase
.. Track readFromGpx
.. FileReader readFromFile
.. FileReader readFromFiles
.. PostgresReader readFromDataBase
.. GpxReader readFromGpx
.. -----------------------------------------------------

.. Ok très bien. La fonction readFromCSV a l'air de correspondre à ce que je cherche. Comment elle fonctionne ?

.. > u.help(Track.estimate_speed)


.. -----------------------------------------------------
.. FUNCTION: estimate_speed
.. -----------------------------------------------------
.. Description: blablabla
.. Input(s):
..     -...
.. Output(s):
..     -...
.. Warning: blablabla
.. -----------------------------------------------------


.. .. figure:: ./img/Profil_vitesse_temporel_1.png
..    :width: 550px
..    :align: center
   
   


