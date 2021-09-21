def compselect(epochs, options):

    import numpy as np
    from scipy.stats import zscore
    import TESA.tesa_UIs as tesa_UIs

    # create output storage
    epochs.tesa['compclass'] = np.zeros([options['comps']])

    # create zscore for each component across channels
    tempCompZ = zscore(epochs.tesa['A'], 0)

    # calculate mean component variance over epochs
    print('\nCalculating component variance.')
    vars = np.var(np.mean(epochs.tesa['S'], 2), axis=1)
    vars_norm = vars/sum(vars)*100

    # tms muscle window
    if options['tmsmuscle'] == 'on':
        mt1 = np.argmin(np.abs(epochs.times*1000 - options['tmsmusclewin'][0]))
        mt2 = np.argmin(np.abs(epochs.times*1000 - options['tmsmusclewin'][1]))

        muscleScore = np.abs(np.mean(epochs.tesa['S'], 2))
        winScore = np.mean(muscleScore[:, mt1:mt2], 1)
        tmsmuscleratio = winScore / np.mean(muscleScore)

    # eyeblinks
    if options['blink'] == 'on':
        blinkidx = [i for i, chan in enumerate(options['chanpicks']) if chan in options['blinkelecs']]
        blinkratio = np.mean(tempCompZ[blinkidx, :], 0)

    # lateral eye movements
    if options['move'] == 'on':
        moveidx = [i for i, chan in enumerate(options['chanpicks']) if chan in options['moveelecs']]
        moveval = np.transpose(tempCompZ[moveidx,:])

    # electrode noise
    if options['elecnoise'] == 'on':
        elecnoise = np.amax(np.abs(tempCompZ), axis=0)

    # get indices for frequency range to detect persistent muscle activity
    freq = np.arange(options['plotfreqx'][0], options['plotfreqx'][1]+ 0.5, 0.5)

    if options['muscle'] == 'on':

        # frequencies to include into fit
        if len(options['musclefreqin']) != 0:
            fin1 = np.argmin(np.abs(freq-options['musclefreqin'][0]))
            fin2 = np.argmin(np.abs(freq-options['musclefreqin'][1]))
            freqHz = freq[fin1:fin2]
        else:
            freqHz = freq

        # frequencies to exclude from fit
        if len(options['musclefreqex']) != 0:
            fex1 = np.argmin(np.abs(freqHz-options['musclefreqex'][0]))
            fex2 = np.argmin(np.abs(freqHz-options['musclefreqex'][1]))
            np.delete(freqHz, slice(fex1, fex2))
        
        # get idx of frequencies in power spectrum
        musclefidx = [i for i, f in enumerate(freq) if f in freqHz]

    # initialize variables
    muscleratio = np.zeros([options['comps']])
    fftbins = np.zeros([options['comps'], len(freq)])

    # if needed for muscle activity detection of component inspection, calculate frequency spectrum
    if options['muscle'] == 'on' or options['compcheck'] == 'on':

        T = 1/epochs.info['sfreq']
        _, L, n_epoch = np.shape(epochs.tesa['S'])

        # find the next power of 2 from the length of Y
        NFFT = 2**np.ceil(np.log2(abs(L)))
        f = epochs.info['sfreq']/2 * np.linspace(0, 1, int(NFFT/2+1))
        freq = np.arange(options['plotfreqx'][0], options['plotfreqx'][1]+ 0.5, 0.5)

        Y2 = np.zeros([options['comps'], len(freq), n_epoch])

        # get the spectral information of each component of interest
        Y = np.fft.rfft(zscore(epochs.tesa['S'], axis=1)[:options['comps'],:,:], n=int(NFFT), axis=1)/L
        Yout = np.abs(Y)**2

        # create frequency bins of 0.5 Hz in width centered around whole frequencies 
        for ia, a in enumerate(freq):
            index1 = np.argmin(np.abs(f-(a-0.25)))
            index2 = np.argmin(np.abs(f-(a+0.25)))
            Y2[:, ia, :] = np.mean(Yout[:, index1:index2,:], 1)

        fftbins = np.mean(Y2, 2)


    # loop over components
    print('\nClassifying components.')

    for compnum in range(options['comps']):

        # persistent muscle activity, polynomial fit, store the slope
        if options['muscle'] == 'on':
            freqPow = fftbins[compnum, musclefidx]
            p = np.polyfit(np.log(freqHz), np.log(freqPow), 1)
            muscleratio[compnum] = p[0]

        # select if component is artifact
        if options['tmsmuscle'] == 'on' and tmsmuscleratio[compnum] >= options['tmsmusclethresh']:
            epochs.tesa['compclass'][compnum] = 2

        elif options['blink'] == 'on' and np.abs(blinkratio[compnum]) >= options['blinkthresh']:
            epochs.tesa['compclass'][compnum] = 3

        elif options['move'] == 'on' and moveval[compnum, 0] >= options['movethresh'] and moveval[compnum, 1] <= -options['movethresh']  \
            or  options['move'] == 'on' and moveval[compnum, 1] >= options['movethresh']  and moveval[compnum, 0] <= -options['movethresh'] :
            epochs.tesa['compclass'][compnum] = 4

        elif options['muscle'] == 'on' and muscleratio[compnum] >= options['musclethresh']:
            epochs.tesa['compclass'][compnum] = 5

        elif options['elecnoise'] == 'on' and elecnoise[compnum] >= np.abs(options['elecnoisethresh']):
            epochs.tesa['compclass'][compnum] = 6

        else:
            epochs.tesa['compclass'][compnum] = 1


    # if desired, open UI for a manual check of the components
    if options['compcheck'] == 'on':
        for compnum in range(options['comps']):
            epochs = tesa_UIs.ui_select(epochs, options, compnum, freq, fftbins[compnum,:])

    return epochs




