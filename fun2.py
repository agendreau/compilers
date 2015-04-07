def even(x):
    return True if x == 0 else odd(x + -1)

def odd(x):
    return True if x == 1 else even(x + -1)

print odd(7)
print even(10)
print odd(11)
print even(0)
print odd(1)

