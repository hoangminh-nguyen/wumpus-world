
import operator as op
import numpy as np
from collections import Counter
import random
import time

class Game:
    def __init__(self):
        self.mapSize = 0
        self.map = []
        self.agent = Agent()
        self.KB = KB()
        self.score = 0
        self.nGold = 0
        self.nWumpus = 0
        self.nKilledWumpus = 0
        self.nGrabbedGold = 0
        self.climbOut = False
        self.log = []
    
    def ReadInput(self):
        inputPath = input("Enter input file path: ")              
        f = None

        try:
            f = open(inputPath, 'r')
        except IOError:
            print("Couldn't open the file")
            return False
        else:
            # First line is size of map
            self.mapSize = int(f.readline())
            print("Map size: " + str(self.mapSize))

            # Next lines are map info
            for i in range(self.mapSize):
                self.map.append(f.readline().rstrip().split('.'))
                       
            # Determine agent's init pos
            for i in range(self.mapSize):
                found = False
                for j in range(self.mapSize):
                    if 'A' in self.map[i][j]:
                        self.agent.curPos = (i,j)
                        self.agent.doorPos = (i,j)
                        self.agent.path.append((i,j))
                        found = True
                        break
                if found == True:
                    break
                    
            # The number of golds and wumpus
            for i in range(self.mapSize):                
                for j in range(self.mapSize):
                    if 'G' in self.map[i][j]:
                        self.nGold += 1
                    if 'W' in self.map[i][j]:
                        self.nWumpus += 1
                                
        finally:
            if f: 
                f.close()
                return True

    def AddLog(self, strLog):
        print(strLog)
        self.log.append(strLog)
            
    def Percept(self, curPos):
        # Percept through current pos
        self.AddLog('-'*50 + ' PERCEPT AT {} '.format(str(self.ToWorldPos(curPos))) + '-'*50)
        curPercept = list(self.map[curPos[0]][curPos[1]])
        emptySquare = True
        onlyS = False
        onlyB = False

        if 'W' in curPercept:            
            self.KB.TellW([['W{}{}'.format(curPos[0], curPos[1])]])
            self.agent.die = True
            self.score -= 10000
            self.AddLog('\tEncountered Wumpus')
            emptySquare = False
        elif 'W' not in curPercept:            
            self.KB.TellW([['!W{}{}'.format(curPos[0], curPos[1])]])
            self.AddLog('\tNo Wumpus')
        
        if 'P' in curPercept:
            self.KB.TellP([['P{}{}'.format(curPos[0], curPos[1])]])
            self.agent.die = True
            self.score -= 10000
            self.AddLog('\tFallen into Pit')
            emptySquare = False
        elif 'P' not in curPercept:
            self.KB.TellP([['!P{}{}'.format(curPos[0], curPos[1])]])
            self.AddLog('\tNo Pit')
        
        if 'S' in curPercept:            
            self.KB.TellW([['S{}{}'.format(curPos[0], curPos[1])]])
            self.AddLog('\tSmelling some Stench')
            emptySquare = False
            onlyS = True
        elif 'S' not in curPercept:
            self.KB.TellW([['!S{}{}'.format(curPos[0], curPos[1])]])
            self.AddLog('\tNo Stench')
        
        if 'B' in curPercept:
            self.KB.TellP([['B{}{}'.format(curPos[0], curPos[1])]]) 
            self.AddLog('\tFeeling some Breeze')
            emptySquare = False
            onlyB = True
        elif 'B' not in curPercept:
            self.KB.TellP([['!B{}{}'.format(curPos[0], curPos[1])]])
            self.AddLog('\tNo Breeze')
            
        # If Gold is there, grab it
        if 'G' in curPercept:
            self.score += 100            
            self.map[curPos[0]][curPos[1]] = self.map[curPos[0]][curPos[1]].replace('G', '')            
            self.nGrabbedGold += 1
            self.AddLog('\tGrab Gold')
        
        self.agent.emptySquare = emptySquare

        if emptySquare == True:
            adjs = self.GetAdjacentSquare(curPos)
            for p in adjs:
                self.KB.TellP([['!P{}{}'.format(p[0], p[1])]])
                self.KB.TellW([['!W{}{}'.format(p[0], p[1])]])              

        if onlyS == True and onlyB == False:
            adjs = self.GetAdjacentSquare(curPos)
            for p in adjs:
                self.KB.TellP([['!P{}{}'.format(p[0], p[1])]])
            self.agent.onlyS.append(curPos)

        if onlyB == True and onlyS == False:
            adjs = self.GetAdjacentSquare(curPos)
            for p in adjs:                
                self.KB.TellW([['!W{}{}'.format(p[0], p[1])]])
            self.agent.onlyB.append(curPos)

        #if onlyB == True and onlyS == True:
        #    adjs = self.GetAdjacentSquare(curPos)
        #    for p in adjs:                
        #        self.KB.TellW([['!W{}{}'.format(p[0], p[1]), '!P{}{}'.format(p[0], p[1])], ['W{}{}'.format(p[0], p[1]), 'P{}{}'.format(p[0], p[1])])            
            
        #self.KB.TellW(KB.ToCNF(self.ConsiderWumpus(curPos)))
        #self.KB.TellP(KB.ToCNF(self.ConsiderPit(curPos)))
        
            
        # Following current percept, generate logic clauses based on game rules
        #adjs = self.GetAdjacentSquare(curPos)
        #for a in adjs:
        #    if a in self.agent.visited or a in self.agent.considered:
        #        adjs.pop(adjs.index(a))
                
        #self.ConsiderDanger(adjs)        
        self.agent.visited.append(curPos)
        #self.agent.considered += adjs
        
            
    def ConsiderDanger(self, poss):
        '''
        poss: a list of positions that need to be considered danger
        '''
        for pos in poss:
            # Wumpus
            self.KB.Tell(KB.ToCNF(self.ConsiderWumpus(pos)))
            
            # Pit
            self.KB.Tell(KB.ToCNF(self.ConsiderPit(pos)))
              
    def ConsiderWumpus(self, pos):
        '''
        Return clause that represents considering danger of wumpus at pos
        '''
        adjs = self.GetAdjacentSquare(pos)
        tmp = []
        for p in adjs:
            tmp.append('W{}{}'.format(p[0], p[1]))
        return ['S{}{}'.format(pos[0], pos[1]), tmp]
        
    def ConsiderPit(self, pos):
        '''
        Return clause that represents considering danger of pit at pos
        '''
        adjs = self.GetAdjacentSquare(pos)
        tmp = []
        for p in adjs:
            tmp.append('P{}{}'.format(p[0], p[1]))
        return ['B{}{}'.format(pos[0], pos[1]), tmp]
    
    def GetAdjacentSquare(self, pos):
        '''
        Return list of squares that are 1 step away from pos in 4 directions
        '''
        i = pos[0]
        j = pos[1]
        adjs = []
        if i+1 < self.mapSize:
            adjs.append((i+1, j))
        if i > 0:
            adjs.append((i-1, j))
        if j+1 < self.mapSize:
            adjs.append((i, j+1))
        if j > 0:
            adjs.append((i, j-1))
        
        return adjs
    
    def GetNotVisitedAround(self):
        l1 = []       
        for pos in self.agent.visited:
            l1 += self.GetNotVisitedAdjacents(pos)
        
        l2 = []        
        for x in l1:
            if x not in l2:
                l2.append(x)       
        return l2
    
    def GetNotVisitedAdjacents(self, pos):
        l1 = [i for i in self.GetAdjacentSquare(pos) if i not in self.agent.visited]
        l2 = []
        
        for x in l1:
            if x not in l2:
                l2.append(x)       
        return l2
    
    def GetVisitedAdjacents(self, pos):
        return [i for i in self.GetAdjacentSquare(pos) if i in self.agent.visited]    
    
    def A_Star_Graph_Search(self, goal, state):
        if (state==goal):
            return []
        frontier=[[state,-1,self.ManhattanDis(goal,state),0,self.ManhattanDis(goal,state)]] #[node,father,f(n),g(n),h(n)]
        expanded_node=[]
        while(frontier):
            node=frontier.pop(0)
            expanded_node.append(node)
            
            if node[0] == goal:
                path_returned=self.return_path(expanded_node)
                return path_returned
            for x in self.GenerateSuccessors((node[0][0], node[0][1]), goal):
                if self.check_Existed(frontier,x)==False and self.check_Existed(expanded_node,x)==False:
                    frontier.append([x,node[0],self.ManhattanDis(x,goal) +node[3]+1,node[3]+1,self.ManhattanDis(x,goal)]) #[node,father,f(n),g(n),h(n)]             
                    frontier.sort(key=op.itemgetter(2))
                    continue
                if self.check_Existed(frontier,x)==True:
                    for y in frontier:
                        if y[0]==x and y[2]>node[2]+1:
                            frontier.pop(frontier.index(y))
                            frontier.append([x,node[0],self.ManhattanDis(x,goal)+node[3]+1,node[3]+1,self.ManhattanDis(x,goal)])
                            frontier.sort(key=op.itemgetter(2))
                            break
        return []
    
    def ManhattanDis(self, x, y):
        return abs(x[0]-y[0]) + abs(x[1] - y[1])
    
    def check_Existed(self, listt,x):
        for y in listt:
            if x==y[0]:
                return True
        return False
    
    def return_path(self, explorded):
        path = []
        current = explorded[-1]
        while(current[1] != -1):
            path.insert(0, current[0])
            for i in explorded:
                if i[0] == current[1]:
                    current = i
                    break
        path.insert(0, current[0])
        return path   
    
    def GenerateSuccessors(self, pos, goal):
        return [i for i in self.GetAdjacentSquare(pos) if i in self.agent.visited or i == goal]
            
    def OnShootArrowAction(self, direction):
        # Eliminate wumpus along that direction
        self.score -= 100
        eliminated = ()
        if direction == 'EAST':
            for j in range(self.mapSize)[self.agent.curPos[1]+1::]:
                p = (self.agent.curPos[0], j)
                if (self.IsWumpusAt(p)):
                    self.map[p[0]][p[1]] = self.map[p[0]][p[1]].replace('W', '')
                    eliminated = p
                    break                 
                      
        elif direction == 'WEST':
            for j in reversed(range(self.mapSize)[:self.agent.curPos[1]]):
                p = (self.agent.curPos[0], j)
                if (self.IsWumpusAt(p)):
                    self.map[p[0]][p[1]] = self.map[p[0]][p[1]].replace('W', '')
                    eliminated = p
                    break  
                    
        elif direction == 'SOUTH':
            for i in range(self.mapSize)[self.agent.curPos[0]+1::]:
                p = (i, self.agent.curPos[1])
                if (self.IsWumpusAt(p)):
                    self.map[p[0]][p[1]] = self.map[p[0]][p[1]].replace('W', '')
                    eliminated = p
                    break
                                
        elif direction == 'NORTH':
            for i in reversed(range(self.mapSize)[:self.agent.curPos[0]]):
                p = (i, self.agent.curPos[1])
                if (self.IsWumpusAt(p)):
                    self.map[p[0]][p[1]] = self.map[p[0]][p[1]].replace('W', '')
                    eliminated = p
                    break
                    
        if eliminated != ():            
            self.nKilledWumpus += 1
            self.RemoveStench(eliminated)
        
    def IsWumpusAt(self, pos):
        return 'W' in self.map[pos[0]][pos[1]]

    def RemoveStench(self, wPos):
        wAdjs = self.GetAdjacentSquare(wPos)        
        for sPos in wAdjs:
            flag = True
            for pos in self.GetAdjacentSquare(sPos):
                if 'W' in self.map[pos[0]][pos[1]]:
                    flag = False
                    break
            if flag:
                self.map[sPos[0]][sPos[1]] = self.map[sPos[0]][sPos[1]].replace('S', '')
    
    def IsEndGame(self):
        if self.climbOut:
            self.AddLog('\nAgent climbed out cave')
        elif (self.nGold-self.nGrabbedGold) == 0 and (self.nWumpus-self.nKilledWumpus) == 0:
            self.AddLog('\nAgent grabbed all Gold and killed all Wumpus')
        elif self.agent.die:
            self.AddLog('\nAgent died')

        return self.climbOut or (self.nGold-self.nGrabbedGold) == 0 and (self.nWumpus-self.nKilledWumpus) == 0 or self.agent.die
    
    def ToWorldPos(self, pos):
        return (pos[1] + 1, self.mapSize - pos[0])

    def IsAdjacentTo(self, pos1, pos2):
        '''
        Determine if pos1 is adjacent to pos2
        '''
        adjs = self.GetAdjacentSquare(pos2)
        return pos1 in adjs

    def ToResultFile(self, path):
        with open("result.txt", 'w') as output:
            for row in self.log:
                output.write(str(row) + '\n')
    
    def Run(self):
        startTime = time.time()
        while (True):              
            #print('GameScore: ' + str(self.score))
            #print('Len agent moves: ' + str(len(self.agent.path)-1))
            #print(" Grabbed Golds: " + str(self.nGrabbedGold))
            #print(" Killed Wumpuses: " + str(self.nKilledWumpus))
            #print(" Shot Arrows: " + str(self.agent.nArrow))
            # Get percept
            if self.agent.curPos not in self.agent.visited:               
                self.Percept(self.agent.curPos)
            # If not die, else break
            if self.IsEndGame() == True:  
                endTime = time.time()
                self.AddLog('-'*30 + ' END GAME ' + '-'*30)
                self.AddLog('-'*10 + ' Time to finish: ' + str(endTime - startTime))
                self.AddLog('-'*10 + ' GAME SCORE: ' + str(self.score))
                self.AddLog('-'*10 + " Agent's Path: " + str([self.ToWorldPos(pos) for pos in self.agent.path]))
                self.AddLog('-'*10 + " The number of Agent's moves: " + str(len(self.agent.path)-1))
                self.AddLog('-'*10 + " Golds in map: " + str(self.nGold))
                self.AddLog('-'*10 + " Grabbed Golds: " + str(self.nGrabbedGold))
                self.AddLog('-'*10 + " Wumpuses in map: " + str(self.nWumpus))
                self.AddLog('-'*10 + " Killed Wumpuses: " + str(self.nKilledWumpus))
                self.AddLog('-'*10 + " Shot Arrows: " + str(self.agent.nArrow))

                break

            # Decide which direction to move next
            hasMoved = False
            if self.agent.emptySquare == True:
                self.AddLog('\t' + '#'*4 + ' At empty square')
                notVisitedAdjs = self.GetNotVisitedAdjacents(self.agent.curPos)
                for pos in notVisitedAdjs:
                    self.AddLog('\t' + '#'*8 + ' No danger at square {}'.format(self.ToWorldPos(pos)))
                
                if notVisitedAdjs != []:
                    self.agent.curPos = random.choice(notVisitedAdjs)
                    self.AddLog('\t' + '#'*8 + ' Random move to {}'.format(self.ToWorldPos(self.agent.curPos)))
                    self.agent.path.append(self.agent.curPos)
                    self.score -= 10
                    hasMoved = True
                                    
            if hasMoved:
                continue
            notVisitedAdjs = self.GetNotVisitedAdjacents(self.agent.curPos)
            for pos in notVisitedAdjs:
                kbW =  self.KB.cnfWClauses.copy() + KB.ToCNF(self.ConsiderWumpus(pos)).copy()
                kbP =  self.KB.cnfPClauses.copy() + KB.ToCNF(self.ConsiderPit(pos)).copy()
                if self.KB.AskW('!W{}{}'.format(pos[0], pos[1]), kbW) and self.KB.AskP('!P{}{}'.format(pos[0], pos[1]), kbP):
                    # If safe pos, move there                   
                    self.AddLog('\t' + '#'*4 + ' No danger at square {}, move there'.format(self.ToWorldPos(pos)))
                    self.agent.curPos = pos
                    hasMoved = True
                    self.agent.path.append(pos) 
                    self.score -= 10
                    break
                else:
                    self.AddLog('\t' + '#'*4 + ' Not sure at {}'.format(self.ToWorldPos(pos)))
                      
            if hasMoved == False: # If not moved yet, take a look at other poss that are not visited yet  
                self.AddLog('\t' + '#'*4 + ' Agent is not sure about squares around and looking at other squares that are not visited yet...')
                notVisited = self.GetNotVisitedAround()
                paths = []
                for pos in notVisited:
                    if pos in notVisitedAdjs:
                        continue
                    kbW =  self.KB.cnfWClauses.copy() + KB.ToCNF(self.ConsiderWumpus(pos)).copy()
                    kbP =  self.KB.cnfPClauses.copy() + KB.ToCNF(self.ConsiderPit(pos)).copy()
                    if self.KB.AskW('!W{}{}'.format(pos[0], pos[1]), kbW) and self.KB.AskP('!P{}{}'.format(pos[0], pos[1]), kbP):                                          
                        paths.append(self.A_Star_Graph_Search(pos, self.agent.curPos))
                        self.AddLog('\t' + '#'*8 + ' No danger at square {}'.format(self.ToWorldPos(pos)))
                    else:
                        self.AddLog('\t' + '#'*8 + ' Not sure at {}'.format(self.ToWorldPos(pos)))
                        
                if paths != []:
                    lens = [len(path) for path in paths]
                    # Move to the closest pos
                    minIdx = np.argmin(lens)
                    self.agent.path += paths[minIdx][1::]
                    self.agent.curPos = self.agent.path[-1]
                    self.score -= 10*(lens[minIdx]-1)
                    hasMoved = True
                    self.AddLog('\t' + '#'*8 + ' Move to the closest safe square {}'.format(self.ToWorldPos(self.agent.curPos)))
                    for p in paths[minIdx][1:-1]:
                        self.AddLog('\t' + '#'*12 + ' On the way to {}, At visited square {}'.format(self.ToWorldPos(self.agent.curPos), self.ToWorldPos(p)))
                    self.AddLog('\t' + '#'*12 + ' On the way to {}, At square {}'.format(self.ToWorldPos(self.agent.curPos), self.ToWorldPos(self.agent.curPos)))
                    
                else: # Agent is not sure about adjacent pos due to lack of perception
                    self.AddLog('\t' + '#'*4 + ' Agent is still not sure about any squares he could move to next and deciding to shoot an arrow...')
                    # Take the closest move
                    # Shoot arrow
                    onlyS = []
                    for pos in notVisited:
                        for a in self.agent.onlyS:
                            if self.IsAdjacentTo(pos, a):
                                onlyS.append([a,pos])
                                path = self.A_Star_Graph_Search(a, self.agent.curPos)
                                if path != []:
                                    paths.append(path)
                    
                    if onlyS and paths:
                        lens = [len(path) for path in paths]
                        minIdx = np.argmin(lens)
                        self.agent.path += paths[minIdx][1::]
                        self.agent.curPos = self.agent.path[-1]
                        self.score -= 10*(lens[minIdx]-1)
                        for p in paths[minIdx][1::]:
                            self.AddLog('\t' + '#'*8 + ' On the way to {}, At visited square {}'.format(self.ToWorldPos(self.agent.path[-1]), self.ToWorldPos(p)))
                        
                        #TODO: which dir to aim
                        notVisitedAdjs = self.GetNotVisitedAdjacents(self.agent.curPos)
                        found = False
                        for adj in notVisitedAdjs:
                            kbW =  self.KB.cnfWClauses.copy() + KB.ToCNF(self.ConsiderWumpus(adj)).copy()
                            if self.KB.AskW('W{}{}'.format(adj[0], adj[1]), kbW):
                                arrowDir = self.agent.ShootArrow(adj)
                                self.KB.TellW([['!W{}{}'.format(adj[0], adj[1])]])
                                found = True
                                self.AddLog('\t' + '#'*8 + ' Wumpus is definitely at {}'.format(adj))
                                break
                            else:
                                self.AddLog('\t' + '#'*8 + ' Not sure whether Wumpus is at {}'.format(adj))
                        if not found: # Take random dir
                            self.AddLog('\t' + '#'*8 + ' Shoot at random direction')
                            choice = random.choice(notVisitedAdjs)
                            arrowDir = self.agent.ShootArrow(choice)
                            self.KB.TellW([['!W{}{}'.format(choice[0], choice[1])]])
                        
                        self.OnShootArrowAction(arrowDir)
                        self.AddLog('\t' + '#'*8 + ' Agent shot an arrow in {} direction'.format(arrowDir))
                        self.AddLog('\t' + '#'*8 + ' Agent is sure that at least one safe square is in {} direction'.format(arrowDir))
                        self.AddLog('\t' + '#'*8 + ' Agent is going to repercept at this current square'.format(arrowDir))
                        self.agent.visited.pop(self.agent.visited.index(self.agent.curPos))
                        
                    else:
                        self.AddLog('\t' + '#'*4 + ' Agent could not make a reasonable shooting. Returning door...')
                        # Return door
                        doorPath = self.A_Star_Graph_Search(self.agent.doorPos, self.agent.curPos)
                        self.agent.path += doorPath[1::]
                        self.score -= 10*(len(doorPath)-1)
                        self.agent.curPos = self.agent.path[-1]
                        self.climbOut = True
                        self.score += 10
                                              
