import mne
import numpy as np



def check_param(inst):

    options = inst.options
    epochs = inst.epochs

    # if any number of components specified, check it is less or equal to the number of channels
    if options['comps'] != -1:
        if options['comps'] > len(options['chanpicks']):
            print('\n The number of components to choose from ({}) '
                  'is more than the number of channel picks ({}).'
                  .format(options['comps'], len(options['chanpicks'])))
            print('Adjusting to maximal number of components ({}).'.format(len(options['chanpicks'])))
            options['comps'] = len(options['chanpicks'])
    else:
        options['comps'] = len(options['chanpicks'])

    # check figure inputs
    accepted_strings = ['small', 'medium', 'large']
    if options['figsize'].lower() not in accepted_strings:
        raise ValueError('Input for \'figsize\' must be either \'small\', \'medium\', or \'large\'.')

    # check the length of the subwindow specified for plotting
    if len(options['plottimex']) != 2:
        raise ValueError('Input for \'plottimex\' must be in the following format: [start, end], e.g. [-200, 500].')
    elif options['plottimex'][0] < epochs.times[0]*1000 or options['plottimex'][1] > epochs.times[-1]*1000:
        raise ValueError('Input for \'plottimex\' must be within the epoch\'s time window.')

    # check if frequency input is in the right format and has above 0 values
    if len(options['plotfreqx']) != 2:
        raise ValueError('Input for \'plotfreqx\' must be in the following format: [low, high], e.g. [1, 100].')
    elif options['plotfreqx'][0] | options['plotfreqx'][1] < 0:
        raise ValueError('Input for \'plotfreqx\' must be larger than 0.')

    if options['freqscale'].lower() not in ['raw', 'log', 'log10', 'db']:
        raise ValueError('Input for \'freqscale\' must be either \'raw\', \'log\', \'log10\' or \'db\'.')

    # check the muscle threshold input
    if options['tmsmuscle'] == 'on':
        if options['tmsmusclethresh'] < 0:
            raise ValueError('Input for \'tmsmusclethresh\' must be greater than 0.')
        elif len(options['tmsmusclewin']) != 2:
            raise ValueError('Input for \'tmsmuscleswin\' must be in the following format: [start,end]. e.g. [11,51].')
        elif options['tmsmusclewin'][0] < epochs.times[0]*1000 or options['tmsmusclewin'][1] > epochs.times[-1]*1000:
            raise ValueError(   'Input for \'tmsmuscleswin\' is out of epoch bounds.'
                                'It needs to be between {} and {} ms.'
                                .format(epochs.times[0]*1000, epochs.times[-1]*1000))

    # check options for the fast ICA function
    if options['approach'] not in ['parallel', 'deflation']:
        raise ValueError('Input for \'approach\' must be either \'parallel\' or \'deflation\'.')
    elif options['g'] not in ['logcosh', 'exp', 'cube']:
        raise ValueError('Input for \'g\' must be either \C.')

    # check frequency scaling input
    if options['freqscale'] not in ['raw', 'log', 'log10', 'db']:
        raise ValueError('Input for \'freqscale\' needs to be either \'raw\', \'log\', \'log10\' or \'db\'.')

    # check lateral eye movement input, disable if one or both electrodes are not present.
    if options['move'] == 'on':
        eNum = [i for i, chan in enumerate(options['chanpicks']) if chan in options['moveelecs']]
    
        if len(eNum) < 2:
            options['move'] = 'off'
            Warning('One or both electrodes required for detecting lateral eye movements not present.'
                    'This function has been disabled.')

    # check eyeblink input, if at least one electrode present
    if options['blink'] == 'on':
        blinkNum = [i for i, chan in enumerate(options['chanpicks']) if chan in options['blinkelecs']]
        missing = [chan for chan in options['blinkelecs'] if chan not in options['chanpicks']]

        if len(blinkNum) == 0:
            options['blink'] = 'off'
            Warning('Blink electrodes not found. Blink detection has been disabled.')
        elif len(blinkNum) == 1:
            Warning('Electrode {} is not present in the data.'
                    'Electrode not included in blink detection.'.format(missing))
        
    # check input for persistent muscle activity
    if options['muscle'] == 'on':
        if len(options['musclefreqin']) == 0:
            options['musclefreqin'] = options['plotfreqx']
        elif len(options['musclefreqin']) != 2:
            raise ValueError('Input for \'musclefreqin\' must be in the following format: [low, high], e.g. [7, 75].')
        elif options['musclefreqin'][0] < options['plotfreqx'][0] or options['musclefreqin'][1] > options['plotfreqx'][1]:
            raise ValueError('Input for \'musclefreqin\' are outside of the frequency range set by input \'plotfreqx\'.'
                            'Please adjust.')
        
        if len(options['musclefreqex']) == 0:
            pass
        elif len(options['musclefreqex']) != 2:
            raise ValueError('Input for \'musclefreqex\' must be either empty or in the following format:'
                                '[low, high], e.g. [48, 52].')
        elif options['musclefreqex'][0] < options['musclefreqin'][0] or options['musclefreqex'][1] > options['musclefreqin'][1]:
            raise ValueError('Input for \'musclefreqex\' are outside of the frequency range set by input \'musclefreqin\'.'
                                'Please adjust.')                  




