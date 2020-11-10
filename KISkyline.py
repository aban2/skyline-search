import torch
from time import time
from loader import load_data
from collections import deque
from utils import dominate, get_bitmap

class Bucket:
    def __init__(self):
        self.master2slaves = {}
        self.slaves = {}
    
    def judge(self, point):
        for candidate_point in self.master2slaves:
            domination = dominate(candidate_point, point)
            if domination == 1:
                return 0
            elif domination == -1:
                return 1
        return 1
    
    def delete_candidate_point(self, candidate_point):
        slaves = self.master2slaves[candidate_point]
        del self.master2slaves[candidate_point]
        for slave in slaves:
            if slave in self.slaves:
                self.add_points(slave)

    def add_points(self, point):
        for candidate_point in self.master2slaves:
            domination = dominate(candidate_point, point)
            if domination == 1:
                self.master2slaves[candidate_point].append(point)
                self.slaves[point] = 1
                return
            elif domination == -1:
                self.delete_candidate_point(candidate_point)
                self.master2slaves[point] = []
                return

        # add new candidate points
        self.master2slaves[point] = []

    def pop_points(self, old_point):
        if old_point in self.master2slaves:
            self.delete_candidate_point(old_point)
        elif old_point in self.slaves:
            del self.slaves[old_point]
        else:
            return 0
        return 1


class KISkyline:
    def __init__(self, args):
        self.args = args
        self.timeline = deque()
        self.data = load_data(args)
        self.bucket = {}
        self.topo_graph = {}            # is dominated, can find global using dfs
        self.reverse_topo_graph = {}    # dominate, used to find fathers

    def run(self):
        start_time = time()
        current_items = 0
        for ct in range(len(self.data)):
            # record new point, init
            new_point = self.data[ct]
            self.timeline.append(new_point)

            # if windows full, pop a point
            if self.get_current_items() >= self.args.window_size:
                while True:
                    current_items -= 1
                    old_point = self.timeline[0]
                    self.timeline.popleft()
                    old_bitmap = get_bitmap(old_point)
                    result = self.bucket[old_bitmap].pop_points(old_point)
                    is_candidate = self.bucket[bitmap].judge(old_point)
                    if is_candidate:
                        self.delete_graph_dependencies(old_point)
                    if result > 0 and self.get_current_items() < self.args.window_size:
                        break

            # get all candidates
            all_candidates = []
            for bitmap in self.bucket:
                for candidate_point in self.bucket[bitmap].master2slaves:
                    all_candidates.append(candidate_point)
    
            # do local skyline insertion
            bitmap = get_bitmap(new_point)
            if bitmap not in self.bucket:
                self.bucket[bitmap] = Bucket()
            is_candidate = self.bucket[bitmap].judge(new_point)
            if is_candidate:
                # complete graph for the new point
                for i in range(len(all_candidates)):
                    domination = dominate(all_candidates[i], new_point)
                    # print(all_candidates[i], new_point, domination)
                    if domination == 1:
                        father, son = all_candidates[i], new_point
                    elif domination == -1:
                        father, son = new_point, all_candidates[i]
                    else:
                        continue

                    # add nodes, edges in graph    
                    if son in self.topo_graph:
                        self.topo_graph[son][father] = 1
                    else:
                        self.topo_graph[son] = {father:1}
                    if father in self.reverse_topo_graph:
                        self.reverse_topo_graph[father][son] = 1
                    else:
                        self.reverse_topo_graph[father] = {son:1}
                
                # init situation
                if len(all_candidates) == 0:
                    all_candidates.append(new_point)

            # add the new point
            self.bucket[bitmap].add_points(new_point)
            
            # update global skyline points
            global_skyline_points = {}
            for candidate in all_candidates:
                if candidate != None:
                    self.dfs(candidate, {}, global_skyline_points)
            
            if (ct+1) % self.args.print_step == 0:
                print('step', ct+1, 'num_global', len(global_skyline_points), \
                    'num_candidate', len(self.topo_graph), len(all_candidates), 'time', '%.2f' % float(time()-start_time))
                start_time = time()
    
    def get_current_items(self):
        # count current items
        current_items = 0
        for bitmap in self.bucket:
            current_items += len(self.bucket[bitmap].slaves)
            current_items += len(self.bucket[bitmap].master2slaves)
        return current_items
    
    def delete_graph_dependencies(self, point):
        if point in self.topo_graph:
            for father in self.topo_graph[point]:
                del self.reverse_topo_graph[father][point]
            del self.topo_graph[point]
        if point in self.reverse_topo_graph:
            for father in self.reverse_topo_graph[point]:
                del self.topo_graph[father][point]
            del self.reverse_topo_graph[point]

    def dfs(self, node, traversed, global_skyline_points):
        if node in traversed:
            return
        # print(node)
        traversed[node] = 1
        if node not in self.topo_graph:
            if node not in global_skyline_points:
                global_skyline_points[node] = 1
            return
        for hop in self.topo_graph[node]:
            self.dfs(hop, traversed, global_skyline_points)