class Agent:
    def __init__(self):
        self.curPos = (0, 0)  
        self.path = []
        self.die = False
        self.visited = []
        self.considered = []
        self.direction = 'EAST'
        self.emptySquare = False
        self.onlyS = []
        self.onlyB = []
        self.doorPos = (0,0)
        self.nGold = 0
        self.nArrow = 0
        
    def ShootArrow(self, aimPos):
        if aimPos == self.curPos:
            return 'NONE'
        shootAt = ''
        if aimPos[0] == self.curPos[0]:
            if aimPos[1] > self.curPos[1]:
                shootAt = 'EAST'                
            if aimPos[1] < self.curPos[1]:
                shootAt = 'WEST'
        elif aimPos[1] == self.curPos[1]:
            if aimPos[0] > self.curPos[0]:
                shootAt = 'SOUTH'
            if aimPos[0] < self.curPos[0]:
                shootAt = 'NORTH'
                
        self.direction = shootAt
        self.nArrow += 1
        return shootAt

class KB:
    '''
    A KB containing CNF clauses
    '''
    def __init__(self):
        self.cnfWClauses = []
        self.cnfPClauses = []                
    @staticmethod
    def ToCNF(clause):
        '''
        clause: e.g., ['W22', ['S12', 'S23', 'S32', 'S21']] represents W22 <=> (S12 v S23 v S32 v S21)
        '''
        cnfClause = []
        cnfClause.append([KB.ToNegatedClause(clause[0])] + clause[1])   
        for x in clause[1]:
            cnfClause.append([clause[0], KB.ToNegatedClause(x)])
        
        return cnfClause
    
    def TellW(self, clauses):
        for clause in clauses:
            if clause not in self.cnfWClauses:
                for wClause in self.cnfWClauses:
                    if self.IsContract(clause[0], wClause[0]):
                        self.cnfWClauses.pop(self.cnfWClauses.index(wClause))
                        break                
                self.cnfWClauses.append(clause)
        
    def AskW(self, query, kb):        
        return self.PL_Resolution(query, kb)

    def TellP(self, clauses):
        for clause in clauses:
            if clause not in self.cnfPClauses:                           
                self.cnfPClauses.append(clause)

    def AskP(self, query, kb):        
        return self.PL_Resolution(query, kb)
    
    @staticmethod
    def ToNegatedClause(alpha):
        negated_alpha = '!' + alpha
        if negated_alpha.count('!') == 2:
            return negated_alpha[2::1]
        return negated_alpha
    
    def PL_Resolution(self, alpha, kb):  
        negated_alpha = KB.ToNegatedClause(alpha)
        new = []
        oldClauses = [[]]
        clauses = kb.copy() + [[negated_alpha]]
        while(True):
            for i in reversed(range(len(clauses))):
                if self.InClauses(clauses[i], oldClauses):
                    continue
                for j in range(len(clauses)):                    
                    resolvents = self.PL_Resolve(clauses[i], clauses[j])
                    for c in resolvents:
                        if c == []:
                            return True                    
                    new = self.Union(new, resolvents)                        
            if self.IsSubSet(new, clauses):
                return False
            oldClauses = clauses.copy()
            clauses = self.Union(clauses, new)

    def Union(self, l1, l2):
        if l2 != []:
            for x in l2:
                if not self.InClauses(x, l1):
                    l1.append(x)
        return l1
    
    def IsSubSet(self, l1, l2):
        for x in l1:
            if not self.InClauses(x, l2):
                return False
        return True            

    def ReducedClause(self, clause):
        res = []
        for x in clause:
            if x not in res:
                res.append(x)
        return res

    #def IsTautoClause(self, a):
    #    for x in a:
    #        for y in a:
    #            if self.IsContract(x, y):
    #                return True
    #    return False

    def IsContract(self, a, b):
        if len(a) == len(b):
            return False
        else:
            return a[1::] == b or b[1::] == a

    def InClauses(self, c, clauses):
        for x in clauses:
            if Counter(c) == Counter(x):
                return True
        return False

    def HasContract(self, l1, l2):
        for a in l1:
            for b in l2:
                if self.IsContract(a, b):
                    return True
        return False
        
    def PL_Resolve(self, ci, cj):
        res = []
        l1 = ci.copy()
        l2 = cj.copy()
        for a in l1:
            for b in l2:
                if self.IsContract(a, b):                                        
                    l1.pop(l1.index(a))
                    l2.pop(l2.index(b))
                    if self.HasContract(l1, l2):
                        return []

                    tmp = self.ReducedClause(l1 + l2)                                       
                    res.append(tmp)
                    return res
        return res       
    

if __name__ == '__main__':
    game = Game()
    game.ReadInput()
    game.Run()
    game.ToResultFile('result.txt')