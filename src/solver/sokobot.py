import time, heapq
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

            # push sequence - the sequence of pushes from the start to the goal
            pushSeq = Astar(width,height,walls,initial,goal,targets)
            """
            pushSeq (or the A* search) returns a list of pushes needed to reach the solution.
            Output format is such: [((row, col), Direction)]
                (row,col) = represents the coordinates of the box being pushed
                Direction = the direction of the push
            
            Example using resulting list from testlevel:
                pushSeq = [ ((3,4), Direction.LEFT), 
                            ((3,3), Direction.LEFT),
                            ((3,2), Direction.LEFT),
                            ((2,2), Direction.DOWN),
                            ((2,3), Direction.UP),
                            ((2,4), Direction.DOWN),
                            ((1,3), Direction.RIGHT)
                          ]
                Description:
                1. Push box at 3,4 to the left
                2. Push box at 3,3 to the left (target)
                3. Push box at 3,2 to the left (final target)
                4. Push box at 2,2 down (final target)
                5. Push box at 2,3 up
                6. Push box at 2,4 down (final target)
                7. Push box at 1,3 to the right (final target)
            """

            print(*pushSeq)

        except Exception as ex:
            print(ex)
        return "lrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlr"

# Start of A* stuff
class Node:
    """Class representing a node."""
    def __init__(self,state,parent=None,push=None):
        """Initialize the node with its state, parent, and push"""
        self.state = state      # state in the node
        self.parent = parent    # parent node
        self.push = push        # push that lead to this node

        self.cost = 0           # cost: box pushes made so far
        self.heuristic = 0      # heuristic: manhattan distance of boxes to targets
        self.total = 0          # cost and heuristic total 

    def __lt__(self,other):
        # Tie-breaking rule for the priority queue based on total
        return self.total < other.total

    
def totalManhattanDist(state,targets):
    """
    The sum of the manhattan distance of each box to its nearest target.
    In order to get an estimate of how many pushes are needed in total for the given state.
    """
    total = 0
    for box in state.boxes:
        distance = [abs(box[0] - target[0]) + abs(box[1] - target[1]) for target in targets]
        total += min(distance)

    return total

def Astar(width,height,walls,initial, goal, targets):
    """ 
    A* search algorithm
    returns the list of pushes needed in order to get to the goal state
    """
    startNode = Node(initial)
    startNode.heuristic = totalManhattanDist(initial,targets)
    startNode.total = startNode.heuristic

    frontier = []           # Priority queue of nodes waiting to be explored
    fDic = {initial}        # Dictionary of States already in the frontier for faster lookup
    explored = set()        # States already explored

    heapq.heappush(frontier,startNode)

    while frontier:
        curNode = heapq.heappop(frontier)
        curState = curNode.state
        fDic.remove(curState)
        explored.add(curState)

        # Check if the current state is the goal
        if curState.areBoxesEqual(goal):
            pushes = []
            node = curNode
            while node.parent is not None:
                pushes.append(node.push)
                node = node.parent
            pushes.reverse()
            print("Goal Reached")
            return pushes

        for push in getActions(walls,curState):
            newState = createState(width,height,walls,curState,push)

            if newState in explored:
                continue

            curCost = curNode.cost + 1

            if newState not in fDic:
                newNode = Node(newState,curNode,push)
                newNode.cost = curCost
                newNode.heuristic = totalManhattanDist(newState,targets)
                newNode.total = newNode.cost + newNode.heuristic

                heapq.heappush(frontier,newNode)
                fDic.add(newState)
            else:
                for node in frontier:
                    if node.state == newState and curCost < node.cost:
                        node.cost = curCost
                        node.total = node.cost + node.heuristic
                        node.parent = curNode
                        node.push = push
                        heapq.heapify(frontier)
                        break

    return None

# End of A* stuff

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
def getActions(walls, currentState):
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
