from setuptools import setup
setup(
    name='TMSRepair',
    version='0.0.1',
    description='MNE extension for repairing TMS-evoked artifacts in EEG data',
    long_description='MNE extension for repairing TMS-evoked artifacts in epochs-objects with Independent Component Analysis',
    author='Mara Wolter',
    author_email='mara.k.wolter@gmail.com',
    url='https://github.com/marakw/TMSRepair.git',
    download_url='https://github.com/marakw/TMSRepair.git',
    license='MIT',
    packages=['TMSRepair'],
    install_requires=[
        'numpy',
        'pickle',
        'matplotlib',
        'mne',
        'tkinter',
        'skipy',
        'sklearn',
        'copy',
        'unittest',
        'sys',
        'ast'
        ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering :: Bio-Informatics'
        ]
    )