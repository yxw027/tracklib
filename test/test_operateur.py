#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

"""
import math
import matplotlib.pyplot as plt
import random
import unittest

from tracklib.core.GPSTime import GPSTime
import tracklib.algo.Analytics as algo
from tracklib.core.Operator import Operator
from tracklib.core.Kernel import GaussianKernel
import tracklib.algo.Interpolation as interpolation
from tracklib.io.FileReader import FileReader
import tracklib.core.Track as core_Track
import tracklib.algo.Segmentation as seg
import tracklib.algo.Synthetics as synth

class TestOperateurMethods(unittest.TestCase):
    
    def mafonct(self, track, af_name):
        
        for i in range(len(track.getAnalyticalFeature(af_name))):
            val = track.getObsAnalyticalFeature(af_name, i)
            if val == 0:
                track.setObsAnalyticalFeature(af_name, i, 1)
            else:
                track.setObsAnalyticalFeature(af_name, i, 0)

    def test_abs_curv1(self):
        GPSTime.setReadFormat("4Y-2M-2D 2h:2m:2s")
        chemin = 'data/trace1.dat'
        
        track = FileReader.readFromFile(chemin, 2, 3, -1, 4, separator=",", DateIni=-1, h=0, com="#", no_data_value=-999999, srid="ENUCoords")
        
        track.addAnalyticalFeature(algo.diffJourAnneeTrace)
        track.operate(Operator.INVERTER, "diffJourAnneeTrace", "rando_jour_neg")
        #track.segmentation(["rando_jour_neg"], "rando_jour", [-1])
        seg.segmentation(track, ["rando_jour_neg"], "rando_jour", [-1])
        self.mafonct(track, "rando_jour")
        
        TRACES = seg.split(track, "rando_jour")
        
        
        self.assertTrue(len(TRACES) == 4)
        
        if len(TRACES) > 0:
            trace = TRACES[1]
            # trace.summary()
            trace.compute_abscurv()
            
            trace.resample(3, interpolation.MODE_SPATIAL)
            Sigma = trace.compute_abscurv()
            trace.estimate_speed()
            Speed = trace.getAnalyticalFeature('speed')
            #print (Speed)
            print (trace.getListAnalyticalFeatures())
            
            # =============================================================================
            # ============================================================================
            #
            fig, ax1 = plt.subplots(figsize=(15, 3))
            #plt.plot(trace.getAnalyticalFeature("sigma"), trace.getAnalyticalFeature("speed2"), '-', color='gold')
            plt.plot(Sigma, Speed, '-', color='skyblue')
            plt.show()
        
    
    def x(t):
        return 10 * math.cos(4 * math.pi * t)*(1 + math.cos(3.5 * math.pi * t))
    def y(t):
        return t
    def prob():
        return random.random()-0.5
        
    def test_random(self):
        GPSTime.setReadFormat("4Y-2M-2D 2h:2m:2s")
        #track = core_Track.Track.generate(TestOperateurMethods.x, TestOperateurMethods.y)
        track = synth.generate(TestOperateurMethods.x, TestOperateurMethods.y)

        track.createAnalyticalFeature("a")

        track.operate(Operator.RANDOM, ("a","a"), TestOperateurMethods.prob, ("x_noised","y_noised"))
        track.operate(Operator.INTEGRATOR, ("x_noised","y_noised"))
        track.operate(Operator.SCALAR_MULTIPLIER, ("x_noised","y_noised"), 0.02)
        track.operate(Operator.ADDER, ("x_noised","y_noised"), ("x","y"))

        kernel = GaussianKernel(21)
        kernel.setFilterBoundary(True)

        track.operate(Operator.FILTER, ("x_noised", "y_noised"), kernel, ("x_filtered", "y_filtered"))

        plt.plot(track.getX(), track.getY(), 'k--')
        plt.plot(track.getAnalyticalFeature("x_noised"), track.getAnalyticalFeature("y_noised"), 'b-')
        plt.plot(track.getAnalyticalFeature("x_filtered"), track.getAnalyticalFeature("y_filtered"), 'r-')
        plt.show()    
        
        
    def x2(t):
        return 10*math.cos(2*math.pi*t)*(1+math.cos(2*math.pi*t))
    def y2(t):
        return 10*math.sin(2*math.pi*t)*(1+math.cos(2*math.pi*t))    

    def test_generate(self):
        GPSTime.setReadFormat("4Y-2M-2D 2h:2m:2s")
        #track = core_Track.Track.generate(TestOperateurMethods.x2, TestOperateurMethods.y2)
        track = synth.generate(TestOperateurMethods.x2, TestOperateurMethods.y2)
        
        track.createAnalyticalFeature("a")
        track.operate(Operator.RANDOM, "a", TestOperateurMethods.prob, "randx")
        track.operate(Operator.RANDOM, "a", TestOperateurMethods.prob, "randy")

        track.operate(Operator.INTEGRATOR, "randx", "randx")
        track.operate(Operator.INTEGRATOR, "randy", "randy")

        track.operate(Operator.SCALAR_MULTIPLIER, "randx", 0.5, "noisex")
        track.operate(Operator.SCALAR_MULTIPLIER, "randx", 0.5, "noisey")

        track.operate(Operator.ADDER, "x", "noisex", "x_noised")
        track.operate(Operator.ADDER, "y", "noisey", "y_noised")

        kernel = GaussianKernel(31)

        track.operate(Operator.FILTER, "x_noised", kernel, "x_filtered")
        track.operate(Operator.FILTER, "y_noised", kernel, "y_filtered")


        plt.plot(track.getAnalyticalFeature("x"), track.getAnalyticalFeature("y"), 'k--')
        plt.plot(track.getAnalyticalFeature("x_noised"), track.getAnalyticalFeature("y_noised"), 'b-')
        plt.plot(track.getAnalyticalFeature("x_filtered"), track.getAnalyticalFeature("y_filtered"), 'r-')

        plt.show()


    def test_import(self):
        
        # ----------------------------------------------
        # Trajectoire calculee par GPS (mode standard)
        # ----------------------------------------------
        path = "data/rawGps1Data.pos"
        track1 = FileReader.readFromFile(path, "RTKLIB")            # Lecture du fichier
        track1.toProjCoords(2154)                                   # Projection Lambert 93
        track1 = track1 > 400                                       # Suppression 400 derniers points

        # ----------------------------------------------
        # Trajectoire de reference IMU
        # ----------------------------------------------
        path = "data/imu_opk_Vincennes1909121306.txt"     
        track3 = FileReader.readFromFile(path, "IMU_STEREOPOLIS")   # Lecture du fichier
        track3 = track3 < 400                                       # Suppression 400 derniers points
        track3.incrementTime(0, 18)                                 # Ajout 18 secondes UTC -> GPS Time
        track3.translate(0, 0, 47.66)                               # Conversion altitude -> hauteur
        track3 = track3 // track1                                   # Synchronisation sur track1                              


        # ----------------------------------------------
        # Calcul RMSE dans chaque direction
        # ----------------------------------------------
        track1.createAnalyticalFeature("x2", track3.getX())
        track1.createAnalyticalFeature("y2", track3.getY())
        track1.createAnalyticalFeature("z2", track3.getZ())

        std_e = track1.operate(Operator.L2, "x", "x2")
        std_n = track1.operate(Operator.L2, "y", "y2")
        std_u = track1.operate(Operator.L2, "z", "z2")

        #print("E std = " + '{:5.3f}'.format(std_e) + " m")
        self.assertEqual('{:5.3f}'.format(std_e), '3.246')
        #print("N std = " + '{:5.3f}'.format(std_n) + " m")
        self.assertEqual('{:5.3f}'.format(std_n), '4.786')
        #print("U std = " + '{:5.3f}'.format(std_u) + " m")
        self.assertEqual('{:5.3f}'.format(std_u), '8.224')


        
if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(TestOperateurMethods("test_abs_curv1"))
    suite.addTest(TestOperateurMethods("test_random"))
    suite.addTest(TestOperateurMethods("test_generate"))
    suite.addTest(TestOperateurMethods("test_import"))
    runner = unittest.TextTestRunner()
    runner.run(suite)
    