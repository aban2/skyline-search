import pandas as pd
import numpy as np
import torch

def load_data(args):
    data = pd.read_csv('data/train/FeatureVectorWithLabel.csv')
    des = data.describe()

    no_use_attrs = ['enrollment_id', 'label']
    attrs = []

    for i in des:
        if i in no_use_attrs:
            continue
        if des[i]['min'] != des[i]['max']:
            attrs.append(i)

    df = data[attrs]
    data = df.values[0:args.num_samples][:,0:args.num_attrs]

    # numpy random drop values
    torch.manual_seed(2233)
    num_row, num_col = data.shape
    for i in range(num_row):
        for j in range(num_col):
            a = torch.rand(1)*100
            if a.item() < args.missing_rate*100:
                data[i][j] = None

    return torch.tensor(data, dtype=torch.float16)