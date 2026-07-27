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
    pl1 = Platform(750, 710)
    pl2 = Platform(1400, 710)
    pl3 = Platform(100, 710)
    pl4 = Platform(400, 650)
    pl5 = Platform(1100, 650)
    return [pl1, pl2, pl3, pl4, pl5]