def less_than(x, y):
    return False if y == 0 else (True if x == 0 else less_than(x + -1, y + -1))

def div(x, y):
    return 0 if less_than(x, y) else 1 + div(x + -y, y)

print div(12, 3)
