import time, heapq
from .helperStructures import State, Direction
from .sokobit import SokoBit
from collections import deque

# python -m src.main.driver 14 bot

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

# maps the Direction enum to its corresponding letter representation; this is used to build the final return string
LETTERS = {
    Direction.UP: 'u',
    Direction.DOWN: 'd',
    Direction.LEFT: 'l',
    Direction.RIGHT: 'r'
}

class SokoBot:
    def solveSokobanPuzzle(self, width, height, mapData, itemsData):
        try:
            useBitMapVersion = False
            if(useBitMapVersion):
                tempObj = SokoBit()
                return tempObj.solveSokobanPuzzle(width, height, mapData, itemsData)
            
            #Reads the initial data and saves them as a set of coordinates
            walls = set()
            boxes = set()
            targets = set()
            floor = set()
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
                    if mapData[row][col] == ' ':
                        floor.add((row,col))


            #Gets the initial area the player can access without pushing
            playerAccess = getAccessibleArea(width, height, walls, boxes, player)   #Flood fill algorithm, could find a faster one
            #Initializes the Initial State and the Goal State
            initial = State(boxes, playerAccess)
            goal = State(targets, playerAccess)

            pushMap = getPushMap(width, height, mapData, targets)

            # push sequence - the sequence of pushes from the start to the goal
            pushSeq = Astar(width,height,walls,initial,goal,targets,pushMap)
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

            #print(*pushSeq)

        except Exception as ex:
            print(ex)
        return boxPushesToMoves(pushSeq, player, boxes, walls)

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

def getPushMap(width, height, mapData, targetCoords):
    """
    BFS from each target to each cell on the map to get the amount of pushes a coordinate needs to reach the nearest target
    returns a bitmap (?) of the distance (in pushes) of each cell to a target

    Example using testlevel:
          # # # # # #
          # x 1 0 x #
        # # 1 2 1 x #
        # 0 0 1 0 x #
        # # # # # # #

        0 = target
        x = deadlock
        1,2 = pushes to the nearest target
    """

    pushCount = {}
    queue = deque(targetCoords)

    for target in targetCoords:
        pushCount[target] = 0

    while queue:
        r,c = queue.popleft()
        for dir in Direction:
            i,j = dir.row, dir.column

            box = r-i, c-j       # box position
            pos = r-2*i, c-2*j   # player position

            isValid = isFloor(width,height,mapData,*box) and isFloor(width,height,mapData,*pos)

            if isValid and box not in pushCount:
                pushCount[box] = pushCount[(r,c)] + 1
                queue.append(box)

    pushMap = [999] * (width * height)
    for (r,c), pushCtr in pushCount.items():
        pushMap[(height - (r+1)) * width + (width-(c+1))] = pushCtr
    return pushMap

def isFloor(width, height, mapData, r, c):
    return 0 <= r < height and 0 <= c < width and mapData[r][c] != '#'

def pushManHattan(state, pushMap):
    return sum(pushMap[box] for box in state.boxes)

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

def Astar(width,height,walls,initial, goal, targets, pushMap):
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



    deadCells = detectSimpleDeadlock(width, height, walls, targets)
    # will add other pruning here 

    # TIME_LIMIT = 15
    # startTime = time.monotonic()
    count = 0
    while frontier:
        count += 1
        #print(count)
        # if time.monotonic() - startTime > TIME_LIMIT:
        #     print("Time Limit Reached")
        #     break


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
        
        for push in getActions(walls, curState, deadCells, width, height, targets):
            box, dirP = push

            movedBox = (box[0] + dirP.row, box[1] + dirP.column)
            # records new boxes after the push
            newBoxes = (curState.boxes - {box}).union({movedBox})

            # check if movedBox in newBoxes state hits frozen deadlock
            # if frozen, skip creating new state
            if detectFrozenDeadlock(movedBox,newBoxes,walls,deadCells,targets):
                continue
            
            newState = createState(width,height,walls,curState,push)

            if newState in explored:
                continue

            curCost = curNode.cost + 1

            if newState not in fDic:
                newNode = Node(newState,curNode,push)
                newNode.cost = curCost
                # can compute push cost between box and target for all targets use that as new heuristic?
                # newNode.heuristic = totalManhattanDist(newState,targets)
                # use revisedlookup
                newNode.heuristic = pushManHattan(newState,pushMap)
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
    explored.add(playerPos)
    
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



# inaccessible but floor ?

