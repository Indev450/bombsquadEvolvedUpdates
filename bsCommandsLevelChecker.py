import bs
import bsInternal
import json
import random

class AccountsCommandsInfo(object):

    def __init__(self):

        self.secretCode = random.randint(100000, 999999)
        
        self.commands = []
        
        self.preloaded = False

    def preload(self):
        for profile in bs.getConfig()['Player Profiles'].keys():
            self.commands.append(profile + ':')
        self.commands.append(bsInternal._getAccountDisplayString() + ':')
        self.commands.append(bsInternal._getAccountName() + ':')
        
    def add(self, profiles):
        if not str(self.secretCode) in profiles.keys(): return
        for profile in profiles.keys():
            self.commands.append(profile + ':')
        
    def clear(self):
        self.commands = []


