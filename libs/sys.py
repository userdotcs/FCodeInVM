def write(obj):
    print(obj, end="")

def writeLn(obj):
    print(obj)

def readLn(q):
    return input(q)

funcs = {
    "w": write,
    "wL": writeLn,
    "rL": readLn
}