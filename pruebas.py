class outer_class:
    s = set()
    def __init__(self):
        self.s = {0,12,3}

    class class_1:
        def __init__(self):
            self.something = outer_class.s
            print(self.something)

