import unittest
from stream.mutate import *

class MockCommand:
    operand_list = None
    cmd = None
    def __init__(self, cmd, *operand_list):
        self.cmd = cmd
        self.operand_list = list(operand_list)
    def copy(self):
        return MockCommand(self.cmd, *self.operand_list)
    def __hash__(self):
        return (self.cmd, tuple(self.operand_list)).__hash__()
    def __repr__(self):
        return self.cmd + " " + " ".join(self.operand_list)
    def __eq__(self, other):
        return self.cmd == other.cmd and self.operand_list == other.operand_list

class TestMutate(unittest.TestCase):
    def test_swap(self):
        self.assertEqual(set(map(tuple, mutator_swap(['cat', 'grep']))),
                         {('grep', 'cat')})
        self.assertEqual(set(map(tuple, mutator_swap(['cat', 'grep', 'sort']))),
                         {('grep', 'cat', 'sort'),
                          ('cat', 'sort', 'grep')})
        self.assertEqual(set(map(tuple, mutator_swap(['cat', 'grep', 'tr', 'sort']))),
                         {('grep', 'cat', 'tr', 'sort'),
                          ('cat', 'tr', 'grep', 'sort'),
                          ('cat', 'grep', 'sort', 'tr')})

    def test_drop(self):
        self.assertEqual(set(map(tuple, mutator_drop(['cat', 'grep']))),
                         {('cat',),
                          ('grep',)})
        self.assertEqual(set(map(tuple, mutator_drop(['cat', 'grep', 'sort']))),
                         {('grep', 'sort'),
                          ('cat', 'sort'),
                          ('cat', 'grep')})

    def test_arg_drop(self):
        self.assertEqual(set(map(tuple, mutator_arg_drop([MockCommand('cat', 'a.txt'),
                                                          MockCommand('grep', '-E', '[A-Z]+')]))),
                         {(MockCommand('cat'),
                           MockCommand('grep', '-E', '[A-Z]+')),
                          (MockCommand('cat', 'a.txt'),
                           MockCommand('grep', '[A-Z]+')),
                          (MockCommand('cat', 'a.txt'),
                           MockCommand('grep', '-E'))})

if __name__ == '__main__':
    unittest.main()
