import torch
import copy
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
        # delete slaves
        deleted_slaves = []
        for slave in self.slaves:
            domination = dominate(slave, point)
            if domination < 0:
                deleted_slaves.append(slave)
        for slave in deleted_slaves:
            del self.slaves[slave]

        # process candidate
        for candidate_point in self.master2slaves:
            domination = dominate(candidate_point, point)
            if domination == 1:
                self.master2slaves[candidate_point].append(point)
                self.slaves[point] = 1
                return
            elif domination == -1:
                del self.master2slaves[candidate_point]
                self.master2slaves[point] = []
                return

        # add new candidate points
        self.master2slaves[point] = []

    def pop_points(self, old_point):
        if old_point in self.master2slaves:
            self.delete_candidate_point(old_point)
        elif old_point in self.slaves:
            del self.slaves[old_point]


class KISkyline:
    def __init__(self, args):
        self.args = args
        self.timeline = deque()
        self.data = load_data(args)
        self.bucket = {}
        self.topo_graph = {}            # is dominated, can find global using dfs
        self.reverse_topo_graph = {}    # dominate, used to find fathers

    def run(self):
        start_time, total_time = time(), 0
        for ct in range(len(self.data)):
            # record new point, init
            new_point = self.data[ct]
            self.timeline.append(new_point)

            # if windows full, pop a point
            if self.get_current_items() >= self.args.window_size:
                while True:
                    old_point = self.timeline[0]
                    self.timeline.popleft()
                    old_bitmap = get_bitmap(old_point)
                    self.bucket[old_bitmap].pop_points(old_point)
                    if self.get_current_items() < self.args.window_size:
                        break

            # get all candidates, num_slaves
            all_candidates, num_slaves = [], 0
            for bitmap in self.bucket:
                num_slaves += len(self.bucket[bitmap].slaves)
                for candidate_point in self.bucket[bitmap].master2slaves:
                    all_candidates.append(candidate_point)
    
            # do local skyline insertion
            new_bitmap = get_bitmap(new_point)
            if new_bitmap not in self.bucket:
                self.bucket[new_bitmap] = Bucket()
            is_candidate = self.bucket[new_bitmap].judge(new_point)
            if is_candidate:
                # complete graph for the new point
                for i in range(len(all_candidates)):
                    domination = dominate(all_candidates[i], new_point)
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
            self.bucket[new_bitmap].add_points(new_point)
            
            # update global skyline points
            self.update_graph(all_candidates)
            global_skyline_points = {}
            for candidate in all_candidates:
                self.dfs(candidate, {}, global_skyline_points)
            
            if (ct+1) % self.args.print_step == 0:
                ct_time = time()-start_time
                total_time += ct_time
                print('step', ct+1, 'num_global', len(global_skyline_points), 'node', \
                    len(self.topo_graph), 'candidates', len(all_candidates), 'slaves', num_slaves, 'time', '%.2f' % float(ct_time))
                # print(all_candidates)
                start_time = time()        
        print('total time: %.2f' % float(total_time))
        print()
    
    def get_current_items(self):
        # count current items
        current_items = 0
        for bitmap in self.bucket:
            current_items += len(self.bucket[bitmap].slaves)
            current_items += len(self.bucket[bitmap].master2slaves)
        return current_items
    
    def update_graph(self, all_candidates):
        # list2dir
        candidates_dict = {}
        for candidate in all_candidates:
            candidates_dict[candidate] = 1
        
        # clear
        deleted_nodes = {}
        for node in self.topo_graph:
            if node not in candidates_dict:
                deleted_nodes[node] = 1
        for node in self.reverse_topo_graph:
            if node not in candidates_dict:
                deleted_nodes[node] = 1
        for node in deleted_nodes:
            self.delete_graph_dependencies(node)
    
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