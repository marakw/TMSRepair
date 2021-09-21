def check_param(epochs, options):

    # if any number of components specified, check it is less or equal to the number of channels
    if options['comps'] != -1:
        if options['comps'] > len(options['chanpicks']):
            raise ValueError('\n The number of components to choose from ({})'
                             'is more than the number of channels ({}).'
                             .format(options['comps'], epochs.info['nchan']))
    else:
        options['comps'] = len(options['chanpicks'])

    # check figure inputs
    lower = options['figsize'].lower()
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
        # TODO: add comparison to epoch length

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


def eval_param(options, **kwargs):

    for opt, val in kwargs.items():

        opt = opt.lower()

        if opt in options:
            options[opt] = val
        else:
            raise ValueError('\n{} is not a recognized parameter name.'.format(opt))

    return options

