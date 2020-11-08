import torch

# should input by time order, first come first in
def dominate(a, b):
    adb, bda = 1, 1
    for i in range(a.shape[0]):
        if torch.isnan(a[i]) or torch.isnan(b[i]):
            continue
        if a[i] > b[i]:
            bda = 0
        if b[i] > a[i]:
            adb = 0
    if bda == 1:
        return -1
    elif abd == 1:
        return 1
    else:
        return 0