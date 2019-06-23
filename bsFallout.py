import bs

def _blast(pos = (0,0,0), r = 1):
    bs.Blast(position = pos, blastRadius = r).autoRetain()

def atomicBlast(pos = (0,0,0)):
    x, y, z = pos
    _blast((x,y,z), 1.5)
    bs.gameTimer(50, call = bs.Call(_blast, (x,y+1,z), 1))
    bs.gameTimer(200, call = bs.Call(_blast, (x,y+2,z), 4))
