from random import randint
import random
import bs
import bsUtils

class BaseDestroyedMessage(object):
    pass

class BaseBlock(bs.Actor):
    
    def __init__(self, position=(0,1,0), team=None):
        
        bs.Actor.__init__(self)
        self.errorSound = bs.getSound('error')
        self.position = position
        self._team = team
        
        # Where do we place block?
        self.loc = bs.newNode('shield',
                            attrs={'position':position,
                                   'radius':0.01,
                                   'color':(-8,-2,-2)})

        # Block.
        self.body = bs.newNode('prop',
                             delegate=self,
                             attrs={'body':'box',
                                    'modelScale':1,
                                    'bodyScale':1,
                                    'model':bs.getModel('tnt'),
                                    'colorTexture':bs.getTexture('powerupCurse'),
                                    'materials':[bs.getSharedObject('footingMaterial'),
                                                 bs.getSharedObject('objectMaterial')]})
        self.loc.connectAttr('position', self.body, 'position')
        self.hp = 8000
        self.frozen = False # On freeze block don't spawn enemies.
        self.position = position # For spawn bots.
        if self._team is None:
            self._bots = bs.BotSet()
            self._botSpawnCooldown = 5000
            self.spawner = bs.Timer(self._botSpawnCooldown, self._spawnBot, repeat=True)
        self._scoreText = bs.newNode('text',
                                     owner=self.body,
                                     attrs={'text':'HP: ' + str(self.hp),
                                            'inWorld':True,
                                            'shadow':1.0,
                                            'flatness':1.0,
                                            'color':(0,1,0),
                                            'scale':0.01,
                                            'hAlign':'center',
                                            'position':self.position})
        bs.gameTimer(1000, self._scoreText.delete)
        
    def _spawnBot(self):
        if self.frozen or len(self._bots.getLivingBots())>= 5: return # 5 bots maximum
        self._bots.spawnBot(bs.ZombieBot,
                            pos=self.position,
                            spawnTime=3000)
    
    def exists(self):
        return self.body.exists()

    def _onPunched(self, damage):
        if not self.exists(): return
        self.hp -= damage
        if self.hp <= 0:
            b = bs.Blast(self.position,(0,0,0),3.0,'normal', None, 'punch').autoRetain()
            bs.screenMessage('Enemies\'s base were destroyed!',
                             color=(0,1,0))
            self.handleMessage(bs.DieMessage())
        self._scoreText.delete()
        self._scoreText = bs.newNode('text',
                                     owner=self.body,
                                     attrs={'text':'HP: ' + str(self.hp),
                                            'inWorld':True,
                                            'shadow':1.0,
                                            'flatness':1.0,
                                            'color':(0,1,0),
                                            'scale':0.01,
                                            'hAlign':'center',
                                            'position':self.position})
        bs.gameTimer(1000, self._scoreText.delete)
        
    
    def handleMessage(self, m):

        if isinstance(m, bs.DieMessage):
            self.body.delete()
            self.loc.delete()
            self.spawner = None
            activity = self._activity()
            if activity and not m.immediate:
                activity.handleMessage(BaseDestroyedMessage())
        
        elif isinstance(m, bs.OutOfBoundsMessage):
            self.body.delete()
            self.loc.delete()

        elif isinstance(m, bs.FreezeMessage):
            if not self.body.exists(): return
            if not self.frozen:
                self.frozen = True
                bs.gameTimer(10000, bs.WeakCall(self.handleMessage,
                                               bs.ThawMessage()))

        elif isinstance(m, bs.ThawMessage):
            if self.frozen and self.body.exists():
                self.frozen = False

        elif isinstance(m, bs.HitMessage):
            if not self.body.exists(): return
            if m.flatDamage: damage = m.flatDamage
            if m.hitType == 'punch':
                damage = randint(1,3) * 150
                #bs.screenMessage('hitted')
            elif m.hitSubType in ('normal', 'tnt', 'block',
                                  'landMine', 'sticky', 'impact',
                                  'cineticTrap'):
                damage = randint(1,3) * 300
                #bs.screenMessage('exploded')
            elif m.hitSubType in ('ice', 'iceImpact'):
                damage = randint(1,3) * 100
                #bs.screenMessage('freezed')
                self.handleMessage(bs.FreezeMessage())
            else:
                bs.playSound(self.errorSound)
                bs.screenMessage('Unknown hit: ' + m.hitSubType)
                damage = 200

            self._onPunched(damage)
            bs.emitBGDynamics(position=self.position, velocity=(0,0,0),
                                  count=35, scale=0.7, chunkType='spark',
                                  emitType='stickers');
            bs.playSound(bs.getSound('punch01'), 1.0,
                         position=self.position)

            # if damage was significant, lets show it
            if damage > 350:
                bs.playSound(bs.getSound('punchStrong01'), 1.0,
                             position=self.position)
                bsUtils.showDamageCount('-' + str(int(damage/10)) + "%",
                                        m.pos, m.forceDirection)

        else:
            bs.Actor.handleMessage(self, m)
    def __del__(self):
        self.handleMessage(bs.DieMessage())