def getCorral(accessible, width, height, walls, boxes):
    # uses accessible area grid 
    # to check if theres no corral region / compare to 0 matrix then proceed to other pruning methods

    corralCells = set()

    # looks for corral region
    for x in range(height):
        for y in range(width):
            if not accessible[x][y] and (x,y) not in walls and (x,y) not in boxes:
                corralCells.add((x,y))

    # separate corralCells into area and boundary
    corralRegion = []
    explored = set()

    cellQ = deque()
    corrals = []
    
    # for each corral cell, check neighbors
    for cell in corralCells:
        if cell in explored:
            continue

        area, boundary = set(), set()
        cellQ.append(cell)
        explored.add(cell)

        # check neighbors of each cell and add to queue
        while cellQ:
            
            cell = cellQ.popleft()

            # all cells are already corral cell so automatically add them
            area.add(cell)


            # looks at neighboring cells
            up = (cell[0]-1, cell[1])
            down = (cell[0]+1, cell[1])
            left = (cell[0], cell[1]-1)
            right = (cell[0], cell[1]+1)

            # neighbor check
            for n in (up,down,left,right):
                if n in boxes:
                    boundary.add(n)
                elif n not in explored and n in corralCells:
                    explored.add(n)
                    cellQ.append(n)

        corrals.append((area,boundary))
        # once cellQ is exhausted / no corral cells remaining, split is complete
        # add each "pocket" or corral area to list of tuples (area, boundary)

    return corrals


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
def getActions(walls, currentState, deadCells, width, height, targets):
    actionSet = set()
    
    blocked = walls.union(currentState.boxes)
    accessible = currentState.playerAccess
    corrals = getCorral(accessible, width, height, walls, currentState.boxes)
    #print(corrals)
    
    # initialize candidate boxes to currentstate boxes 
    # this is so that we can try every box by default, and apply pruning
    # when PI corral is found
    candidateBoxes = currentState.boxes

    # go through each corral pocket
    for area, boundary in corrals:
        # check if PI (player accessible and can be pushed inwards towards the corral)
        if isPI(area, boundary, accessible, blocked, deadCells, targets):
            # if PI, only set boundaries as candidate boxes
            candidateBoxes = boundary
            break


    for box in candidateBoxes:
        up = (box[0]-1, box[1])
        down = (box[0]+1, box[1])
        left = (box[0], box[1]-1)
        right = (box[0], box[1]+1)
        #The accesible coordinates is the position beside the box at the opposite direction of the push
        #Up push means check if accesible from the free position at down of the box

        #Up Push. box[0] + 1][box[1] is the coordinates of down. same with the other directions
        if accessible[box[0] + 1][box[1]] and up not in blocked and up not in deadCells:
            actionSet.add((box,Direction.UP))
        #Down Push
        if accessible[box[0] - 1][box[1]] and down not in blocked and down not in deadCells:
            actionSet.add((box,Direction.DOWN))
        #Left Push
        if accessible[box[0]][box[1]+1] and left not in blocked and left not in deadCells:
            actionSet.add((box,Direction.LEFT))
        #Right Push
        if accessible[box[0]][box[1]-1] and right not in blocked and right not in deadCells:
            actionSet.add((box,Direction.RIGHT))
    
    return actionSet

# Empty floor for reverse search for deadlocks
# Removes all boxes except for walls and targets
def getEmptyFloor(width, height, walls):
    #Initializes an empty map
    grid = [[0 for x in range(width)] for y in range(height)]
    
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            if ((y, x)) not in walls:
                grid[y][x] = 1

    return grid



def isPI(area, boundary, accessible, blocked, deadCells, targets):
    # check if all boundary boxes are already solved / in targets
    # check if theres no target inside the corral pocket
    if all(box in targets for box in boundary) and not any(cell in targets for cell in area):
        return False


    # looks at all directions to see if pushes go inward (valid) / outward / sideward
    for box in boundary:
        for direction in Direction:
            dy = direction.row
            dx = direction.column

            boxLandingPos = (box[0]+dy, box[1]+dx)
            playerSide = (box[0]-dy, box[1]-dx)

            if boxLandingPos in area:
                if boxLandingPos not in deadCells and not accessible[playerSide[0]][playerSide[1]]:
                    return False

            # if not in area
            else:
                if accessible[playerSide[0]][playerSide[1]] and boxLandingPos not in blocked and boxLandingPos not in deadCells:
                    return False
    return True
    


# Algorithm used here is a reverse search wherein a box is placed in the targets and a "player" attempts to pull
# If a player was able to pull, its a good square, if not then its a dead square
# For pruning in getActions
def detectSimpleDeadlock(width, height, walls, targets):
    validFloorCells = getEmptyFloor(width, height, walls)
    
    # All squares from which a box can potentially reach a target
    goodCell = set(targets)
    q = deque(targets)

    while q:
        box = q.popleft() 

        for direction in Direction:
            dy = direction.row
            dx = direction.column
            
            boxPullPos = (box[0] - dy, box[1] - dx)
            playerPullPos = (box[0] - (dy * 2), box[1] - (dx * 2))
            
            #Check if boxPullPos and playerPullPos are within bounds
            if not (0 <=  boxPullPos[0] < height and
               0 <= boxPullPos[1] < width and
               0 <= playerPullPos[0] < height and
               0 <= playerPullPos[1] < width):
                continue
            
            if validFloorCells[boxPullPos[0]][boxPullPos[1]] and validFloorCells[playerPullPos[0]] [playerPullPos[1]]:
                if boxPullPos not in goodCell:
                    goodCell.add(boxPullPos)
                    q.append(boxPullPos)

    # Every non-wall tile not found by reverse search is a dead square.
    deadCell = set()

    for y in range(height):
        for x in range(width):
            cell = (y, x)

            if cell not in goodCell:
                deadCell.add(cell)

    return deadCell

