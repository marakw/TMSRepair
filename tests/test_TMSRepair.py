import unittest
import pickle
import numpy as np
import sys
sys.path.append('../TMSRepair')

from TMSRepair.TMSRepair_class import TMSRepair


class TestTMSRepair(unittest.TestCase):

    def setUp(self):
        with open('tests/testdata/example_epochs.p', 'rb') as file:
            epochs = pickle.load(file)
        self.inst1 = TMSRepair(epochs, options={'manualinput':'off'})



    def tearDown(self):
        pass



    def test_set_options(self):
        self.inst1.set_options(options={'elecnoise':'off'})
        assert self.inst1.options['elecnoise'] == 'off'



    def test_replace_with_zeros(self):
        orig_datashape = np.shape(self.inst1.epochs)
        self.inst1.replace_with_zeros([self.inst1.epochs.times[0]*1000, self.inst1.epochs.times[-1]*1000])

        assert np.sum(self.inst1.epochs._data) == 0
        assert np.shape(self.inst1.epochs) == orig_datashape



    def test_cubic_interpolation(self):
        from copy import copy

        window = [-20,20]
        
        x = self.inst1.epochs.times
        idx1 = np.argmin(np.abs(x - window[0]*0.001))
        idx2 = np.argmin(np.abs(x - window[1]*0.001)) +1

        orig_data = copy(self.inst1.epochs._data[:,:,idx1:idx2])
        self.inst1.cubic_interpolation([-20, 20])

        with self.assertRaises(AssertionError):
            np.testing.assert_array_equal(  self.inst1.epochs._data[:,:,idx1:idx2], 
                                            orig_data)



    def test_fastica(self):
        from scipy import signal

        # example signal from sklearn ICA
        # Generate sample data
        np.random.seed(0)
        n_samples = 2000
        time = np.linspace(0, 8, n_samples)

        s1 = np.sin(2 * time)  # Signal 1 : sinusoidal signal
        s2 = np.sign(np.sin(3 * time))  # Signal 2 : square signal
        s3 = signal.sawtooth(2 * np.pi * time)  # Signal 3: saw tooth signal

        S = np.c_[s1, s2, s3]
        S += 0.2 * np.random.normal(size=S.shape)  # Add noise

        S /= S.std(axis=0)  # Standardize data
        # Mix data
        A = np.array([[1, 1, 1], [0.5, 2, 1.0], [1.5, 1.0, 2.0]])  # Mixing matrix
        X = np.dot(S, A.T)  # Generate observations

        # pretend that artificial signal are three channels in the epochs object
        self.inst1.epochs._data = np.transpose(X)[None, :,:]
        self.inst1.options['chanpicks'] = ['Fp1', 'Fp2', 'F3']

        # call fast ICA function
        self.inst1.fastica()

        # reconstruct signal
        ncomps, _, _ = np.shape(self.inst1.S)
        S_concat = np.reshape(self.inst1.S, [ncomps, -1])
        post = np.dot(S_concat.T, self.inst1.A.T)
        post += self.inst1.mean

        # assert original and reconstructed signal are almost equal
        np.testing.assert_array_almost_equal(post, X)



    def test_compselect(self):
        self.inst1.options['confirm'] = 'off'
        self.inst1.options['compcheck'] = 'off'
        self.inst1.options['move'] = 'off'
        self.inst1.options['blink'] = 'off'
        self.inst1.options['muscle'] = 'off'

        self.inst1.options['tmsmuscle'] = 'on'
        self.inst1.options['elecnoise'] = 'on'

        # make threshold for electrode noise high
        self.inst1.options['elecnoisethresh'] = 7
        self.inst1.options['tmsmusclethresh'] = 10
        self.inst1.options['tmsmusclewin'] = [10,20]

        # make signal of first channel 100 times higher than average amp
        meanamp = np.mean(self.inst1.epochs._data)
        self.inst1.epochs._data[:, 0, :] = self.inst1.epochs._data[:, 0, :] + meanamp*100

        # make signal of second channel really high in the time window for tms muscle threshold
        tp = np.argmin(np.abs(self.inst1.epochs.times*1000
                      -self.inst1.options['tmsmusclewin'][0]))

        self.inst1.epochs._data[:,1, tp] = self.inst1.epochs._data[:,1, tp] + meanamp*1000

        self.inst1.fastica()
        self.inst1.compselect()

        # see whether at least one component captures a high amplitude in tms muscle window and the noisy channel
        self.assertIn( [6.0], self.inst1.compclass)
        self.assertIn( [2.0], self.inst1.compclass)



if __name__ == '__main__':
    unittest.main()