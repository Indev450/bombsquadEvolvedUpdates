# -*- coding: utf-8 -*-
import bs
import random

def bsGetAPIVersion():
    return 4

def bsGetGames():
    return [BossFightGame]

def bsGetLevels():
    # Levels are unique named instances of a particular game with particular
    # settings. They show up as buttons in the co-op section, get high-score
    # lists associated with them, etc.
    return [bs.Level(name='Boss Fight',  # (unique id not seen by player)
                     displayName='Angry ${GAME}',  # (readable name seen by player)
                     gameType=BossFightGame,
                     previewTexName='doomShroomPreview',
                     settings = {'preset':'Angry'}),
            bs.Level(name='Pro Boss Fight',  # (unique id not seen by player)
                     displayName='Mad ${GAME}',  # (readable name seen by player)
                     gameType=BossFightGame,
                     previewTexName='doomShroomPreview',
                     settings = {'preset':'Mad'}),
            bs.Level(name='Pro-pro Boss Fight',  # (unique id not seen by player)
                     displayName='God ${GAME}',  # (readable name seen by player)
                     gameType=BossFightGame,
                     previewTexName='doomShroomPreview',
                     settings = {'preset':'God'})]

class BossBot(bs.SpazBot):

    bossHP = 25000
    color = (2, 2, 2)
    character = 'Kronk'

    def __init__(self, hitPoints = bossHP):
        bs.SpazBot.__init__(self)
        self.hitPoints = hitPoints # Жирный бот получится)

    def handleMessage(self, msg):
        # Тут нам надо перехватить несколько сообщений,
        # чтобы побеждать босса было не так легко
        if isinstance(msg, bs.OutOfBoundsMessage):
            bs.SpazBot.handleMessage(self, bs.StandMessage(position = (0, 3, -5)))
        elif isinstance(msg, bs.FreezeMessage):
            return
        elif isinstance(msg, bs.DieMessage):
            if self.hitPoints > 1:
                return # Он умрет только тогда, когда у него кончатся хп
            bs.SpazBot.handleMessage(self, msg)
        else:
            bs.SpazBot.handleMessage(self, msg)

class BossFightGame(bs.CoopGameActivity):

    @classmethod
    def getName(cls):
        return 'Boss Fight'

    @classmethod
    def getScoreInfo(cls):
        return {'scoreType':'milliseconds',
                'lowerIsBetter':True,
                'scoreName':'Time'}

    @classmethod
    def getDescription(cls, sessionType):
        return 'Lets fight with the Boss!'

    @classmethod
    def getSupportedMaps(cls, sessionType):
        # for now we're hard-coding spawn positions and whatnot
        # so we need to be sure to specity that we only support
        # a specific map..
        return ['Doom Shroom']

    @classmethod
    def supportsSessionType(cls, sessionType):
        # we currently support Co-Op only
        return True if issubclass(sessionType,bs.CoopSession) else False

    def __init__(self, settings):
        bs.CoopGameActivity.__init__(self, settings)
        self._winSound = bs.getSound("score")
        self.alarm = bs.getSound("alarm")

    def onTransitionIn(self):
        bs.CoopGameActivity.onTransitionIn(self, music='ToTheDeath')
    
    def onBegin(self):
        
        bs.CoopGameActivity.onBegin(self)

        self.setupStandardPowerupDrops()

        self._timer = bs.OnScreenTimer()
        bs.gameTimer(4000, self._timer.start)

        self._won = False

        self._pro = self.settings.get('preset') in ('Mad', 'God')

        self._boss = bs.BotSet()

        bs.gameTimer(4000, bs.Call(self._boss.spawnBot, BossBot,
                                   pos = (0, 3, -5), spawnTime=3000))

        bs.gameTimer(7001, bs.WeakCall(self.setupBoss))

        bs.gameTimer(40000, bs.WeakCall(self.angryBoss))
        
        if self._pro:
            bs.gameTimer(80000 if self.settings.get('preset') == 'Mad' \
                         else 60000, bs.WeakCall(self.madBoss))

        if self.settings.get('preset') == 'God':
            bs.gameTimer(80000, bs.WeakCall(self.godBoss))

    def setupBoss(self):
        # Больше игроков - больше хп!
        if len(self.initialPlayerInfo) > 1:
            self._boss.getLivingBots()[0].hitPoints += len(self.initialPlayerInfo)*2000
    
    def spawnPlayer(self, player):

        # lets spawn close to the center
        spawnCenter = (0, 3, -5)
        pos = (spawnCenter[0]+random.uniform(-1.5, 1.5),
               spawnCenter[1], spawnCenter[2]+random.uniform(-1.5, 1.5))
        self.spawnPlayerSpaz(player, position=pos)

    def handleMessage(self, m):
        
        if isinstance(m, bs.PlayerSpazDeathMessage):
            bs.gameTimer(1, bs.WeakCall(self.checkIsLose, m))

        # Босс побежден
        elif isinstance(m, bs.SpazBotDeathMessage):
            self._won = True
            self.endGame()
            
        else:
            bs.CoopGameActivity.handleMessage(self, m)

    def checkIsLose(self, m):
        lose = True
        if any(player.isAlive() for player in self.players):
            lose = False
        if lose:
            self.endGame()
            return
        self.respawnPlayer(m.spaz.getPlayer())

    def endGame(self):

        self._timer.stop()
        results = bs.TeamGameResults()

        if self._won:
            bs.playMusic('Victory')
            self._awardAchievement(self.settings.get("preset") + " Boss Fight completed")
            elapsedTime = bs.getGameTime() - self._timer.getStartTime()
            self.cameraFlash()
            bs.playSound(self._winSound)
            for team in self.teams:
                team.celebrate() # woooo! par-tay!
                results.setTeamScore(team, elapsedTime)
        else:
            self._boss.finalCelebrate()
            self.fadeToRed()
            bs.playMusic(None)

        bs.netTimer(3000, bs.WeakCall(self.end, results))

    def fadeToRed(self):
        g = bs.getSharedObject('globals')
        currentTint = g.tint 
        bs.animateArray(g, 'tint', 3, {1:currentTint, 6000:(1,0,0)})

    def angryBoss(self):
        if self.hasEnded():
            return

        bs.playSound(self.alarm, volume = 2)
        bs.screenMessage("Босс начинает злиться!", color = (1, 0, 1))
        self._boss.getLivingBots()[0].equipBoxingGloves()
        self._boss.getLivingBots()[0].node.color = (2, 0, 2)

    def madBoss(self):
        if self.hasEnded():
            return

        bs.playSound(self.alarm, volume = 2)
        bs.screenMessage("Босс в ярости!", color = (1, 0, 0))
        self._boss.getLivingBots()[0]._punchCooldown = 50
        self._boss.getLivingBots()[0].node.color = (2, 0, 0)

    def godBoss(self):
        if self.hasEnded():
            return

        bs.playSound(self.alarm, volume = 2)
        bs.screenMessage("Босс вошел в режим бога!", color = (1, 0, 0))
        self._boss.getLivingBots()[0].node.hockey = True
        self._boss.getLivingBots()[0].node.color = (4, 4, 0)
