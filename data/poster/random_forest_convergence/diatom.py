#!/bin/python

s = 'total.dat'
f1 = 'entropy.dat'
f2 = 'gini.dat'
f3 = 'deviance.dat'
f4 = 'exponential.dat'

total = open(s);
f1o = open(f1, 'w');
f2o = open(f2, 'w');
f3o = open(f3, 'w');
f4o = open(f4, 'w');
files = [f1o, f2o, f3o, f4o];
ind = 0;
for line in total:
    files[ind % 4].write(line);
    ind += 1;

f1o.close()
f2o.close()
f3o.close()
f4o.close()
total.close()
