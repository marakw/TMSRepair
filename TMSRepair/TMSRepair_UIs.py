def ui_raw(options):
    
    import tkinter as tk
    import numpy as np

    win = tk.Tk()
    win.configure(background='white')
    win.title('Manual component classification. Choose and click OK to continue.')

    if options['figsize'] == 'small':
        sz = [700, 560]
    elif options['figsize'] == 'medium':
        sz = [900, 600]
    elif options['figsize'] == 'large':
        sz = [1200, 900]

    # center window horizontally and vertically
    sw = win.winfo_screenwidth()
    xpos = int(np.ceil((sw-sz[0])/2))

    sh = win.winfo_screenheight()
    ypos = int(np.ceil((sh-sz[1])/2))

    win.geometry(f'{sz[0]}x{sz[1]}+{xpos}+{ypos}')

    return win


def ui_check(self):

    import numpy as np
    import tkinter as tk
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.pyplot as plt

    # extract data from instance
    ch_idx = [  i for i, chan in enumerate(self.epochs.ch_names) 
                if chan in self.options['chanpicks']]

    post= np.mean(self.post, 2)
    pre = np.mean(self.epochs._data[:,ch_idx, :], 0)
    rel_time = self.epochs.times*1000

    win = ui_raw(self.options)
    win.configure(background='white')
    win.title('Are you satisfied with the correction?')

    # plot pre-/post
    fig, (sp1, sp2) = plt.subplots(2)

    sp1.plot(rel_time, pre.T, 'k', linewidth=0.5)
    sp1.title.set_text('Pre')
    sp1.set_xlabel('time [ms]')
    sp1.set_ylabel('amplitude [\muV]') 

    sp2.plot(rel_time, post.T, 'k', linewidth=0.5)
    sp2.title.set_text('Post')
    sp2.set_xlabel('time [ms]')
    sp2.set_ylabel('amplitude [\muV]') 

    # make ylimits equal in both plots
    sp2.set_ylim(sp1.get_ylim())

    canvas = FigureCanvasTkAgg(fig)
    widget = canvas.get_tk_widget()
    widget.pack(fill=tk.BOTH, expand=tk.YES, side='bottom')
    canvas.draw()

    buttonframe = tk.Frame(win, padx=10, pady=10, bg='white')
    buttonframe.pack(side='top')

    def on_yes():
        global redo
        redo = False
        win.destroy()

    def on_no():
        global redo
        redo = True
        win.destroy()

    yesbutton = tk.Button(buttonframe, bg='white', text='Yes', command=on_yes, padx=20)
    yesbutton.pack(side='left')

    nobutton = tk.Button(buttonframe, bg='white', text='No', command=on_no, padx=20)
    nobutton.pack(side='left')

    win.mainloop()

    return redo


def ui_redo():

    import tkinter as tk

    win = tk.Tk()
    win.configure(background='white')
    win.title('Redo with new settings?')

    buttonframe = tk.Frame(win, padx=10, pady=10, bg='white')
    buttonframe.pack(side='top')

    def on_yes():
        global newsettings
        newsettings = True
        win.destroy()

    def on_no():
        global newsettings
        newsettings = False
        win.destroy()

    yesbutton = tk.Button(buttonframe, bg='white', text='Yes, redo.', command=on_yes, padx=20)
    yesbutton.pack(side='left')

    nobutton = tk.Button(buttonframe, bg='white', text='No, only re-check components.', command=on_no, padx=20)
    nobutton.pack(side='left')

    win.mainloop()  

    return newsettings



