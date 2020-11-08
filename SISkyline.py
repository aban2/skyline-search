
class SISkyline():
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
                self.bucket[bit_map] = new_point.view(1,-1)

            # if bitmap in bucket, process
            else:
                # local skyline insertion
                tensor = self.bucket[bit_map]
                # self.bucket[bit_map] = torch.vstack((tensor, new_point))