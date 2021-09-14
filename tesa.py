def tesa(epochs, **kwargs):

    import matplotlib
    import TESA.tesa_fastica as tesa_fastica
    import TESA.tesa_misc as tesa_misc
    import TESA.tesa_UIs as tesa_UIs

    # get the current backend for resetting it later and set to Agg for tkinter
    orig_backend = matplotlib.get_backend()
    matplotlib.use('Agg')

    # initialize/overwrite dict in epochs object
    epochs.tesa = {}

    # define defaults independent of method
    options =  {'manualinput':'on',
                'manualcheck':'on',
                'threshfeedback': 'on',
                'chanpicks':epochs.ch_names,
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
                'musclefreqex':[],
                
                'elecnoise':'on',
                'elecnoisethresh':2}
            
    # evaluate any parameters passed
    options = tesa_misc.eval_param(options, **kwargs)

    # if manual input desired open UI
    if options['manualinput'] == 'on':
        options = tesa_UIs.ui_input(options)

    # check if parameters are valid
    tesa_misc.check_param(epochs, options)

    # run fast ICA and component selection
    epochs = tesa_fastica.run(epochs, options)

    # reset backend
    matplotlib.use(orig_backend)

    return epochs