def isFrozen(box, boxes, walls, deadCells, checking):
    checking = checking.union({box})
    # treats box currently being checked as a wall 
    # so that when u recurse into neigboring boxes it looks at box as something you can't move
    # like A checks B, B checks A (where A and B are directly neighboring boxes)
    blocked = walls.union(checking)

    up = (box[0]-1, box[1])
    down = (box[0]+1, box[1])
    left = (box[0], box[1]-1)
    right = (box[0], box[1]+1)

    horizontalBlock = ( left in blocked or right in blocked
                       or (left in deadCells and right in deadCells)
                       or (left in boxes and isFrozen(left,boxes,walls,deadCells,checking))
                       or (right in boxes and isFrozen(right,boxes,walls,deadCells,checking))
                    )

    verticalBlock = ( up in blocked or down in blocked
                           or (up in deadCells and down in deadCells)
                           or (up in boxes and isFrozen(up,boxes,walls,deadCells,checking))
                           or (down in boxes and isFrozen(down,boxes,walls,deadCells,checking))
                     )

    return horizontalBlock and verticalBlock

    
def detectFrozenDeadlock(movedBox, boxes, walls, deadCells, targets):
    toCheck = [movedBox]

    up = (movedBox[0]-1, movedBox[1])
    down = (movedBox[0]+1, movedBox[1])
    left = (movedBox[0], movedBox[1]-1)
    right = (movedBox[0], movedBox[1]+1)

    # check if there's directly neighboring box
    for n in (up,down,left,right):
        if n in boxes:
            toCheck.append(n)

    # checks is box is unsolved and frozen 
    for box in toCheck:
        if box not in targets and isFrozen(box, boxes, walls, deadCells, set()):
            return True

    return False


#def detectFrozenDeadlock(width, height, walls, targets):
# box beside another box (cant push opposite sides (ex check if vertical freeze), may be pushed horizontally)
# box beside 
                
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

# This finds the path from player start position to goal position using BFS (path for EACH box)
# for context: the goal position is the position beside the box opposite of the direction of the push
def findPath(start, goal, walls, boxes):
    if start == goal:
        return ""

    blocked = walls.union(boxes)

    # dict to store prev position as (x,y) in this case, I just called it start; and direction as char, which is "None" at the start
    cameFrom = {start: None}

    q = deque()
    q.append(start)
    
    # while loop to explore the grid until we reach the goal (BFS)
    while q:
        currPos = q.popleft()

        for direction in Direction:
            # calculates the new position based on the current position and the direction of movement
            newPos = (currPos[0] + direction.row, currPos[1] + direction.column)
            if newPos in blocked or newPos in cameFrom:
                continue

            # sets the previous position and direction for the new position in the cameFrom dictionary
            # this kind of simulates the way we solve Frontier and Explored in class
            # ex. cameFrom[(x,y)] = ((prevX, prevY), direction) to show where (x,y) came from and what direction we took to get there
            # take note that direction is parsed into its corresponding character here, as seen in the LETTERS dictionary above
            cameFrom[newPos] = (currPos, LETTERS[direction])

            # once we reach the goal, reconstruct path
            if newPos == goal:
                return reconstructPath(cameFrom, start, goal)

            # if goal is not reached, continue exploring
            else:
                q.append(newPos)

    return None

# This reconstructs the path from the goal position back to the start position using the cameFrom dictionary
# It works by tracing backwards from goal to start, appending the direction 
def reconstructPath(cameFrom, start, goal):
    path = ""
    cell = goal

    # traces back from goal to start
    while cameFrom[cell] is not None:
        # cameFrom's (prevX, prevY) is assigned to 'prev' and the direction taken to get to (x,y) is assigned to 'direction'
        prev, direction = cameFrom[cell]
        # path string is built by appending the direction
        path += direction
        # cell is updated to the previous cell to continue tracing back
        cell = prev

    # reverses the path string to get the correct order from start to goal 
    return path[::-1]


# This function takes the push sequence (basically, the single final push to get the box to the target) 
# from A* and converts it into a string of moves for the player to execute
# It does this by finding running findPath (which finds the path from player's current position to position beside the box opposite the direction of the push) 

# The result of this function is what is returned to the main.py file and printed out / used as the final solution
def boxPushesToMoves(pushSeq, player, boxes, walls):
    moves = ""

    currentBoxes = set(boxes)
    
    for push in pushSeq:
        boxGoal, direction = push
        # sets coords of player to position beside the box opposite of target
        playerReadyPos = (boxGoal[0] - direction.row, boxGoal[1] - direction.column)
        moves += findPath(player, playerReadyPos, walls, currentBoxes)
        # adds extra letter to string for the actual push to target
        moves += LETTERS[direction]
        # player assumes old pos of box after push
        player = boxGoal
        currentBoxes.remove(boxGoal)
        # box is now in the new position
        currentBoxes.add((boxGoal[0] + direction.row, boxGoal[1] + direction.column))

    return moves

#For testing
def printGrid(grid):
    for x in range(len(grid)):
        for y in range(len(grid[x])):
            print(grid[x][y], end="")
        print()


