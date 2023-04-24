#!/usr/bin/python
# -*- coding: utf-8 -*-
import os


sample_period = 0.01 #total sampling in seconds per sample
sample_collection = 100 #how many samples

os.system('mkdir perfdata')

for i in range(sample_collection):
	os.system('sudo perf record -F 999 -ag -o perfdata/perf'+str(i)+'.data sleep '+str(sample_period))
	os.system('sudo chmod 777 perfdata/perf'+str(i)+'.data')



for i in range(sample_collection):
	os.system('sudo perf report -i perfdata/perf'+str(i)+'.data --stdio -q -g folded > perfdata/perf'+str(i)+'.txt')
	os.system('sudo chmod 777 perfdata/perf'+str(i)+'.txt')
	os.system('sudo rm perfdata/perf'+str(i)+'.data')
	print(str(int(100*i/(sample_collection-1)))+"% done")

print("All complete!")

