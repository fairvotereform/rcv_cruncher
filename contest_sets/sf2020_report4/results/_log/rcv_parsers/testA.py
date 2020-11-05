
import inspect
import pickle

class B:
    def g(self):
        print("B")

class A(B):
    def p(self):
        print("A")

    def c(self):
        pass

x = str(inspect.getsource(A))

f = open("A", 'wb')
pickle.dump(x, f)
f.close()
