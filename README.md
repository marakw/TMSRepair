# TMSRepair
Code for repairing artifacts in TMS-EEG data.
Available as PyPI package: "pip install TMSRepair"

<br> 

### General
Combining the method of Transcranial Magnetic Stimulation (TMS) with electroencephalographic (EEG) recordings leads to a severe distortion of the electrophyiological signal from sources other than the neural activity. Application of TMS induces an instant, large amplitude artifact in the EEG signal, which has to be removed prior to processing the data. Other distorting artifacts that originate directly or indirectly from stimulation are TMS-evoked muscle activity, eyeblinks, eye movement or electrode noise. These artifacts are inevitable during recording, but need to be removed prior to filtering and analyzing the data.

For more information about TMS-EEG processing, I refer the reader to: https://nigelrogasch.gitbook.io/tesa-user-manual/an_overview_of_tms-eeg_analysis

<br> 

### The Package
TMSRepair is an extension for the MNE toolbox (Gramfort et al., 2013) and works on 'epochs' instances.
It is inspired by the TESA toolbox for MATLAB (Rogasch et al., 2017; Mutanen et al., 2020).

The data is analysed with fast Independent Components Analysis (fast ICA). Components capturing eye blinks/eye movement, muscular artifacts or electrode noise can be detected and rejected automatically or manually, through thresholds or a User Interface, respectively.

It also provides a method for detecting and rejecting bad channels and interpolating the time window around the spiky TMS artifact with cubic interpolation.

<br> 


### References

Alexandre Gramfort, Martin Luessi, Eric Larson, Denis A. Engemann, Daniel Strohmeier, Christian Brodbeck, Roman Goj, Mainak Jas, Teon Brooks, Lauri Parkkonen, and Matti S. Hämäläinen. MEG and EEG data analysis with MNE-Python. Frontiers in Neuroscience, 7(267):1–13, 2013. doi:10.3389/fnins.2013.00267.

Rogasch NC, Sullivan C, Thomson RH, Rose NS, Bailey NW, Fitzgerald PB, Farzan F, Hernandez-Pavon JC. Analysing concurrent transcranial magnetic stimulation and electroencephalographic data: a review and introduction to the open-source TESA software. NeuroImage. 2017; 147:934-951.

Mutanen TP, Biabani M, Sarvas J, Ilmoniemi RJ, Rogasch NC. Source-based artifact-rejection techniques available in TESA, an open-source TMS-EEG toolbox. Brain Stimulation. 2020; In press.
