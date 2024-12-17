import math

remainder = 21660 % 4
print(remainder)

def splitList(l,n):
    remainder = l % n
    if remainder == 0:
        return int(l/n)
    else:
        return int(math.ceil(l/n))
    
print(splitList(21660,4))
print(splitList(21661,4))
print(splitList(21664,4))
