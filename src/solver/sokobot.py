import time
from .helperStructures import State, Direction
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
            playerAccess = getAccessibleArea(width, height, walls, boxes, player)   #Flood fill algorithm, could find a faster one
            #Initializes the Initial State and the Goal State
            initial = State(boxes, playerAccess)
            goal = State(targets, playerAccess)

            #We are NOT using a list for the frontier, but for now i am doing this as I can't think
            frontier = []
            explored = set()
            frontier.append(initial)
            while frontier:
                #Grab the highest priority frontier state
                exploring = frontier[0]

                #Check if what is being explored is the goal
                if exploring.areBoxesEqual(goal):
                    print("Goal Reached")
                    break

                #Get the list of actions from this state
                actionSet = getActions(width, height, walls, exploring)
                #Generate every new State and add it to frontier
                for action in actionSet:
                    newState = createState(width, height, walls, exploring, action)
                    if (newState not in explored):
                        frontier.append(newState)

                explored.add(exploring)
                frontier.pop(0)

        except Exception as ex:
            print(ex)
        return "lrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlr"

#Floodfill algorithm to check the player's access area, currently just using BFS
#Prints out 1 and 0 whether a space is occupied or not
#This is used to generate possible actions by checking if a box is within the range of the accesible area
#Example Grid:
"""
00000000
00111110
00000010
00000010
00000000
"""
#In the grid above, the 1s represent the spaces the bot can move into and the 0 either represents a wall or a box
def getAccessibleArea(width, height, walls, boxes, playerPos):
    #Initializes an empty map
    grid = [[0 for x in range(width)] for y in range(height)]
    explored = set()
    blocked = walls.union(boxes)

    q = deque()
    q.append(playerPos)

    while q:
        pos = q.popleft()
        grid[pos[0]][pos[1]] = 1

        up = (pos[0]-1, pos[1])
        down = (pos[0]+1, pos[1])
        left = (pos[0], pos[1]-1)
        right = (pos[0], pos[1]+1)
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

#This returns the possible actions based on the accessible area
#It checks the coordinates of each box and checks if those coordinates are within the range of the accesible area
#Using the example grid from getAccessibleArea:
"""
00000000
00111110
00200010
00000010
00000000
"""
#For the sake of representation, 2 is the box which is at coordinates (2,2) (stored in currentState.boxes)
#It will first check the possible area(up, down, left, right) that the boxed can be moved into using blocked
#If the area is not blocked, it will then use accesible area to check if that box can be moved from the opposite direction of the movement.
#Ex: The down coordinates of the box is free/not blocked. Since the accessible area has 1 on the up of the box, this means that pushing the box
#downwards is indeed a valid movement
#This movement is then added to the actionSet which is all the possible actions from this current state
def getActions(width, height, walls, currentState):
    actionSet = set()

    blocked = walls.union(currentState.boxes)
    accessible = currentState.playerAccess
    
    for box in currentState.boxes:
        up = (box[0]-1, box[1])
        down = (box[0]+1, box[1])
        left = (box[0], box[1]-1)
        right = (box[0], box[1]+1)
        #The accesible coordinates is the position beside the box at the opposite direction of the push
        #Up push means check if accesible from the free position at down of the box

        #Up Push. box[0] + 1][box[1] is the coordinates of down. same with the other directions
        if accessible[box[0] + 1][box[1]] and up not in blocked:
            actionSet.add((box,Direction.UP))
        #Down Push
        if accessible[box[0] - 1][box[1]] and down not in blocked:
            actionSet.add((box,Direction.DOWN))
        #Left Push
        if accessible[box[0]][box[1]+1] and left not in blocked:
            actionSet.add((box,Direction.LEFT))
        #Right Push
        if accessible[box[0]][box[1]-1] and right not in blocked:
            actionSet.add((box,Direction.RIGHT))
    
    return actionSet

def createState(width, height, walls, exploring, action):
    boxes = set(exploring.boxes)
    target = action[0]
    direction = action[1]

    boxes.remove(target)
    boxes.add((target[0] + direction.row, target[1] + direction.column))

    #Player should be standing in the opposite direction of where they pushed the box, so we can call the search here
    player = (target[0] - direction.row, target[1] - direction.column)

    playerAccess = getAccessibleArea(width, height, walls, boxes, player)   #Flood fill algorithm, could find a faster one

    return State(boxes,playerAccess)

#For testing
def printGrid(grid):
    for x in range(len(grid)):
        for y in range(len(grid[x])):
            print(grid[x][y], end="")
        print()
