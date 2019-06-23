import bs
import random

class FlyBot(bs.Actor):

    def __init__(self, pos = (0,4,0), vel = (0,0,0)):
        bs.Actor.__init__(self)
        
        self.speedMul = 1.0
        self.hp = 100
        self.x, self.y, self.z = pos
        # Our 'base'
        self.touchedSound = bs.getSound('error')
        # DON'T TOUCH THE CHILD!!!!!1!!!1!!11!!
        self.tex1 = bs.getTexture('landMine')
        self.tex2 = bs.getTexture('landMineLit')

        self.node = bs.newNode('prop',
                               delegate = self,
                               attrs={
                                   'position':pos,
                                   'velocity':vel,
                                   'body':'sphere',
                                   'model':bs.getModel('bomb'),
                                   'shadowSize':0.3,
                                   'colorTexture':self.tex1,
                                   'materials':[bs.getSharedObject('objectMaterial')],
                                   'extraAcceleration':(0,20,0)})

        bs.gameTimer(1000, bs.Call(self._update), True)
        self.textureSequence = \
                bs.newNode('textureSequence', owner=self.node, attrs={
                    'rate':100,
                    'inputTextures':(self.tex1, self.tex2)})
        
        
    def _update(self):
        if not self.node.exists(): return
        xv, yv, zv = (0,20,0)

        if self.x < self.node.position[0]:
            xv -= 5 * self.speedMul
        if self.x > self.node.position[0]:
            xv += 5 * self.speedMul
        if self.y < self.node.position[1]:
            yv -= 5 * self.speedMul
        if self.y > self.node.position[1]:
            yv += 5 * self.speedMul 
        if self.z < self.node.position[2]:
            xv -= 5 * self.speedMul 
        if self.z > self.node.position[2]:
            zv += 5 * self.speedMul

        self.node.extraAcceleration = (xv, yv, zv)

    def handleMessage(self, m):
        if not self.node.exists(): return
        if isinstance(m, bs.OutOfBoundsMessage):
            self.node.delete()
        elif isinstance(m, bs.DieMessage):
            self.node.delete()

        # TODO - add functoional for speed-up on picked up
        elif isinstance(m, bs.PickedUpMessage):
            bs.Blast(position = self.node.position, blastType = 'impact',
                     blastRadius = 0.8).autoRetain()
            bs.playSound(self.touchedSound, position = self.node.position,
                         volume = 4)
            self.x, self.y, self.z = m.node.position
            # I SAID DON'T TOUCH!
            self.speedMul = 3.0
            self.hp -= 10 + random.randint(-3,3)
            if self.hp < 0:
                bs.Blast(position = self.node.position, blastRadius = 0.5,
                         blastType = 'tnt')
                self.handleMessage(bs.DieMessage())
        elif isinstance(m, bs.DroppedMessage):
            self.speedMul = 1.0
        else:
            bs.Actor.handleMessage(self, m)

