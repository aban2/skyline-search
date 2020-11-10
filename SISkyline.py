import torch
import copy
from time import time
from loader import load_data
from collections import deque
from utils import dominate, get_bitmap
from KISkyline import Bucket, KISkyline

class SISkyline(KISkyline):
    def __init__(self, args):
        super(SISkyline, self).__init__(args)
        self.virtual2shadows = {}
        self.shadow2virtuals = {}

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

                # update virtual, shadows after deletion
                self.update_virtual_shadow()

            # get all candidates, num_slaves
            all_candidates, num_slaves = [], 0
            for bitmap in self.bucket:
                num_slaves += len(self.bucket[bitmap].slaves)
                for candidate_point in self.bucket[bitmap].master2slaves:
                    if candidate_point not in self.shadow2virtuals:
                        all_candidates.append(candidate_point)
            
            # do local skyline insertion
            new_bitmap = get_bitmap(new_point)
            if new_bitmap not in self.bucket:
                self.bucket[new_bitmap] = Bucket()

            is_candidate = self.bucket[new_bitmap].judge(new_point)
            if is_candidate:
                # if not controlled by virtual point, insert to graph
                is_controlled = 0
                for candidate_point in all_candidates:
                    domination = dominate(candidate_point, new_point)
                    if domination == 1:
                        is_controlled = 1
                        # add virtual point and shadow point
                        if candidate_point not in self.virtual2shadows:
                            self.virtual2shadows[candidate_point] = {new_point:1}
                        else:
                            self.virtual2shadows[candidate_point][new_point] = 1
                        if new_point not in self.shadow2virtuals:
                            self.shadow2virtuals[new_point] = {candidate_point:1}
                        else:
                            self.shadow2virtuals[new_point][candidate_point] = 1
                
                if is_controlled == 0:
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
                        
                        # update virtual, shadow
                        if son in self.shadow2virtuals:
                            self.shadow2virtuals[son][father] = 1
                        else:
                            self.shadow2virtuals[son] = {father:1}
                        if father in self.virtual2shadows:
                            self.virtual2shadows[father][son] = 1
                        else:
                            self.virtual2shadows[father] = {son:1}
                
                # init situation
                if len(all_candidates) == 0:
                    all_candidates.append(new_point)

            # add the new point
            self.bucket[new_bitmap].add_points(new_point)

            # update virtual, shadows after insertion
            self.update_virtual_shadow()
            
            # update global skyline points
            self.update_graph(all_candidates)
            global_skyline_points = {}
            for candidate in all_candidates:
                if candidate not in self.shadow2virtuals:
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

    def update_virtual_shadow(self):
        all_candidates = {}
        for bitmap in self.bucket:
            for candidate in self.bucket[bitmap].master2slaves:
                all_candidates[candidate] = 1
        
        deleted_virtuals = []
        for virtual_point in self.virtual2shadows:
            if virtual_point not in all_candidates:
                deleted_virtuals.append(virtual_point)
        
        for virtual_point in deleted_virtuals:
            for shadow in self.virtual2shadows[virtual_point]:
                if shadow in self.shadow2virtuals:
                    if virtual_point in self.shadow2virtuals[shadow]:
                        del self.shadow2virtuals[shadow][virtual_point]
                    if len(self.shadow2virtuals[shadow]) == 0:
                        del self.shadow2virtuals[shadow]