def eval_param(options, kwargs):

    for opt, val in kwargs.items():

        opt = opt.lower()

        if opt in options:
            options[opt] = val
        else:
            raise ValueError('\n{} is not a recognized parameter name.'.format(opt))

    return options





def chan_visual_inspection(x, indexmode = 'exclude'):

    """
    from Github mkeute (visual_inspection).
    Allows you to visually inspect and exclude elements from an array.
    The array x typically contains summary statistics, e.g., the signal
    variance for each trial.
    """

    import matplotlib.pyplot as plt
    from matplotlib.widgets import RectangleSelector
    import numpy as np
    import matplotlib

    matplotlib.use('Qt5Agg')

    x = np.array(x)
    x = x.flatten()
    nanix = np.zeros(len(x))

    def line_select_callback(eclick, erelease):
        """
        Callback for line selection.
    
        *eclick* and *erelease* are the press and release events.
        """
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        
        print("(%3.2f, %3.2f) --> (%3.2f, %3.2f)" % (x1, y1, x2, y2))
        print(" The button you used were: %s %s" % (eclick.button, erelease.button))
    

    fig, current_ax = plt.subplots()                 # make a new plotting range
    # plt.plot(np.arange(len(x)), x, lw=1, c='b', alpha=.7)  # plot something
    current_ax.plot(x, 'b.', alpha=.7)  # plot something

    print("\n      click  -->  release")

    # drawtype is 'box' or 'line' or 'none'
    RS = RectangleSelector(current_ax, line_select_callback,
                                    drawtype='box', useblit=True,
                                    button=[1],  # don't use middle button
                                    minspanx=5, minspany=5,
                                    spancoords='pixels',
                                    interactive=True)
    RSinv = RectangleSelector(current_ax, line_select_callback,
                                drawtype='box', useblit=True,
                                button=[3],  # don't use middle button
                                minspanx=5, minspany=5,
                                spancoords='pixels',
                                interactive=True)
    plt.connect('key_press_event', (RS, RSinv))

    while plt.fignum_exists(1):
        plt.cla()
        current_ax.set_ylim([np.min(x[np.where(nanix == 0)[0]]), 1.1*np.max(x[np.where(nanix == 0)[0]])])
        current_ax.plot(x, 'b.', alpha=.7)  # plot something
        if np.sum(nanix) > 0:
            current_ax.plot(np.squeeze(np.where(nanix == 1)), x[np.where(nanix == 1)], 'w.', alpha=.7)  # plot something

        fig.show()
        plt.pause(.1)
        if plt.fignum_exists(1):
            plt.waitforbuttonpress(timeout = 2)
            
            if (RS.geometry[1][1] > 1):
                exclix = np.where((x > min(RS.geometry[0])) & (x < max(RS.geometry[0])))[0]
                exclix = exclix[np.where((exclix > min(RS.geometry[1])) & (exclix < max(RS.geometry[1])))]
                nanix[exclix] = 1
            if (RSinv.geometry[1][1] > 1):
                exclix = np.where((x > min(RSinv.geometry[0])) & (x < max(RSinv.geometry[0])))[0]
                exclix = exclix[np.where((exclix > min(RSinv.geometry[1])) & (exclix < max(RSinv.geometry[1])))]
                nanix[exclix] = 0
            if not plt.fignum_exists(1):
                break
            else:
                plt.pause(.1)
        else:
            plt.pause(.1)
            break
    if indexmode == 'exclude':
        return np.where(nanix == 1)[0]
    elif indexmode == 'keep':
        return np.where(nanix == 0)[0]
    else:
    	raise ValueError




def MNE_raw_format(eegdata, ch_names, sfreq):

    """
    Helps get EEG data into MNE raw object format by using some default values.
    Channel types all defined as EEG and default 1005 montage used.

    Args:
        eegdata (numpy array): EEG data array, timepoints*channels
        ch_names (list): list of strings with channel names
        sfreq (float, int): sampling frequency

    Returns:
        raw : instance of MNE raw
    """

    ch_types = ['eeg']*len(ch_names)
    
    info = mne.create_info(ch_names=ch_names, 
                           sfreq=sfreq, 
                           ch_types=ch_types,
                           verbose=0)

    raw = mne.io.RawArray(np.transpose(eegdata), info, verbose=0)

    raw.set_montage(mne.channels.make_standard_montage('standard_1005'), verbose=0)

    return raw




def cubic_interpolation(epochs, win):

    from scipy import interpolate

    x = epochs.times

    # convert window to indices in epochs; +1 because it should include the last timepoint
    idx1 = np.argmin(np.abs(x - win[0]*0.001))
    idx2 = np.argmin(np.abs(x - win[1]*0.001)) +1

    # delete timepoints that should be interpolated
    x = np.delete(x, np.s_[idx1:idx2], 0)

    for i, epoch in enumerate(epochs):

        y = np.delete(epoch, np.s_[idx1:idx2], -1)
        p = interpolate.interp1d(x, y, kind='cubic')

        # get the interpolation values for the timepoints of interest
        interp_values = p.__call__(epochs.times[idx1:idx2])

        # for each epoch replace timepoints in epochs object
        epochs._data[i, :, idx1:idx2] = interp_values

    return epochs
