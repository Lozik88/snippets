import os
cwd = os.path.dirname(__file__)
ifile = os.path.join(cwd,'input.txt')
ofile = os.path.join(cwd,'output.txt')
with open(ifile,'r') as f:
    text = f.read()

# splitting out to list, appending line numbers
line_nums = [str(idx+1)+'.) '+v for idx, v in enumerate(text.splitlines())]
# making a single string of text
lines_txt = '\n'.join(line_nums)
# find single string match
index_match = [idx for idx,v in enumerate(line_nums) if 'samp' in v.lower()]
value_match = [line_nums[v] for v in index_match]

# Find multiline match
search_list = ['samp','thi']
multi_match=[]
for idx,v in enumerate(text.splitlines()):
    for sv in search_list:
        if sv.lower() in v.lower():
            # print(idx,' - ',v)
            multi_match.append(idx)

line_nums = [line_nums[v] for v in multi_match]
lines_txt = '\n'.join(line_nums)

with open(ofile,'w') as f:
    f.write(lines_txt)