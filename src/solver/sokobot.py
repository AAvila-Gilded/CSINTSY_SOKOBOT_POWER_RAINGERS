import time
from collections import deque

#TO DO:
#Get a way to generate actions from a state
#Make an algorithm to explore actions
#Make a way to generate the resulting state
#Make a way to end the search early for deadend states

#Ideas to make it faster
#Switch to bits (I will be making an alt file converting things to a bitboard to check the performance, if yall don't wanna deal with that, you can continue working here and I will just convert new methods over there)
#Get a better floodfill algorithm or
#Get a better method for checking what boxes a player can access or
#Find a way to update the playerAccess grid when moving from one state to another
#Find better algorithms than bfs (maybe some heuristics that could prioritize better paths? maybe we could look up normal sokoban strats or smthn)

class SokoBot:
    def solveSokobanPuzzle(self, width, height, mapData, itemsData):
        try:
            #Reads the initial data and saves them as a set of coordinates
            walls = set()
            boxes = set()
            targets = set()
            player = ()
            #Gets the current positions of each object in the maze
            for row in range(height):
                for col in range(width):
                    if itemsData[row][col] == '$':
                        boxes.add((row,col))
                    if itemsData[row][col] == '@':
                        player = (row,col)
                    if mapData[row][col] == '#':
                        walls.add((row,col))
                    if mapData[row][col] == '.':
                        targets.add((row,col))

            #Gets the initial area the player can access without pushing
            #Flood fill algorithm, could find a faster one
            playerAccess = getAccessibleArea(width, height, player, walls, boxes)

            #Initializes the Initial State and the Goal State
            initial = State(boxes, playerAccess)
            goal = State(targets, playerAccess)

            #Make something to generate possible moves from initial state


            #Make something to generate new state

            #Make hashset equals override for the state

        except Exception as ex:
            print(ex)
        return "lrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlr"

#Floodfill algorithm to check the player's access area, currently just using BFS
def getAccessibleArea(width, height, playerPos, walls, boxes):
    #Initializes an empty map
    grid = [[0 for x in range(width)] for y in range(height)]
    explored = set()
    blocked = walls.union(boxes)

    q = deque()
    q.append(playerPos)

    while q:
        pos = q.popleft()
        grid[pos[0]][pos[1]] = 1

        up = (pos[0]-1,pos[1])
        down = (pos[0]+1,pos[1])
        left = (pos[0],pos[1]-1)
        right = (pos[0],pos[1]+1)
        if up not in blocked and up not in explored:
            q.append(up)
            explored.add(up)
        if down not in blocked and down not in explored:
            q.append(down)
            explored.add(down)
        if left not in blocked and left not in explored:
            q.append(left)
            explored.add(left)
        if right not in blocked and right not in explored:
            q.append(right)
            explored.add(right)

    return grid

def getActions(playerAccess, boxes, walls):
    for x in boxes:
        pass

#For testing
def printGrid(grid):
    for x in range(len(grid)):
        for y in range(len(grid[x])):
            print(grid[x][y], end="")
        print()


#Extra Objects
class State:
    #Constructor Method, boxes contain the coordinates of the boxes and playerAccess contains the area the player can access without any pushes
    def __init__(self, boxes, playerAccess):
        self.boxes = frozenset(boxes)
        self.playerAccess = tuple(map(tuple,playerAccess))

    #Equality Override, States are equal if they have the same set of Boxes and PlayerAccess
    def __eq__(self, other):
        return self.boxes == other.boxes and self.playerAccess == other.playerAccess

    #A function to check if the current state has the same box positions as another state. For testing if its equal to the goal state as the current player position is unimportant here
    def areBoxesEqual(self, other):
        return self.boxes == other.boxes

    #Hash Override, sets the hash to use the tuple of box coordinates and player access.
    def __hash__(self):
        return hash((self.boxes,self.playerAccess))
