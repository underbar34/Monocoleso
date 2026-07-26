import pygame
import random
pygame.init()

# Код, описывающий окно программы
WIDTH = 1560  # Ширина окна
HEIGHT = 800  # Высота окна
screen = pygame.display.set_mode((WIDTH, HEIGHT))

# Создаём контроль FPS
clock = pygame.time.Clock()
FPS = 30  # Устанавливаем нужное значение FPS

# Игровые переменные, если надо, описываем в этом блоке
player=pygame.image.load("Tems(stoit1).png")
playerx=300
playery=200
y_vel=0
y_veling=0
opuskatsa=0
isjump=False
mognovnis=False
graviti=1.3
timer=0
otpuskal=True
ground_y=526
playermovex=0
playermovey=0
speedplaer=5
speedplaery=10
health=4
healthmax=5
neuyazvimost=0
neuyazvimostmax=30
atakapl=False
flagatak=0
vrematakpl=0
atakax=-1000
gizn=pygame.image.load("gizn.png")
nogizn=pygame.image.load("giznmax.png")

giznx=100
gizny=2
akumpower=5
maxakumpower=5
akum=pygame.image.load("akum0.png")
akum0=pygame.image.load("akum0.png")
akum1=pygame.image.load("akum1.png")
akum2=pygame.image.load("akum2.png")
akum3=pygame.image.load("akum3.png")
akum4=pygame.image.load("akum4.png")
akum5=pygame.image.load("akum5.png")
playeridet1=pygame.image.load("Tems(idet1).png")
playeridet2=pygame.image.load("Tems(idet2).png")
playerataka1=pygame.image.load("ataka1tems.png")
playerataka2=pygame.image.load("ataka2tems.png")
playerataka3=pygame.image.load("ataka3tems.png")
playerataka4=pygame.image.load("ataka4tems.png")
playerataka5=pygame.image.load("ataka5tems.png")
playerataka6=pygame.image.load("ataka6tems.png")
playerataka7=pygame.image.load("ataka7tems.png")
playerataka8=pygame.image.load("ataka8tems.png")
playerstoit1=pygame.image.load("Tems(stoit1).png")
playerstoit2=pygame.image.load("Tems(stoit2).png")
platform=pygame.image.load("platform.png")
class platforms:
    def __init__(self,x,y):
        self.x=x
        self.y=y
        self.shir=105
    def pup(self,px,py,gr):
        if self.x-50<=px<=self.x+self.shir and self.y-50>py>self.y-100:
            return self.y-70
        else:
            return 526
pl1=platforms(450,510)
pl2=platforms(900,510)
pl3=platforms(10,510)
pl4=platforms(200,450)
pl5=platforms(700,450)

pls=[pl1,pl2,pl3,pl4,pl5]
# Игровой цикл и флаг выполнения программы
game_run = True
while game_run:
    # БЛОК ОБРАБОТКИ СОБЫТИЙ ИГРЫ
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_run = False
        if event.type==pygame.KEYDOWN:
            
            if event.key==pygame.K_s and  otpuskal and playermovey==0:
                playery+=40
                
            if event.key==pygame.K_w and not atakapl:
                atakapl=True
            if event.key==pygame.K_e and akumpower==maxakumpower:
                akumpower=0
                if health<=healthmax:
                    health+=1
    if akumpower==0:
        akum=akum0
    elif akumpower==1:
        akum=akum1
    elif akumpower==2:
        akum=akum2
    elif akumpower==3:
        akum=akum3
    elif akumpower==4:
        akum=akum4
    elif akumpower==5:
        akum=akum5
                
    e=True
    n=0
    while e:
        ground_y=pls[n].pup(playerx,playery,ground_y)
        if ground_y==526:
            n+=1
            if n>len(pls)-1:
                e=False
        else:
            e=False
    
    
            
            
    
             
    # БЛОК ИГРОВОЙ ЛОГИКИ (обновление переменных)
    keys=pygame.key.get_pressed()
    playermovex=keys[pygame.K_d]-keys[pygame.K_a]
    playerx+=playermovex*speedplaer
    if playermovex==1:
        player=playeridet1
        if atakapl:
            flagatak=1
      
    if playermovex==-1:
        player=playeridet2
        if atakapl:
            flagatak=2
    if playermovex==0:
        if player==playeridet1 or player==playerstoit1:
            player=playerstoit1
            if atakapl:
                flagatak=1
        elif player==playeridet2 or player==playerstoit2: 
            player=playerstoit2
            if atakapl:
                flagatak=2
    if keys[pygame.K_SPACE]==1 and timer==0 and playery==ground_y and playermovey<0.1:
        timer+=1
        otpuskal=False
        playermovey=-2
    if timer!=0 and timer!=-15 and keys[pygame.K_SPACE]==1 and timer<=15 and otpuskal==False and playermovey<0.1:
        timer+=1
        playermovey+=0.1
        
    if timer>15 and playery<=ground_y or keys[pygame.K_SPACE]!=1 and playery<=ground_y:
        timer=-15
        
        playermovey=1
        
        
        playermovey+=0.1
        otpuskal=True
    if timer==-15 and playery>=ground_y:
        playermovey=0
        playery=ground_y
        timer=0
        opuskatsa=0
    if playery<ground_y and playermovey==0 and keys[pygame.K_SPACE]==1:
        playermovey=0.7
    if playery>ground_y:
        playery=ground_y
        playermovey=0
    
    playery+=playermovey*speedplaery
    
        

    # БЛОК ОТРИСОВКИ ОБЪЕКТОВ В ОКНЕ ПРОГРАММЫ

    screen.fill([255,255,255])
    for i in pls:
        screen.blit(platform,(i.x,i.y))
    screen.blit(player,(playerx,playery))
    for i in range(health):
        screen.blit(gizn,(giznx,gizny))
        giznx+=40
    for i in range(healthmax-health):
        screen.blit(nogizn,(giznx,gizny))
        giznx+=40
    giznx=50
    if flagatak==1 and vrematakpl<=5:
        atakax=playerx+30
        screen.blit(playerataka1,(atakax,playery-10))
        vrematakpl+=1
    elif flagatak==2 and vrematakpl<=5:
        atakax=playerx-30
        screen.blit(playerataka2,(atakax,playery-10))
        vrematakpl+=1
    else:
        atakapl=False
        flagatak=0
        vrematakpl=0
    neuyazvimost+=1
    
    screen.blit(akum,(0,2))
    pygame.display.flip()  # Отображение нарисованных объектов
    clock.tick(FPS)  # Контроль FPS
pygame.quit()