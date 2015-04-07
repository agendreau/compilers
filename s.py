def rec(n):
	return 1+rec(n+-1) if n!=0 else 0

print rec(2)
