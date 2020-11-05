
import inspect
import pickle

y = pickle.load(open("A", "rb"))

class A:
    def p(self):
        print("AA")

x = inspect.getsource(A)

print(y)
print(x)
print(x == y)
