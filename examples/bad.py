import os, pickle

def load(data, cache={}):
    x = eval(data)
    os.system("ls " + data)
    pickle.loads(data)
    f = open("/etc/passwd")
    try:
        y = data["key"]
    except:
        pass
    if x == None:
        return cache
