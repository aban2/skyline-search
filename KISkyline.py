import torch
from utils import dominate
from loader import load_data
from collections import deque

class Bucket:
    def __init__(self):
        self.timeline = deque()
        self.candidate_points = []
        self.master2slave = {}
        self.holes = deque()
    
    def add_points(self, point):
        self.timeline.append(point)
        for id in range(len(self.candidate_points)):
            candidate_point = candidate_points[id]
            domination = dominate(candidate_point, point)
            if domination == 1:
                self.master2slave[id].append(point)
            elif domination == -1:
                self.master2slave[id].append(candidate_point)
                self.candidate_points[id] = point

        # add new candidate points
        if len(self.holes) == 0:
            self.master2slave[len(self.candidate_points)] = []
            self.candidate_points.append(point)
        else:
            idx = self.holes[0]
            self.holes.popleft()
            self.master2slave[idx] = []
            self.candidate_points[idx] = point

    def pop_points(self):
        top = self.timeline[0]
        if top in self.candidate_points:
            idx = self.candidate_points.index(top)
            self.holes.append(idx)
            for point in self.master2slave[idx]:
                self.add_points(point)
        self.timeline.popleft()

class KISkyline:
    def __init__(self, args):
        self.args = args
        self.data = load_data(args)
        self.bucket = {}

    def run(self):
        for i in range(len(self.data)):
            new_point = self.data[i]

            # get the bitmap
            isnan = torch.isnan(new_point)
            bit_map = ''
            for idx, ele in enumerate(isnan):
                bit_map += '0' if ele else '1'
            if bit_map not in self.bucket:
                self.bucket[bit_map] = Bucket()
            
            # local skyline insertion
            self.bucket[bit_map].add_points(new_point)
            
            break