def sortcomps(epochs, icasig, mixing):

    import numpy as np

    # get variance of each component in percent relative to all components as mean over epochs
    vars = np.var(np.mean(epochs.tesa['S'], 2), axis=1)
    vars_norm = vars/sum(vars)*100

    # sort components in descending order based on variance
    ixsSort = np.flip(np.argsort(vars_norm))

    epochs.tesa['A'] =  epochs.tesa['A'][:, ixsSort]
    epochs.tesa['S'] = epochs.tesa['S'][ixsSort, :,:]
    icasig = icasig[:,ixsSort]
    mixing=mixing[:,ixsSort]

    print('\nICA weights sorted by time course variance.')

    return epochs, icasig, mixing



def run (epochs, options):

    from sklearn.decomposition import FastICA
    import numpy as np
    import TESA.tesa_UIs as tesa_UIs
    import TESA.tesa as tesa

    # reconcatenate epochs
    ch_idx = [i for i, chan in enumerate(epochs.ch_names) if chan in options['chanpicks']]
    data = epochs._data[:, ch_idx, :]
    nevents, nchans, npnts = np.shape(data)
    data_concat = np.reshape(np.moveaxis(data, 0, 2), [nchans, -1])

    print('\nPerforming fast ICA on data using {} approach.'
          .format(options['approach']))

    # run FastICA and reshape component time courses
    rank = np.linalg.matrix_rank(data_concat)
    print('The matrix rank is {}. '. format(rank))

    if rank < options['comps']:
        print('Number of components adjusted accordingly.')
        options['comps'] = rank

    ica = FastICA(n_components=rank, algorithm=options['approach'], fun=options['g'], max_iter=1000)
    ica = ica.fit(data_concat.T)
    icasig = ica.transform(data_concat.T)
    epochs.tesa['S'] = np.reshape(icasig.T, [-1, npnts, nevents]) # component time courses
    epochs.tesa['A'] = ica.mixing_ # topographies

    # sort components after variance
    epochs, icasig, ica.mixing_ = sortcomps(epochs, icasig, ica.mixing_)

    # select components
    select = True
    while select == True:

        epochs = compselect(epochs, options)
        badcomp = [i for i, comp in enumerate(epochs.tesa['compclass']) if int(comp) != 1]
        goodcomp = [i for i in range(rank) if i not in badcomp]

        print(goodcomp)
        # correcting data by removing the detected artifactual components
        pre_mean = np.mean(data, 0)
        ica.mixing_ = ica.mixing_[:, goodcomp]
        post = ica.inverse_transform(icasig[:, goodcomp])
        post = np.reshape(post.T, [nchans, npnts, nevents])
        post_mean = np.mean(post, 2)

        # check if satisfied with result
        if options['confirm'] == 'on':
            redo = tesa_UIs.ui_check(epochs.times*1000, pre_mean, post_mean, options)
        else:
            redo = False

        # if redo desired check whether everything should be redone or just the manual component selection
        if redo == True:
            newsettings = tesa_UIs.ui_redo()

            if newsettings == True:
                # if new settings are desired, call main function recursively 
                #TODO check recursion
                options['manualinput'] = 'on'
                epochs = tesa.tesa(epochs, **options)
                select = False
            else:
                options['compcheck'] = 'on'

        else:
            # if components should be removed replace data in epochs object. Replace only data of non-rejected channels
            if options['remove'] == 'on':
                epochs._data[:, ch_idx, :] = np.moveaxis(post, 2, 0)
                print('\n{} independent components removed from data.\n'.format(len(badcomp)))

                if len(badcomp) > 0:
                    print('Thereof:')
                    print('{} x TMS muscle artifacts'.format(sum(epochs.tesa['compclass']==2)))
                    print('{} x eye blink artifacts'.format(sum(epochs.tesa['compclass']==3)))
                    print('{} x lateral eye movement artifacts'.format(sum(epochs.tesa['compclass']==4)))
                    print('{} x persistent muscle activity'.format(sum(epochs.tesa['compclass']==5)))
                    print('{} x electrode noise \n'.format(sum(epochs.tesa['compclass']==6)))

            epochs.tesa['badcomponents'] = badcomp
            epochs.tesa['options'] = options
            select = False

    return epochs