def ui_select(inst):

    import tkinter as tk
    from mne.viz import plot_topomap
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.pyplot as plt
    from scipy.stats import zscore
    from mne.channels import read_layout
    import numpy as np


    rel_time = inst.epochs.times*1000
    ch_names = [chan for chan in inst.epochs.ch_names 
                if chan in inst.options['chanpicks']]

    # color code for plotting (red = suspected artifact)
    clrs = np.where(inst.compclass == 1, 'b', 'r')


    for compnum in range(inst.options['comps']):

        win = ui_raw(inst.options)
        fig, ((sp1, sp2), (sp3, sp4)) = plt.subplots(2, 2)

        temp = inst.S[compnum, :, :]

        # plot time series of component
        sp1.plot(rel_time, np.mean(temp, 1), clrs[compnum])
        sp1.title.set_text('Component time series across channels')
        sp1.set_xlabel('Time [ms]')
        sp1.set_ylabel('Amplitude [a.u.]')

        # plot topographical plot
        # adjust channel positions from default mne layout, 
        # original from mkeute (github), plot topographical plot with mne
        layout = read_layout("EEG1005")
        pos = (np.asanyarray([layout.pos[layout.names.index(ch)] for ch in ch_names])[:, 0:2]- 0.5) / 5
        plot_topomap(inst.A[:,compnum].T, pos, names=ch_names, show_names=True, axes=sp2, show=False)
        sp2.title.set_text('Topographical map')
        
        # plot spectral information
        freq = np.arange(   inst.options['plotfreqx'][0], 
                            inst.options['plotfreqx'][1]+ 0.5, 0.5)

        if inst.options['freqscale'] == 'raw':
            sp3.plot(freq, inst.fftbins[compnum, :].T)
        elif inst.options['freqscale'] == 'log':
            sp3.plot(freq, np.log(inst.fftbins[compnum, :].T))
        elif inst.options['freqscale'] == 'log10':
            sp3.plot(freq, np.log10(inst.fftbins[compnum, :].T))
        elif inst.options['freqscale'] == 'db':
            sp3.plot(freq, 10*np.log10(inst.fftbins[compnum, :].T))

        sp3.title.set_text('Power spectrum')
        sp3.set_xlabel('Frequency [Hz]')
        sp3.set_ylabel('Power [muV^2/Hz]')

        # plot time course matrix
        tp1 = np.argmin(np.abs(rel_time - inst.options['plottimex'][0]))
        tp2 = np.argmin(np.abs(rel_time - inst.options['plottimex'][1]))
        sp4.matshow(np.transpose(zscore(temp[tp1:tp2, :])), extent=[0, 1, 0, 0.8], interpolation=None, cmap='RdBu')
        sp4.title.set_text('Time course matrix')
        sp4.set_xlabel('Time [ms]')
        sp4.set_ylabel('Trials')

        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=tk.YES, side='bottom')
        canvas.draw()

        def on_closing():

            choice = clicked.get()
            inst.compclass[compnum] = int(art_types.index(choice)) + 1
            win.destroy()
        
        buttonframe = tk.Frame(win, padx=10, pady=10, bg='white')
        buttonframe.pack(side='right')

        okbutton = tk.Button(buttonframe, bg='white', text='OK', command=on_closing)
        okbutton.pack(side='right')

        # make a menu for choosing whether component should be rejected or not. Default should be based on threshold.
        clicked = tk.StringVar()

        art_types = ["neural", "tms muscle artifact", 
                    "eyeblink", "lateral eye movement", 
                    "persistent muscle activity", "electrode noise"]

        # use the classification number to index the list with the different artifact types
        # and set as default value in dropdown menu
        clicked.set(art_types[int(inst.compclass[compnum])-1])

        menu = tk.OptionMenu(buttonframe, clicked, *art_types)
        menu.configure(background='white', activebackground='white')
        menu.pack(side='right')

        win.mainloop()




def textfield (win, default, rownr, colnr, sticky='w'):

    import tkinter as tk

    inputvar = tk.StringVar()

    if type(default) == list and len(default) == 2:
        inputvar.set('[' + str(default[0]) + ', ' + str(default[1]) + ']')
    else:
        inputvar.set(default)

    txtfld = tk.Entry(win, text=inputvar)
    txtfld.configure(background='white', width=10)
    txtfld.grid(row=rownr, column=colnr, sticky=sticky)

    return inputvar



