class Agent:
    def __init__(self,name,sojourn,time):
        self.name = name
        self.sojourn = sojourn
        self.exitTime = time+self.sojourn
        return

    