import argparse
from KISkyline import KISkyline
from SISkyline import SISkyline

def _init(parser):
    parser.add_argument('-algorithm', action='store')
    parser.add_argument('-window_size', type=int, action='store')
    parser.add_argument('-missing_rate', type=float, action='store')
    parser.add_argument('-num_samples', type=int, action='store')
    parser.add_argument('-num_attrs', type=int, action='store')

if __name__ == '__main__':
    # parse args
    parser = argparse.ArgumentParser()
    _init(parser)
    args = parser.parse_args()

    # enter main process
    if args.algorithm == 'KISkyline':
        model = KISkyline(args)
    elif args.algorithm == 'SISkyline':
        model = SISkyline(args)
    else:
        raise Exception('model name must be KISkyline or SISkyline')

    # run model
    model.run()