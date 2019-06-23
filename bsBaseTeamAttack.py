import bs

def bsGetAPIVersion():
    # see bombsquadgame.com/apichanges
    return 4


def bsGetGames():
    return [BaseAttackGame]

class BaseAttackGame(bs.TeamGameActivity):

    @classmethod
    def getName(cls):
        return 'Team base attck'

    @classmethod
    def getDescription(cls, sessionType):
        return 'Destroy enemies\'s base'

    @classmethod
    def supportsSessionType(cls, sessionType):
        return True if issubclass(sessionType, bs.TeamsSession) else False

    @classmethod
    def getSupportedMaps(cls, sessionType):
        return bs.getMapsSupportingPlayType("teamFlag")

    @classmethod
    def getSettings(cls, sessionType):
        return [
            ("Score to Win", {'minValue': 1, 'default': 1}),
            ("Time Limit", {
                'choices': [('None', 0), ('1 Minute', 60),
                            ('2 Minutes', 120), ('5 Minutes', 300),
                            ('10 Minutes', 600), ('20 Minutes', 1200)],
                'default': 0 }),
            ("Respawn Times", {
                'choices': [('Shorter', 0.25), ('Short', 0.5), ('Normal',1.0),
                            ('Long',2.0), ('Longer', 4.0)],
                'default': 1.0}),
            ("Epic Mode", {'default': False})]

    def __init__(self, settings):
        bs.TeamGameActivity.__init__(self, settings)
        self._scoreBoard = bs.ScoreBoard()
        if self.settings['Epic Mode']: self._isSlowMotion = True

    def getInstanceDescription(self):
        if self.settings['Score to Win'] == 1: return 'Destroy enemies\'s base.'
        else:
            return ('Destroy enemies\'s base ${ARG1} times.',
                    self.settings['Score to Win'])

    def getInstanceScoreBoardDescription(self):
        if self.settings['Score to Win'] == 1: return 'Destroy 1 base.'
        else: return ('Destroy ${ARG1} bases.', self.settings['Score to Win'])

    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(
            self,
            music='Epic' if self.settings['Epic Mode'] else 'FlagCatcher')

    def onTeamJoin(self, team):

        team.gameData['score'] = 0
        team.gameData['flagReturnTouches'] = 0
        team.gameData['homeFlagAtBase'] = True
        team.gameData['touchReturnTimer'] = None
        team.gameData['enemyFlagAtBase'] = False
        team.gameData['basePos'] = self.getMap().getFlagPosition(team.getID())
        team.gameData['basePos'] = (team.gameData['basePos'][0],
                                    team.gameData['basePos'][1] + 0.5,
                                    team.gameData['basePos'][2])

        self.projectFlagStand(team.gameData['basePos'])

        bs.newNode(
            'light',
            attrs={
                'position': team.gameData['basePos'],
                'intensity': 0.6,
                'heightAttenuated': False,
                'volumeIntensityScale': 0.1,
                'radius': 0.1,
                'color': team.color
            })

        self._spawnFlagForTeam(team)
        self._updateScoreBoard()

    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)
        self.setupStandardTimeLimit(self.settings['Time Limit'])
        self.setupStandardPowerupDrops()

    def _spawnFlagForTeam(self, team):
        base = team.gameData['base'] = bs.BaseBlock(position=team.gameData['basePos'], team=team)
        team.gameData['flagReturnTouches'] = 0
        self._flashBase(team, length=1000)
        bs.playSound(self._swipSound, position=base.body.position)

    def _score(self, team):
        team.gameData['score'] -= 1
        self._flashBase(team)
        self._updateScoreBoard()
        # have teammates celebrate
        for player in team.players:
            try:
                player.actor.node.handleMessage('celebrate', 2000)
            except Exception:
                pass
        if team.gameData['score'] <= -1*self.settings['Score to Win']:
            self.endGame()

    def endGame(self):
        results = bs.TeamGameResults()
        for t in self.teams:
            results.setTeamScore(t, t.gameData['score'])
        self.end(results=results, announceDelay=800)

    def _flashBase(self, team, length=2000):
        light = bs.newNode(
            'light',
            attrs={
                'position': team.gameData['basePos'],
                'heightAttenuated': False,
                'radius': 0.7,
                'color': team.color
            })
        bs.animate(light, 'intensity', {0: 0, 250: 2.0, 500: 0}, loop=True)
        bs.gameTimer(length, light.delete)

    def spawnPlayerSpaz(self, *args, **keywds):
        # intercept new spazzes and add our team material for them
        spaz = bs.TeamGameActivity.spawnPlayerSpaz(self, *args, **keywds)
        spaz.getPlayer().gameData['touchingOwnFlag'] = 0
        noPhysicalMats = [
            spaz.getPlayer().getTeam().gameData['spazMaterialNoFlagPhysical']
        ]
        noCollideMats = [
            spaz.getPlayer().getTeam().gameData['spazMaterialNoFlagCollide']
        ]
        # our normal parts should still collide; just not physically
        # (so we can calc restores)
        spaz.node.materials = list(spaz.node.materials) + noPhysicalMats
        spaz.node.rollerMaterials = list(
            spaz.node.rollerMaterials) + noPhysicalMats
        # pickups and punches shouldn't hit at all though
        spaz.node.punchMaterials = list(
            spaz.node.punchMaterials) + noCollideMats
        spaz.node.pickupMaterials = list(
            spaz.node.pickupMaterials) + noCollideMats
        spaz.node.extrasMaterials = list(
            spaz.node.extrasMaterials) + noCollideMats
        return spaz

    def _updateScoreBoard(self):
        for team in self.teams:
            self._scoreBoard.setTeamValue(team, team.gameData['score'],
                                          self.settings['Score to Win'])

    def handleMessage(self, m):
        if isinstance(m, bs.PlayerSpazDeathMessage):
            bs.TeamGameActivity.handleMessage(self, m)  # augment standard
            self.respawnPlayer(m.spaz.getPlayer())
        elif isinstance(m, bs.BaseDestroyedMessage):
            bs.gameTimer(3000, bs.Call(self._spawnFlagForTeam,
                                      self._checkBases()))
        else:
            bs.TeamGameActivity.handleMessage(self, m)

    def _checkBases(self):
        for team in self.teams:
            if not team.gameData['base'].exists():
                self._score(team)
                return team
            