def bsGetAPIVersion():
    # see bombsquadgame.com/apichanges
    return 4

def bsGetGames():
    return [BaseAttackGame]

def bsGetLevels():
    # Levels are unique named instances of a particular game with particular
    # settings. They show up as buttons in the co-op section, get high-score
    # lists associated with them, etc.
    return [bs.Level(name='Base attack',  # (unique id not seen by player)
                     displayName='${GAME}',  # (readable name seen by player)
                     gameType=BaseAttackGame,
                     settings={'preset':'regular'},
                     previewTexName='CragCastlePreview')]

class BaseAttackGame(bs.TeamGameActivity):

    @classmethod
    def getName(cls):
        return 'Base attack'
    
    @classmethod
    def getScoreInfo(cls):
        return {'scoreType':'milliseconds',
                'lowerIsBetter':True,
                'scoreName':'Time'}
    
    @classmethod
    def getDescription(cls, sessionType):
        return 'Destroy enemies\'s bases.'
    
    @classmethod
    def getSupportedMaps(cls, sessionType):
        # for now we're hard-coding spawn positions and whatnot
        # so we need to be sure to specity that we only support
        # a specific map..
        return ['Crag Castle']

    @classmethod
    def supportsSessionType(cls, sessionType):
        # we currently support Co-Op only
        return True if issubclass(sessionType,bs.CoopSession) else False

    def __init__(self, settings):
        bs.TeamGameActivity.__init__(self, settings)
        self._winSound = bs.getSound("score")

    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self, music='Marching')

    def onBegin(self):

        bs.TeamGameActivity.onBegin(self)

        self._isWon = False

        # make our on-screen timer and start it roughly when our bots appear
        self._timer = bs.OnScreenTimer()
        bs.gameTimer(4000, self._timer.start)

        self.setupStandardPowerupDrops()

        self._bases = [BaseBlock((7.8, 7.7, 0)),
                       BaseBlock((-6.3, 7.7, 0))]

    def spawnPlayer(self, player):

        # lets spawn close to the center
        pos = (0, 6, 0)
        
        self.spawnPlayerSpaz(player, position=pos)

    def _checkIfWon(self):
        # simply end the game if there's no living bots..
        for base in self._bases:
            if base.exists():
                return
        self._isWon = True
        self.endGame()

    def handleMessage(self, m):

        # a player has died
        if isinstance(m, bs.PlayerSpazDeathMessage):
            bs.TeamGameActivity.handleMessage(self, m) # do standard stuff
            self.respawnPlayer(m.spaz.getPlayer()) # kick off a respawn

        # One of bases were destroyed
        elif isinstance(m, BaseDestroyedMessage):
            bs.pushCall(self._checkIfWon)

    def endGame(self):

        # stop our on-screen timer so players can see what they got
        self._timer.stop()
        
        results = bs.TeamGameResults()

        # if we won, set our score to the elapsed time
        # (there should just be 1 team here since this is co-op)
        # ..if we didn't win, leave scores as default (None) which means we lost
        if self._isWon:
            elapsedTime = bs.getGameTime()-self._timer.getStartTime()
            self.cameraFlash()
            bs.playSound(self._winSound)
            for team in self.teams:
                team.celebrate() # woooo! par-tay!
                results.setTeamScore(team, elapsedTime)

        # ends this activity..
        self.end(results)
