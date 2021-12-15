import TMSRepair.TMSRepair_misc as misc
import TMSRepair.TMSRepair_UIs as UIs

import numpy as np
import matplotlib
import mne

from copy import copy
from sklearn.decomposition import FastICA
from scipy.stats import zscore




class TMSepochs:
    """
    Class for repairing TMS evoked artifacts in 
    mne epochs objects based on fast ICA.


    Attributes
    ----------
    epochs : mne epochs object
        data to be repaired in mne format
    options : dict
        dictionary with the settings for the ICA. 
    rank : int
        rank of the matrix that the ICA is performed on
    orig_backend : string
        original backend at the timepoint the object is initialized. 
        The backend needs to be changed to 'Agg' for tkinter 
        and later be reset.
    S : numpy array
        ICA components time courses
    A : numpy array
        mixing matrix
    badcomp : list
        the components that were chosen to be rejected
    compclass : list
        list of length (n° components) with values ranging from 0-6 
        indicating the class of the component
    fftbins : numpy array
        spectral information of each component
    mean : numpy array
        mean for each channel that was subtracted from the data for whitening it prior to ICA, 
        that needs to be added after the inverse transform  
    perc_var : array
        percent of amplitude variance relative to other components over time 
        for each component
    post : numpy array
        data after the inverse transform, stored separately
        in order not to replace it in the epochs object right away
    transformed : bool
        whether the data in the epochs object has already been transformed 
        and the matrix rank adjusted to the component rejection


    Methods
    ----------
    mark_bad_channels:
        interactive rejection of bad channels specifically for analyzing event-related potentials.
        plots channel variance and the event related potentials 
        averaged across epochs for bad channel marking.
    replace_with_zeros(window : list):
        removes the data in each epoch 
        in the specified window [ms, e.g. [-5, 15]] and replaces it with zeros
    cubic_interpolation(window : list):
        interpolates the data in each epoch 
        in the specified window with first degree cubic interpolation
    fastica:
        performs fast ICA and sorts components after their variance over time
    compselect:
        component classification based on thresholds and/or visual inspection
    inverse_transform:
        application of the inverse transform, rejection of artifactual components,
        optionally visual check. 
        Result is saved in self.post (data in epochs not changed)
    transform_epochs_object:
        replace epochs._data with the transformed data
    reset_orig_backend:
        reset the matplotlib backend after setting it to 'Agg' for tkinter
    fit_select_transform:
        wrapper method calling the methods: fastica(), compselect(), 
        inverse_transform(), transform_epochs_object(),
        reset_orig_backend()

    """

    # define default options
    options = { 'manualinput':'on',
                'confirm':'on',
                'threshfeedback': 'on',
                'chanpicks':[],
                'compcheck':'on',
                'remove':'on', 
                'comps': -1, 
                'figsize': 'medium', 
                'plottimex': [-200, 300], 
                'plotfreqx': [1,100],
                'freqscale': 'log',
                
                'tmsmuscle': 'on',
                'tmsmusclethresh': 8,
                'tmsmusclewin': [11,30],

                'approach': 'parallel', 
                'g': 'logcosh', 

                'blink':'on', 
                'blinkthresh':2.5, 
                'blinkelecs':['Fp1', 'Fp2'], 

                'move':'on', 
                'movethresh':2, 
                'moveelecs':['F7', 'F8'],

                'muscle':'on', 
                'musclethresh':-0.31, 
                'musclefreqin':[],
                'musclefreqex':[48, 52],
                
                'elecnoise':'on',
                'elecnoisethresh':2}




    def __init__(self, epochs, options=None):

        self.epochs = epochs
        self.options['chanpicks'] = [self.epochs.ch_names[i] for i in self.epochs.picks]
        self.orig_backend = matplotlib.get_backend()

        # overwrite default options with user choices and check them
        if options is not None:
            self.set_options(options)
        else:
            self.set_options({})




    def set_options(self, options):

        self.options = misc.eval_param(self.options, options)  

        # if manual input desired open UI
        if self.options['manualinput'] == 'on':
            self.options = UIs.ui_input(self.options)

        # check if parameters are valid
        misc.check_param(self)



    def replace_with_zeros(self, win:list):
        
        # convert window to indices in epochs, +1 to include last timepoint
        idx1 = np.argmin(np.abs(self.epochs.times - win[0]*0.001))
        idx2 = np.argmin(np.abs(self.epochs.times - win[1]*0.001)) +1

        # set values in specified window to 0
        self.epochs._data[:, :, idx1:idx2] = 0




    def cubic_interpolation(self, win:list):

        self.epochs = misc.cubic_interpolation(self.epochs, win)




    def mark_bad_channels(self):
            
        # plotting of channel variance
        vars = np.var(self.epochs._data.T, axis=(0,2))
        badchans = misc.chan_visual_inspection(vars)

        # filtering and plotting of epochs data with marked bad channels
        # bandpass and bandstop filter data first
        epochs = copy(self.epochs)
       
        # mark the channels with high variance
        epochs.info['bads'] = [epochs.info['ch_names'][i] for i in list(badchans)]

        # interpolate, bandpass and bandstop filter data
        # this is done only on the copied epochs object within the scope of this function, 
        # only for visualization and noisy channel detection!
        epochs = misc.cubic_interpolation(epochs, [-5, 15])
        epochs.filter(0.5, 49, method='iir', verbose=0)
        epochs._data = mne.filter.notch_filter( epochs._data, epochs.info['sfreq'], 50, notch_widths=2, 
                                                phase='zero', verbose=0)

        # create a fake raw object out of the evoked object, 
        # to see which channels distort the ERP and be able to mark them
        evoked = epochs.average()
        fake_raw = misc.MNE_raw_format( evoked._data.T, 
                                        epochs.info['ch_names'], 
                                        epochs.info['sfreq'])

        fake_raw.info['bads'] = epochs.info['bads']

        fake_raw.plot(  n_channels=len(epochs.info['ch_names']), scalings='auto', 
                        title='EEG data - Choose bad channels manually', 
                        show=True,
                        bad_color='r',
                        block=True)

        # take bad channels out of the channel picks
        self.options['chanpicks'] = [   chan for chan in self.options['chanpicks'] 
                                        if chan not in fake_raw.info['bads']]

        self.epochs.info['bads'] = fake_raw.info['bads']


        print('Number of rejected channels: {}'.format(len(fake_raw.info['bads'])))




    def fastica(self):

        ch_idx = [ i for i, chan in enumerate(self.epochs.ch_names) 
                        if chan in self.options['chanpicks']]

        # reconcatenate epochs
        nevents, nchans, npnts = np.shape(self.epochs._data[:, ch_idx, :])
        data_concat = np.reshape(np.moveaxis(self.epochs._data[:, ch_idx, :], 0, 2), [nchans, -1])

        print('\nPerforming fast ICA on data using {} approach.'
                .format(self.options['approach']))

        # check whether matrix is full rank, or adjust the number of components
        # otherwise fast ICA may fail to converge because it is searching for more ICs 
        # than there are in the data
        self.rank = np.linalg.matrix_rank(data_concat)

        if self.rank < self.options['comps']:
            print('The matrix rank is {}. '. format(self.rank))
            print('Number of components adjusted accordingly.')
            self.options['comps'] = self.rank


        # run FastICA and reshape component time courses
        ica = FastICA(  n_components=self.rank, 
                        algorithm=self.options['approach'], 
                        fun=self.options['g'], 
                        max_iter=1000)

        ica = ica.fit(data_concat.T)
        icasig = ica.transform(data_concat.T)

        self.S = np.reshape(icasig.T, [-1, npnts, nevents]) # component 3d time courses
        self.A = ica.mixing_ # topographies
        self.mean = ica.mean_ # mean for the inverse transform of the whitened data

        # get variance of each component in percent relative to all components as mean over epochs
        vars = np.var(np.mean(self.S, 2), axis=1)
        self.perc_var =  vars/sum(vars)*100

        # sort components in descending order based on variance
        ixsSort = np.flip(np.argsort(self.perc_var))

        self.perc_var = self.perc_var[ixsSort]
        self.A = self.A[:, ixsSort]
        self.S = self.S[ixsSort, :,:]

        print('\nICA weights sorted by time course variance.')




    def compselect(self):

        # create zscore for each component across channels
        tempCompZ = zscore(self.A, 0)

        # tms muscle window
        if self.options['tmsmuscle'] == 'on':
            mt1 = np.argmin(np.abs(self.epochs.times*1000 - self.options['tmsmusclewin'][0]))
            mt2 = np.argmin(np.abs(self.epochs.times*1000 - self.options['tmsmusclewin'][1]))

            muscleScore = np.abs(np.mean(self.S, 2))
            winScore = np.mean(muscleScore[:, mt1:mt2], 1)
            tmsmuscleratio = winScore / np.mean(muscleScore)

        # eyeblinks
        if self.options['blink'] == 'on':
            blinkidx = [i for i, chan in enumerate(self.options['chanpicks']) if chan in self.options['blinkelecs']]
            blinkratio = np.mean(tempCompZ[blinkidx, :], 0)

        # lateral eye movements
        if self.options['move'] == 'on':
            moveidx = [i for i, chan in enumerate(self.options['chanpicks']) if chan in self.options['moveelecs']]
            moveval = np.transpose(tempCompZ[moveidx,:])

        # electrode noise
        if self.options['elecnoise'] == 'on':
            elecnoise = np.amax(np.abs(tempCompZ), axis=0)

        # get indices for frequency range to detect persistent muscle activity
        freq = np.arange(self.options['plotfreqx'][0], self.options['plotfreqx'][1]+ 0.5, 0.5)

        # if needed for muscle activity detection or component inspection, calculate frequency spectrum
        if self.options['muscle'] == 'on' or self.options['compcheck'] == 'on':

            sfreq = self.epochs.info['sfreq']
            _, L, n_epoch = np.shape(self.S)

            # find the next power of 2 from the length of Y
            NFFT = 2**np.ceil(np.log2(abs(L)))
            f = sfreq/2 * np.linspace(0, 1, int(NFFT/2+1))
            freq = np.arange(self.options['plotfreqx'][0], self.options['plotfreqx'][1]+ 0.5, 0.5)

            Y2 = np.zeros([self.options['comps'], len(freq), n_epoch])

            # get the spectral information of each component of interest
            Y = np.fft.rfft(zscore(self.S, axis=1)[:self.options['comps'],:,:], n=int(NFFT), axis=1)/L
            Yout = np.abs(Y)**2

            # create frequency bins of 0.5 Hz in width centered around whole frequencies 
            for ia, a in enumerate(freq):
                index1 = np.argmin(np.abs(f-(a-0.25)))
                index2 = np.argmin(np.abs(f-(a+0.25)))
                Y2[:, ia, :] = np.mean(Yout[:, index1:index2,:], 1)

            self.fftbins = np.mean(Y2, 2)

        
        if self.options['muscle'] == 'on':

            # frequencies to include into fit
            if len(self.options['musclefreqin']) != 0:
                fin1 = np.argmin(np.abs(freq-self.options['musclefreqin'][0]))
                fin2 = np.argmin(np.abs(freq-self.options['musclefreqin'][1]))
                freqHz = freq[fin1:fin2]
            else:
                freqHz = freq

            # frequencies to exclude from fit
            if len(self.options['musclefreqex']) != 0:
                fex1 = np.argmin(np.abs(freqHz-self.options['musclefreqex'][0]))
                fex2 = np.argmin(np.abs(freqHz-self.options['musclefreqex'][1]))
                np.delete(freqHz, slice(fex1, fex2))
            
            # get idx of frequencies in power spectrum
            musclefidx = [i for i, f in enumerate(freq) if f in freqHz]

            # polynomial fit for each component, store the slope
            freqPow = self.fftbins[:, musclefidx]
            p = np.polyfit(np.log(freqHz), np.log(freqPow).T, 1)
            muscleratio = p[0,:]

        # create output storage
        self.compclass = np.zeros([self.options['comps']])

        # select if component is artifact
        print('\nClassifying components.')

        for compnum in range(self.options['comps']):

            if self.options['tmsmuscle'] == 'on' and tmsmuscleratio[compnum] >= self.options['tmsmusclethresh']:
                self.compclass[compnum] = 2

            elif self.options['blink'] == 'on' and np.abs(blinkratio[compnum]) >= self.options['blinkthresh']:
                self.compclass[compnum] = 3

            elif self.options['move'] == 'on' and moveval[compnum, 0] >= self.options['movethresh'] and moveval[compnum, 1] <= -self.options['movethresh']  \
                or  self.options['move'] == 'on' and moveval[compnum, 1] >= self.options['movethresh']  and moveval[compnum, 0] <= -self.options['movethresh'] :
                self.compclass[compnum] = 4

            elif self.options['muscle'] == 'on' and muscleratio[compnum] >= self.options['musclethresh']:
                self.compclass[compnum] = 5

            elif self.options['elecnoise'] == 'on' and elecnoise[compnum] >= np.abs(self.options['elecnoisethresh']):
                self.compclass[compnum] = 6

            else:
                self.compclass[compnum] = 1


        # if desired, open UI for a manual check of the components
        if self.options['compcheck'] == 'on':
            UIs.ui_select(self)

    


    def inverse_transform(self):

        self.badcomp = [i for i, comp in enumerate(self.compclass) if int(comp) != 1]
        goodcomp = [i for i in range(self.rank) if i not in self.badcomp]

        # correcting data by removing the detected artifactual components
        # dot product between the component time series and the transpose of the mixing matrix
        # mean added because data was whitened prior to ICA
        ncomps, npnts, nevents = np.shape(self.S)
        
        S_concat = np.reshape(self.S, [ncomps, -1])
        post = np.dot(S_concat[goodcomp,:].T, self.A[:,goodcomp].T)
        post += self.mean
        self.post = np.reshape(post.T, [len(self.options['chanpicks']), npnts, nevents])

        # check if satisfied with result
        if self.options['confirm'] == 'on':
            redo = UIs.ui_check(self)
        else:
            redo = False

        if redo:

            # ask if user wants to enter different settings with UI
            newsettings = UIs.ui_redo()

            if newsettings:
                self.set_options({'manualinput':'on'})
                self.fastica()

            else:
                self.set_options({'compcheck':'on'})

            self.compselect()
            self.inverse_transform()
            




    def transform_epochs_object(self):

        if self.options['remove'] == 'on':
            try:
                self.post
            except:
                self.inverse_transform()

            ch_idx = [  i for i, chan in enumerate(self.epochs.ch_names) 
                        if chan in self.options['chanpicks']]

            self.epochs._data[:, ch_idx, :] = np.moveaxis(self.post, 2, 0)
            self.transformed = True
            self.rank = np.linalg.matrix_rank(self.epochs._data)


            print('\n{} independent components removed from data.\n'.format(len(self.badcomp)))

            if len(self.badcomp) > 0:
                print('Thereof:')
                print('{} x TMS muscle artifacts'.format(sum(self.compclass==2)))
                print('{} x eye blink artifacts'.format(sum(self.compclass==3)))
                print('{} x lateral eye movement artifacts'.format(sum(self.compclass==4)))
                print('{} x persistent muscle activity'.format(sum(self.compclass==5)))
                print('{} x electrode noise \n'.format(sum(self.compclass==6)))




    def reset_orig_backend(self):

        matplotlib.use(self.orig_backend)




    def fit_select_transform(self):
        
        self.fastica()
        self.compselect()
        self.inverse_transform()
        self.transform_epochs_object()
        self.reset_orig_backend()