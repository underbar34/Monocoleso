# platforms.py
class Platform:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.shir = 105
    
    def pup(self, px, py, ground_y):
        if self.x - 50 <= px <= self.x + self.shir and self.y - 50 > py > self.y - 100:
            return self.y - 70
        else:
            return ground_y

def create_platforms():
    from platforms import Platform
    pl1 = Platform(450, 510)
    pl2 = Platform(900, 510)
    pl3 = Platform(10, 510)
    pl4 = Platform(200, 450)
    pl5 = Platform(700, 450)
    return [pl1, pl2, pl3, pl4, pl5]