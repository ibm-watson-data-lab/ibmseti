2.0.1 (unreleased)
==================

2.0.0 (2018-03-23)
==================

- Released after testing

2.0.0.dev5 (2017-08-24)
==================

- [NEW] Support for Python 3. Tested to work with Python 2.7 and Python 3.6.
- [NEW] Uses six package to handle data input SimCompamp 

2.0.0.dev1 (2017-08-23)
==================

- [NEW] Support for Python 3. Tested to work with Python 2.7 and Python 3.6. 

1.0.5  (2017-06-21)
==================
- [NEW] Adding ibmseti.compamp.SimCompamp.sigProc function for inserting signal processing function before spectrogram calculations.

1.0.4 
==================

- [UPDATE] Automatically subtract any DC offset in Simulation data (compamp.SimCompamp)

1.0.3
==================
- [UPDATE] Changes default size of SimCompamp to 32 x 6144.

1.0.2 
==================
- [UPDATE] Moves SimCompamp class into compamp module instead of having separate file. :p

1.0.1
==================
- [NEW] Supports reading simulated data files prepared for the SETI Institute hackathon and code challenge, 2017.

1.0.0 (2017-03-21)
==================
- [NEW] Removes signaldb module, which wasn't so useful. Also makes the package independent of pyspark. 

0.0.8 (2016-11-07)
==================

- [NEW] Breaks out methods to compute signal in fourier space and to create a single 1D time-domain signal with over-sampled frequencies removed.

0.0.7 (2016-11-07)
==================

- [UPDATE] Compamp.complex_data returns a Numpy array of type complex64, reducing memory usage
- [NEW] Automatically imports ibmseti.constants (bins_per_half_frame is needed for DIY data manipulation)

0.0.6 (2016-10-19)
==================

- [NEW] Removes callback to track usage.

0.0.5 and earlier
===================
Changes were not tracked.