def sum(n):
    return n + sum(n+-1) if n!=0 else 0

print sum(1)
