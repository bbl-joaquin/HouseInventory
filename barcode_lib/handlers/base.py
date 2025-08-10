class ModeBase:
    def __init__(self, reader): self.reader=reader
    def prompt(self):
        name=self.__class__.__name__.replace('Mode','').lower()
        return f'[{name}] Scan code: '
