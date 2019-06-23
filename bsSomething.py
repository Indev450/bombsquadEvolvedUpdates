from random import randint

import bs

class Something(bs.Actor): # TODO - give normal name)
    '''
    Just try do any object without bs.Bomb
'''
    def __init__(self, position=(0, 1, 0), velocity=(0,0,0), deathTimeout = (False, 0)):
        bs.Actor.__init__(self)
        activity = self.getActivity()
        self.rType=randint(0,2)
        self.color=self.getColor(self.rType)
        self.material=self.getMaterial(self.rType)
        self.bodyNode = bs.newNode(
            'prop',
            delegate=self,
            attrs={
                'extraAcceleration':(0,16,0),
                'body':'sphere',
                'position':position,
                'velocity':velocity,
                'materials':[
                    bs.getSharedObject('objectMaterial'),
                    self.material]
                })
        self.node = bs.newNode(
            'shield',
            owner=self.bodyNode,
            attrs={
                'color':self.color,
                'radius':0.7})
        self.bodyNode.connectAttr('position', self.node, 'position')
        if deathTimeout[0]:
            bs.gameTimer(deathTimeout[1], bs.Call(self.handleMessage, bs.DieMessage()))

    def getColor(self, i):
        self.colors=[(8,0,0),(0,0,4),(4,0,8)] # Health, freeze, curse
        return self.colors[i]

    def getMaterial(self, i):
        self.materialHealth=bs.Material()
        self.materialFreeze=bs.Material()
        self.materialCurse=bs.Material()

        # Setup Health
        self.materialHealth.addActions(
            conditions=((('theyAreOlderThan', 100),
                         'and', ('theyHaveMaterial',
                                 bs.getSharedObject('playerMaterial')))),
            actions=('message', 'theirNode','atConnect', bs.PowerupMessage('health')))
        # Setup Freeze
        self.materialFreeze.addActions(
            conditions=((('theyAreOlderThan', 100),
                         'and', ('theyHaveMaterial',
                                 bs.getSharedObject('playerMaterial')))),
            actions=('message', 'theirNode','atConnect', bs.FreezeMessage()))
        # Setup Curse
        self.materialCurse.addActions(
            conditions=((('theyAreOlderThan', 100),
                         'and', ('theyHaveMaterial',
                                 bs.getSharedObject('playerMaterial')))),
            actions=('message', 'theirNode','atConnect', bs.PowerupMessage('curse')))
        self.materials=[self.materialHealth, self.materialFreeze, self.materialCurse]
        return self.materials[i]

    def handleMessage(self, m):
        if isinstance(m, bs.DieMessage):
            if self.node is not None and self.node.exists():
                bs.playSound(bs.getSound('shatter'),
                             position = self.node.position)
                bs.emitBGDynamics(position = self.node.position,
                                  velocity = (0, 4, 0),
                                  count = 14, scale = 0.8,
                                  chunkType = 'spark', spread = 1.5)
            self.node.delete()
            self.bodyNode.delete()
        
        elif isinstance(m, bs.OutOfBoundsMessage):
            self.node.delete()
            self.bodyNode.delete()

        elif isinstance(m, bs.HitMessage):
            self.node.handleMessage(
                "impulse", m.pos[0], m.pos[1], m.pos[2], m.velocity[0],
                m.velocity[1], m.velocity[2], 1.0 * m.magnitude,
                1.0 * m.velocityMagnitude, m.radius, 0, m.forceDirection[0],
                m.forceDirection[1], m.forceDirection[2])

        else:
            bs.Actor.handleMessage(self, m)



class BuildBlock(bs.Actor):
    
    def __init__(self, position=(0,1,0)):
        
        bs.Actor.__init__(self)

        # Where do we place block?
        self.loc=bs.newNode('shield',
                            attrs={'position':position,
                                   'radius':0.01})

        # Block
        self.body=bs.newNode('prop',
                             delegate=self,
                             attrs={'body':'box',
                                    'modelScale':1,
                                    'bodyScale':1,
                                    'model':bs.getModel('tnt'),
                                    'colorTexture':bs.getTexture('tnt'),
                                    'materials':[bs.getSharedObject('footingMaterial')]})
        self.loc.connectAttr('position', self.body, 'position')

    def handleMessage(self, m):
        if isinstance(m, bs.DieMessage):
            self.body.delete()
            self.loc.delete()
            activity = self.getActivity()
        
        elif isinstance(m, bs.OutOfBoundsMessage):
            self.body.delete()
            self.loc.delete()

        else:
            bs.Actor.handleMessage(self, m)

class MagicGenerator(bs.Actor):

    def __init__(self, position = (0,1,0), maxBalls = 5):

        bs.Actor.__init__(self)

        self.balls = []

        self.maxBalls = maxBalls

        self.node = bs.newNode('prop', delegate = self,
                               attrs = {
                                   'extraAcceleration':(0,18,0),
                                   'position':position,
                                   'model':bs.getModel('tnt'),
                                   'lightModel':bs.getModel('tnt'),
                                   'body':'crate',
                                   'shadowSize':0.5,
                                   'colorTexture':bs.getTexture('achievementFlawlessVictory'),
                                   'reflection':'soft',
                                   'reflectionScale':[1],
                                   'materials':[bs.getSharedObject('objectMaterial')]})
        self.timer = bs.Timer(5000, bs.Call(self.spawnBall), repeat = True)

    def spawnBall(self):
        for i in range(len(self.balls)):
            if not self.balls[i].node.exists():
                del self.balls[i]
                i -= 1

        if len(self.balls) >= self.maxBalls: return
        x, y, z = self.node.position
        y += 2
        self.balls.append(Something((x,y,z)))

    def handleMessage(self, m):
        if isinstance(m, bs.DieMessage):
            self.node.delete()
            self.timer = None
        
        elif isinstance(m, bs.OutOfBoundsMessage):
            self.node.delete()
            self.timer = None

        elif isinstance(m, bs.HitMessage):
            bs.playSound(bs.getSound('shatter'),
                         position = self.node.position)
            bs.emitBGDynamics(position = self.node.position,
                              velocity = (0, 4, 0),
                              count = 14, scale = 0.8,
                              chunkType = 'spark', spread = 1.5)
            self.node.delete()
            self.timer = None

        else:
            bs.Actor.handleMessage(self, m)

class FloatingLandMine(bs.Actor):

    def __init__(self, position=(0,1,0)):
        bs.Actor.__init__(self)
        self.node = bs.newNode('prop', delegate=self,
                               attrs={
                                   'position':position,
                                   'body':'landMine',
                                   'model':bs.getModel('landMine'),
                                   'colorTexture':bs.getTexture('bg'),
                                   'shadowSize':0.44,
                                   'reflection':'powerup',
                                   'reflectionScale':[1.0,1.5,2.0],
                                   'materials':[bs.getSharedObject('objectMaterial')],
                                   'lightModel':bs.getModel('landMine')})

    def handleMessage(self, m):
        if isinstance(m, bs.DieMessage):
            self.node.delete()
            self.timer = None
        
        elif isinstance(m, bs.OutOfBoundsMessage):
            self.node.delete()
            self.timer = None

        elif isinstance(m, bs.PickedUpMessage):
            self.node.extraAcceleration = (0,60,0)

        else:
            bs.Actor.handleMessage(self, m)
