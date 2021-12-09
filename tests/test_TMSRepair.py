import unittest
import pickle
import TMSRepair.TMSRepair_class

class TestTMSRepair(unittest.TestCase):

    def setUp(self):

        with open('tests/testdata/example_epochs.p', 'rb') as file:
            epochs = pickle.load(file)
        self.inst1 = TMSRepair(epochs)

    def tearDown(self):
        pass

    def test_set_options(self):
        pass


if __name__ == '__main__':
    unittest.main()