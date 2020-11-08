import torch
from loader import load_data
class BaseSkyline:
    def __init__(self, args):
        self.args = args
        self.data = load_data(args)
        self.bucket = {}

    def dominate(self, a, b):
        for i in a:
            