import csv
l=[[idx,i,'hi'] for idx,i in enumerate(range(1,1000000))]

with open('someFile.csv','w') as f:
    writer = csv.writer(f,delimiter='\t',lineterminator='\n')
    writer.writerows(l)
    
    # for j in l:
    #     writer.writerow(j)

inc = 9999
start = 0

with open('someFile.csv') as f:
    # read = csv.reader(f)
    # read
    i = [i for i in csv.reader(f)]
    while inc < len(i):
        #incrementally write to csv
        with open('someBatchFile.csv','w') as bf: 
            writer = csv.writer(bf,delimiter='\t',lineterminator='\n')
            writer.writerows(i[start:inc])
            # do sql stuff here
            start+=inc
            inc+=inc
    

# end = inc

while inc < len(i):
    i[start:inc]
    start+=inc
    inc+=inc
""