def toggle(frame, default, row, column):

    import tkinter as tk

    var = tk.BooleanVar()
    if default =='on':
        var.set(True)
    else:
        var.set(False)

    r_on = tk.Radiobutton(frame, text='on', background='white', variable=var, value=True)
    r_on.grid(row=row, column=column, sticky='w')

    r_off = tk.Radiobutton(frame, text='off', background='white', variable=var, value=False)
    r_off.grid(row=row, column=column, sticky='e')

    return var



def choicemenu(frame, default, choices, row, column):

    import tkinter as tk

    var =  tk.StringVar(value=default)
    menu = tk.OptionMenu(frame, var, *choices)
    menu.configure(background='white', activebackground='white', width=10)
    menu.grid(row=row, column=column, sticky='w')

    return var



def ui_input(options):

    import tkinter as tk
    import ast
    import numpy as np

    win = ui_raw(options)
    win.title('TESA - Please specify settings.')
    ttl_font = ('Helvetica', 12, 'bold')
    framepadx = 20
    framepady = 20

    # Frames
    frame_fig = tk.Frame(win, bg='white', padx=framepadx, pady=framepady)
    frame_feedb = tk.Frame(win, bg='white', padx=framepadx, pady=framepady)
    frame_tmsmuscle = tk.Frame(win, bg='white', padx=framepadx, pady=framepady)
    
    frame_ica = tk.Frame(win, bg='white', padx=framepadx, pady=framepady)
    frame_eye = tk.Frame(win, bg='white', padx=framepadx, pady=framepady)
    frame_lat = tk.Frame(win, bg='white', padx=framepadx, pady=framepady)
    frame_muscle = tk.Frame(win, bg='white', padx=framepadx, pady=framepady)
    frame_elnoise = tk.Frame(win, bg='white', padx=framepadx, pady=framepady)

    frames = [frame_fig, frame_feedb, frame_tmsmuscle, frame_ica, 
                frame_eye, frame_lat, frame_muscle, frame_elnoise]
    titles = ['Figure Settings', 'Feedback Settings', 'TMS muscle artifacts', 'FastICA Settings', 
                'Eyeblinks', 'Lateral eye movement', 'Persistent muscle activity', 'Electrode noise']

    # Frame titles
    for i, ttl in enumerate(titles):
        tk.Label(frames[i], text=ttl, background='white', font=ttl_font).grid(row=0, column=0, sticky='w')


    # FIGURE SETTINGS
    tk.Label(frame_fig, text='Figure Size: ', background='white').grid(row=1, column=0, sticky='w')
    figsize = choicemenu(frame_fig, options['figsize'], ('small', 'medium', 'large'), 1, 1)

    tk.Label(frame_fig, text='Time window [ms]: ', background='white').grid(row=2, column=0, sticky='w')
    plottimex = textfield(frame_fig, options['plottimex'], 2, 1, 'w')

    tk.Label(frame_fig, text='Frequencies to plot [Hz]: ', background='white').grid(row=3, column=0, sticky='w')
    plotfreqx = textfield(frame_fig, options['plotfreqx'], 3, 1, 'w')

    tk.Label(frame_fig, text='Frequency scaling: ', background='white').grid(row=4, column=0, sticky='w')
    freqscale = choicemenu(frame_fig, options['freqscale'], ('raw', 'log', 'log10', 'db'), 4, 1)

    frame_fig.grid(row=0, column=0, sticky='nw')
    frame_fig.grid_columnconfigure(1, minsize=100)



    # FEEDBACK SETTINGS
    tk.Label(frame_feedb, text='Number of components: ', background='white').grid(row=1, column=0, sticky='w')
    comps = textfield(frame_feedb, options['comps'], 1, 1, 'w')

    # Manual component check
    tk.Label(frame_feedb, text='Manual component check: ', background='white').grid(row=2, column=0, sticky='w')
    compcheck = toggle(frame_feedb, options['compcheck'], 2, 1)

    # Feedback on thresholds
    tk.Label(frame_feedb, text='Feedback on thresholds: ', background='white').grid(row=3, column=0, sticky='w')
    threshfeedback = toggle(frame_feedb, options['threshfeedback'], 3, 1)

    # Remove components
    tk.Label(frame_feedb, text='Remove selected components: ', background='white').grid(row=4, column=0, sticky='w')
    remove = toggle(frame_feedb, options['remove'], 4, 1)

    frame_feedb.grid(row=0, column=1, sticky='nw')
    frame_feedb.grid_columnconfigure(1, minsize=100)



    # TMS-EVOKED MUSCLE ARTIFACTS
    tmsmuscle = toggle(frame_tmsmuscle, options['tmsmuscle'], 1, 1)

    tk.Label(frame_tmsmuscle, text='TMS muscle threshold: ', background='white').grid(row=2, column=0, sticky='w')
    tmsmusclethresh = textfield(frame_tmsmuscle, options['tmsmusclethresh'], 2, 1, 'w')

    tk.Label(frame_tmsmuscle, text='TMS muscle window: ', background='white').grid(row=3, column=0, sticky='w')
    tmsmusclewin = textfield(frame_tmsmuscle, options['tmsmusclewin'], 3, 1, 'w')

    frame_tmsmuscle.grid(row=1, column=0, sticky='nw')
    frame_tmsmuscle.grid_columnconfigure(1, minsize=100)



    # ICA SETTINGS
    tk.Label(frame_ica, text='Approach: ', background='white').grid(row=1, column=0, sticky='w')
    approach = choicemenu(frame_ica, options['approach'], ('parallel', 'deflation'), 1, 1)

    tk.Label(frame_ica, text='Contrast function (g): ', background='white').grid(row=2, column=0, sticky='w')
    g = choicemenu(frame_ica, options['g'], ('logcosh', 'exp', 'cube'), 2, 1)

    frame_ica.grid(row=1, column=1, sticky='nw')
    frame_ica.grid_columnconfigure(1, minsize=100)



    # EYEBLINKS
    blink = toggle(frame_eye, options['blink'], 1, 1)

    tk.Label(frame_eye, text='Blink threshold: ', background='white').grid(row=2, column=0, sticky='w')
    blinkthresh = textfield(frame_eye, options['blinkthresh'], 2, 1, 'nsew')

    tk.Label(frame_eye, text='Electrodes used: ', background='white').grid(row=3, column=0, sticky='w')
    blinkelecs = textfield(frame_eye, options['blinkelecs'], 3, 1, 'nsew')

    frame_eye.grid(row=2, column=0, sticky='nw')
    frame_eye.grid_columnconfigure(1, minsize=100)



    # LATERAL EYE MOVEMENTS
    move = toggle(frame_lat, options['move'], 1, 1)

    tk.Label(frame_lat, text='Lateral movement threshold: ', background='white').grid(row=2, column=0, sticky='w')
    movethresh = textfield(frame_lat, options['movethresh'], 2, 1, 'nsew')

    tk.Label(frame_lat, text='Electrodes used: ', background='white').grid(row=3, column=0, sticky='w')
    moveelecs = textfield(frame_lat, options['moveelecs'], 3, 1, 'nsew')

    frame_lat.grid(row=2, column=1, sticky='nw')
    frame_lat.grid_columnconfigure(1, minsize=100)



    # PERSISTENT MUSCLE ACTIVITY
    muscle = toggle(frame_muscle, options['muscle'], 1, 1)

    tk.Label(frame_muscle, text='Muscle activity threshold: ', background='white').grid(row=2, column=0, sticky='w')
    musclethresh = textfield(frame_muscle, options['musclethresh'], 2, 1, 'nsew')

    tk.Label(frame_muscle, text='Frequency range to include: ', background='white').grid(row=3, column=0, sticky='w')
    musclefreqin = textfield(frame_muscle, options['musclefreqin'], 3, 1, 'nsew')

    tk.Label(frame_muscle, text='Frequency range to exclude: ', background='white').grid(row=4, column=0, sticky='w')
    musclefreqex = textfield(frame_muscle, options['musclefreqex'], 4, 1, 'nsew')

    frame_muscle.grid(row=3, column=0, sticky='nw')
    frame_muscle.grid_columnconfigure(1, minsize=100)



    # ELECTRODE NOISE
    elecnoise = toggle(frame_elnoise, options['elecnoise'], 1, 1)

    tk.Label(frame_elnoise, text='Electrode noise threshold: ', background='white').grid(row=2, column=0, sticky='w')
    elecnoisethresh = textfield(frame_elnoise, options['elecnoisethresh'], 2, 1, 'nsew')

    frame_elnoise.grid(row=3, column=1, sticky='nw')
    frame_elnoise.grid_columnconfigure(1, minsize=100)


    def on_ok():

        global choices
        choices = {}

        choices['figsize'] = figsize.get()
        choices['plottimex'] = ast.literal_eval(plottimex.get())
        choices['plotfreqx'] = ast.literal_eval(plotfreqx.get())
        choices['freqscale'] = freqscale.get()

        choices['tmsmuscle'] = tmsmuscle.get()

        if comps.get().strip().isnumeric():
                choices['comps'] = ast.literal_eval(comps.get())

        choices['compcheck'] = compcheck.get()
        choices['threshfeedback'] = threshfeedback.get()
        choices['remove'] = remove.get()

        if tmsmuscle.get() == True:
            if tmsmusclethresh.get().strip().isnumeric():
                choices['tmsmusclethresh'] = ast.literal_eval(tmsmusclethresh.get())
            else:
                Warning('Input for the tms muscle threshold could not be evaluated. No threshold set.')

            choices['tmsmusclewin'] = ast.literal_eval(tmsmusclewin.get())

        choices['approach'] = approach.get()
        choices['g'] = g.get()

        choices['blink'] = blink.get()

        if blink.get() == True:
            if blinkthresh.get().strip().isnumeric():
                choices['blinkthresh'] = ast.literal_eval(blinkthresh.get())
            else:
                Warning('Input for the eyeblink threshold could not be evaluated. No threshold set.')

            choices['blinkelecs'] = [str.strip("[] ") for str in blinkelecs.get().split(",")]

        choices['move'] = move.get()

        if move.get() == True:
            if movethresh.get().strip().isnumeric():
                choices['movethresh'] = ast.literal_eval(movethresh.get())
            else:
                Warning('Input for the lateral eye movement threshold could not be evaluated. No threshold set.')

            choices['moveelecs'] = [str.strip("[] ") for str in moveelecs.get().split(",")]

        choices['muscle'] = muscle.get()
        
        if muscle.get() == True:
            if musclethresh.get().strip().isnumeric():
                choices['musclethresh'] = ast.literal_eval(musclethresh.get())
            else:
                Warning('Input for the persistent muscle activity threshold could not be evaluated. No threshold set.')

            if len(musclefreqin.get()) > 0:
                choices['musclefreqin'] = ast.literal_eval(musclefreqin.get())
            if len(musclefreqex.get()) > 0:
                choices['musclefreqex'] = ast.literal_eval(musclefreqex.get())

        choices['elecnoise'] = elecnoise.get()

        if elecnoise.get() == True:
            if elecnoisethresh.get().strip().isnumeric():
                choices['elecnoisethresh'] = float(elecnoisethresh.get())
            else:
                Warning('Input for the electrode noise threshold could not be evaluated. No threshold set.')

        win.destroy()

    def on_cancel():
        win.destroy()

    frame_button = tk.Frame(win, padx=10, pady=10, bg='white')
    frame_button.grid(row=4, column=1)

    cancelbutton = tk.Button(frame_button, bg='white', text='Cancel Changes', command=on_cancel)
    cancelbutton.grid(row=0, column=0, sticky='ne')
    okbutton = tk.Button(frame_button, bg='white', text='Ok', command=on_ok)
    okbutton.grid(row=0, column=1, sticky='ne')

    win.columnconfigure((0,1), weight=50)
    win.rowconfigure((0,1,2,3), weight=50)

    win.mainloop()

    try:
        for key, val in choices.items():

            if val == True:
                val = 'on'
            elif val == False:
                val = 'off'

            options[key] = val
    except:
        print('\nOptions not changed.')

    return options

