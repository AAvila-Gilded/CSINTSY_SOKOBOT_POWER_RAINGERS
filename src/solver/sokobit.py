import time, heapq
from .helperBit import State, Direction
from collections import deque
from scipy.optimize import linear_sum_assignment
import traceback

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

shifts = {

}

gwidth = -1
gheight = -1
gameBox = -1
useHungarian = True

class SokoBit:
    def solveSokobanPuzzle(self, width, height, mapData, itemsData):
        try:
            """
                Creates a mask that encompasses the whole game area by left shifting 1 width*height times then subtracting one.
                For example, a 3x3 grid. Left shift 1 9 times.
                            1
                000      000
                000  ->  000
                001      000
                Then you subtract one.
                  1
                000      111
                000  ->  111
                000      111
                Making a mask that encompasses the grid.
            """
            global gwidth, gheight, gameBox, shifts
            gwidth = width
            gheight = height
            gameBox = (1 << (width*height)) - 1
            shifts = {
                Direction.UP: width,
                Direction.DOWN: -width,
                Direction.LEFT: 1,
                Direction.RIGHT: -1
            }
            """
                Creates a mask for the whole left column of the game area. << width - 1 shifts the bit to the left side, and x*width shifts it up by x rows.
                Example: 3x3 grid, width 3, height 3
                1 << (0 * 3 + 3 - 1) = 1 << (2)     1 << (1 * 3 + 3 - 1) = 1 << (5)     1 << (2 * 3 + 3 - 1) = 1 << (8)
                000                                 000                                 100
                000                                 100                                 000
                100                                 000                                 000
                Getting their sum:
                000   000   100   100
                000 + 100 + 000 = 100
                100   000   000   100
            """
            leftColumn = sum(1 << (x * width + width - 1) for x in range(height))
            """
                Same here but just without shifting it to the left side
            """
            rightColumn = sum(1 << (x * width) for x in range(height))

            walls = 0
            boxes = 0
            targets = 0
            targetCoords = []
            player = 0

            #Reads the initial data and saves them as 2d bitmaps
            #Gets the current positions of each object in the maze
            """
                bitmap |= (1 << ((height-(row+1))*width) << (width-(col+1)))
                This command sets a bit to 1 at the target row and column.

                << ((height-(row+1))*width) moves it to the target row. Ex. 3x3 grid on row 1
                ((3 - (1+1)) * 3) -> ((3 - 2) * 3) -> (1*3) -> 3, left shift by 3
                000      000
                000  ->  001
                001      000
                The 1 moved up to row 1. (The top row is the 0th row).

                << (width - (col+1)) moves it to the target column. Ex. 3x3 grid on column 1
                (3 - (1+1)) -> (3 - 2) -> 1, left shift by 1
                000    000
                001 -> 010
                000    000
                The 1 moved left to column 1. (The left row is the 0th column).

                |= is the OR-assignment bit operator, it works similarly to +=. Ex.
                111   000   111
                000 | 010 = 010
                000   000   000
                It applies the OR operation on both bitmaps and assigns the resulting value to the first.
            """
            for row in range(height):
                for col in range(width):
                    if itemsData[row][col] == '$':
                        boxes |= (1 << ((height-(row+1))*width) << (width-(col+1)))
                    if itemsData[row][col] == '@':
                        player = (1 << ((height-(row+1))*width) << (width-(col+1)))
                    if mapData[row][col] == '#':
                        walls |= (1 << ((height-(row+1))*width) << (width-(col+1)))
                    if mapData[row][col] == '.':
                        targets |= (1 << ((height-(row+1))*width) << (width-(col+1)))
                        targetCoords.append((row,col))

            #Builds a lookup table so getting the manhattan distance for each box is O(1)
            #Basically since target positions don't change, we just precompute the distance from each square
            # updated: lookup table for push amount to a target; like a heatmap for the entire grid
            pushMap = getPushMap(walls,targets)
            # print(pushMap)

            #Gets the number of targets needed
            targetNum = len(targetCoords)

            #Gets the initial area the player can access without pushing
            playerAccess = getAccessibleArea(walls, boxes, player)

            #Initializes the Initial State and the Goal State
            initial = State(boxes, playerAccess)
            goal = State(targets, playerAccess)

            # push sequence - the sequence of pushes from the start to the goal
            targetPushMaps = getTargetPushMaps(walls, targets)
            pushSeq = Astar(walls,targetNum,pushMap,initial,goal,targets,targetPushMaps)
            # print(pushSeq)
            """
                pushSeq (or the A* search) returns a list of pushes needed to reach the solution.
                Output format is such: [(boxIndex, Direction)]
                    boxIndex = represents the coordinates of the box being pushed
                    Direction = the direction of the push
                
                Example using resulting list from testlevel:
                    pushSeq = [ (512, Direction.LEFT), 
                                (1024, Direction.LEFT),
                                (2048, Direction.LEFT),
                                (262144, Direction.DOWN),
                                (131072, Direction.UP),
                                (65536, Direction.DOWN),
                                (16777216, Direction.RIGHT)
                            ]
                    Description (The bottom right corner is index 1, with coordinates of (height, width)):
                    1. Push box at 3,4 (512) to the left
                    2. Push box at 3,3 (1024) to the left (target)
                    3. Push box at 3,2 (2048) to the left (final target)
                    4. Push box at 2,2 (262144) down (final target)
                    5. Push box at 2,3 (131072) up
                    6. Push box at 2,4 (65536) down (final target)
                    7. Push box at 1,3 (16777216) to the right (final target)
            """

            #print(*pushSeq)
            return boxPushesToMoves(pushSeq, player, boxes, walls)
        except Exception as ex:
            print(ex)
            traceback.print_exc()
            return "lrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlrlr"



def getPushMap(walls, targets):
    """
    BFS from each target to each cell on the map to get the amount of pushes a coordinate needs to reach the nearest target
    returns a look-up table of the distance (in pushes) of each cell to a target

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

    floor = walls ^ gameBox
    # printBitMap(floor,width,height)
    pushCount = {}
    targetArray = getIndivBits(targets)
    queue = deque(targetArray)

    for target in targetArray:
        pushCount[target] = 0

    while queue:
        pos = queue.popleft()
        # print(bitToIndex(pos))
        boxPos = 0
        playerPos = 0
        for dir in Direction:
            shift = shifts[dir]
            if shift > 0:
                boxPos = pos << shift
                playerPos = boxPos << shift
            else:
                boxPos = pos >> -shift
                playerPos = boxPos >> -shift

            isValid = boxPos & floor and playerPos & floor

            if isValid and boxPos not in pushCount:
                pushCount[boxPos] = pushCount[pos] + 1
                queue.append(boxPos)

    pushMap = [999] * (gwidth * gheight)
    for pos, pushCtr in pushCount.items():
        pushMap[bitToIndex(pos)] = pushCtr
    return pushMap

def getTargetPushMaps(walls, targets):
    targetBits = getIndivBits(targets)
    return [getPushMap(walls,t) for t in targetBits]

def getHungarian(targetPushMaps,boxes):
    boxBits = getBitIndices(boxes)
    cost = [[m[bitmap] for m in targetPushMaps] for bitmap in boxBits]
    row, col= linear_sum_assignment(cost)

    total = 0
    for k in range(len(row)):
        c = cost[row[k]][col[k]]
        if c >= 999:
            return 999
        total += c

    return total

#Helper Bit Functions
def getBitIndices(bitmap):
    """
        This returns the indices of all set bits in the bitmap.
        -bitmap switches all 1s to 0s and 0s to 1s, then adds one, basically acting like the Two's Complement System when switching from positive to negative.
        Example:
        - (101011100100)
        -> 010100011011
        +1 010100011100
        bitmap & -bitmap gets the lowest set bit by using the AND bitwise operator.
        101011100100 &
        010100011100 =
        000000000100
        Afterwards: just run bit_length(), (here it returns 3), and subtract 1 (zero indexing) to get the location of the bit.
    """
    indices = []
    while(bitmap):
        lowestSetBit = bitmap & -bitmap
        indices.append(lowestSetBit.bit_length()-1)
        bitmap ^= lowestSetBit
    return indices

def getIndivBits(bitmap):
    """
        Similar to getBitIndices() but just returns the value of the bit instead of transforming it into its index.
    """
    indivBits = []
    while(bitmap):
        lowestSetBit = bitmap & -bitmap
        indivBits.append(lowestSetBit)
        bitmap ^= lowestSetBit
    return indivBits

def bitToIndex(bitmap):
    """
        Works like getBitIndices but for just 1 bitmap.
    """
    return (bitmap & -bitmap).bit_length()-1

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
        if self.total != other.total:
            return self.total < other.total
        
        # if same total, check the one closer to the goal.
        return self.heuristic < other.heuristic 

def totalManhattanDist(state,pushMap):
    """
    The sum of the manhattan distance of each box to its nearest target.
    In order to get an estimate of how many pushes are needed in total for the given state.
    """

    """
        Equivalent normal loop
        total = 0
        for box in getIndivBits(state.boxes):
            #This is just getting the precomputed manhattan distance
            total += pushMap[box]

        return total
    """
    #Alternate single line return
    return sum(pushMap[box] for box in getBitIndices(state.boxes))

def Astar(walls,targetNum,pushMap,initial,goal,targets,targetPushMaps):
    """ 
    A* search algorithm
    returns the list of pushes needed in order to get to the goal state
    """
    startNode = Node(initial)
    startNode.heuristic = 0
    if useHungarian:
        startNode.heuristic = getHungarian(targetPushMaps,initial.boxes)
    else:
        startNode.heuristic = totalManhattanDist(initial,pushMap)
    startNode.total = startNode.heuristic

    frontier = []           # Priority queue of nodes waiting to be explored
    fDic = {initial}        # Dictionary of States already in the frontier for faster lookup
    explored = set()        # States already explored

    heapq.heappush(frontier,startNode)
    deadCells = detectSimpleDeadlock(walls, targets)

    TIME_LIMIT = 15
    # startTime = time.monotonic()
    count = 0
    while frontier:
        count += 1
        # print(count)
        # if time.monotonic() - startTime > TIME_LIMIT:
        #     print("Time Limit Reached")
        #     print(count)
        #     break
        floor = walls ^ gameBox
        curNode = heapq.heappop(frontier)
        curState = curNode.state
        fDic.remove(curState)
        explored.add(curState)

        # Check if the current state is the goal
        if (curState.checkProgress(goal) >= targetNum):
            pushes = []
            node = curNode
            while node.parent is not None:
                pushes.append(node.push)
                node = node.parent
            pushes.reverse()
            print(f"Goal Reached {count}")
            return pushes
        
        for push in getActions(walls, curState, deadCells, targets):            
            newState = createState(walls,curState,push)

            if newState in explored:
                continue

            #Could switch this off to simulate gbfs
            curCost = curNode.cost + 1

            if newState not in fDic:
                newNode = Node(newState,curNode,push)
                newNode.cost = curCost
                if useHungarian:
                    newNode.heuristic = getHungarian(targetPushMaps,newState.boxes)
                else:
                    newNode.heuristic = totalManhattanDist(newState,pushMap)
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

def getAccessibleArea(walls, boxes, player):
    """
        Breadth-First-Search Floodfill Algorithm.
        Returns a bitmap of the player's accessible area.
    """
    #Original Description
    """
        #Floodfill algorithm to check the player's access area, currently just using BFS
        #Prints out 1 and 0 whether a space is occupied or not
        #This is used to generate possible actions by checking if a box is within the range of the accesible area
        #Example Grid:
            00000000
            00111110
            00000010
            00000010
            00000000
        #In the grid above, the 1s represent the spaces the bot can move into and the 0 either represents a wall or a box
    """
    #Can potentially replace this with some row scan algo?
    """
        This sets the openArea to be every tile in gameBox that is not occupied by a Box or a Wall.
        Example:
        boxes | walls
        010     000     010
        010  |  101  =  111
        010     000     010

        (boxes|walls) ^ gameBox. The ^, or XOR operator, results in 1 if only 1 bit is 1, or 0 if both bits are 1 or 0.
        010     111     101
        111  ^  111  =  000
        010     111     101
        Since gameBox is all 1 bits, XOR-ing it with boxes|walls returns a bitmap where all of the unoccupied spaces are 1, or truthy.
    """
    openArea = (boxes | walls) ^ gameBox
    explored = 0

    q = deque()
    q.append(player)
    explored |= player
    
    while q:
        pos = q.popleft()
        """
            & gameBox ensures that moving the position a row up out of bounds results in 0. Might not matter if all maps have walls
            Example:
                    010
            010     000
            000  -> 000
            000     000

            010
            000     111     000
            000  &  111  =  000
            000     111     000
        """
        up = pos << gwidth
        down = pos >> gwidth
        """
            & (gameBox ^ rightColumn) ensures that if the left of the position wraps around to the right side, it results in 0 instead.
            Example:
            gameBox ^ rightColumn
            111     001     110
            111  ^  001  =  110
            111     001     110

            000     001     110     000
            100  -> 000  &  110  =  000
            000     000     110     000
            
            It also guards against a position in the top left wrapping around into an out of bounds row above.
            gameBox ^ leftColumn works similarly but on the other side.
        """
        left = pos << 1
        right = pos >> 1

        """
            This uses the bitwise AND operator to check if the target position, (up, down, left, right), are in the openArea (unblocked) and if they were already explored or not.
            If the target is in the open area, that bit will stay 1, and return a truthy value, else it will return falsy and does not enter the if block.
            Example:
            up      openArea
            010     111     010
            000  &  001  =  000
            000     000     000
            Since the bitmap is nonzero, it is read as a truthy value and succeeds the condition.
            Example 2:
            000     111     000
            010  &  001  =  000
            000     000     000
            Since the bitmap has a value of zero, it is read as a falsy value and fails the condition.

            Checking if it is not in explored works similarly, except we have a NOT conditional operator as we want it to not be in the explored area yet to add it to the frontier.
        """
        if up & openArea and not (up & explored):
            q.append(up)
            explored |= up
        if down & openArea and not (down & explored):
            q.append(down)
            explored |= down
        if left & openArea and not (left & explored):
            q.append(left)
            explored |= left
        if right & openArea and not (right & explored):
            q.append(right)
            explored |= right

    return explored

def getCorral(accessible, walls, boxes):
    #gets all positions that are not accessible, not a wall, and not a box
    corralCells = gameBox ^ accessible ^ walls ^ boxes
    separatedCells = getIndivBits(corralCells)

    corralRegion = []
    explored = 0

    cellQ = deque()
    corrals = []

    for cell in separatedCells:
        if cell & explored:
            continue
        area, boundary = 0, 0
        cellQ.append(cell)
        explored |= cell

        while cellQ:
            cell2 = cellQ.popleft()
            area |= cell2
            up = cell2 << gwidth
            down = cell2 >> gwidth
            left = cell2 << 1
            right = cell2 >> 1

            for n in (up, down, left, right):
                if n & boxes:
                    boundary |= n
                elif not n & explored and n & corralCells:
                    explored |= n
                    cellQ.append(n)
        corrals.append((area, boundary))

    return corrals

def isPI(area, boundary, accessible, blocked, deadCells, targets):
    if (boundary & targets) == boundary and not area & targets:
        return False

    separatedBoundary = getIndivBits(boundary)
    for box in separatedBoundary:
        for direction in Direction:
            shift = shifts[direction]
            boxLandingPos, playerSide = 0, 0
            if shift > 0:
                boxLandingPos = box << shift
                playerSide = box >> shift
            else:
                boxLandingPos = box >> -shift
                playerSide = box << -shift

            if boxLandingPos & area:
                if not boxLandingPos & deadCells and not playerSide & accessible:
                    return False

            else:
                if playerSide & accessible and not boxLandingPos & (blocked | deadCells):
                    return False

    return True

def getActions(walls, currentState, deadCells, targets):
    """
        This returns the possible actions based on the accessible area.
        It checks the coordinates of each box and checks if those coordinates are within the range of the accesible area.
        Using the example grid from getAccessibleArea:
            00000000
            00111110
            00200010
            00000010
            00000000
        For the sake of representation, 2 is the box which is at coordinates (2,2) (stored in currentState.boxes).
        It will first check the possible area(up, down, left, right) that the boxed can be moved into using blocked.
        If the area is not blocked, it will then use accesible area to check if that box can be moved from the opposite direction of the movement.
        Ex: The down coordinates of the box is free/not blocked. Since the accessible area has 1 on the up of the box, this means that pushing the box downwards is indeed a valid movement.
        This movement is then added to the actionSet which is all the possible actions from this current state.
    """
    actionSet = set()
    
    blocked = walls | currentState.boxes | deadCells
    accessible = currentState.playerAccess
    corrals = getCorral(accessible, walls, currentState.boxes)

    candidateBoxes = getIndivBits(currentState.boxes)
    boxes = currentState.boxes

    for area, boundary in corrals:
        if isPI(area, boundary, accessible, blocked, deadCells, targets):
            candidateBoxes = getIndivBits(boundary)
            break
    
    for box in candidateBoxes:
        up = box << gwidth
        down = box >> gwidth
        left = box << 1
        right = box >> 1 
        #The accesible coordinates is the position beside the box at the opposite direction of the push
        #Up push means check if accesible from the free position at down of the box

        #Up Push. box[0] + 1][box[1] is the coordinates of down. same with the other directions
        if down & accessible and not up & blocked:
            up_frozen = detectFrozenDeadlock(up, boxes ^ box ^ up, walls, deadCells, targets)
            if not up_frozen:
                actionSet.add((box,Direction.UP))
        #Down Push
        if up & accessible and not down & blocked:
            down_frozen = detectFrozenDeadlock(down, boxes ^ box ^ down, walls, deadCells, targets)
            if not down_frozen:
                actionSet.add((box,Direction.DOWN))
        #Left Push
        if right & accessible and not left & blocked:
            left_frozen = detectFrozenDeadlock(left, boxes ^ box ^ left, walls, deadCells, targets)
            if not left_frozen:
                actionSet.add((box,Direction.LEFT))
        #Right Push
        if left & accessible and not right & blocked:
            right_frozen = detectFrozenDeadlock(right, boxes ^ box ^ right, walls, deadCells, targets)
            if not right_frozen:
                actionSet.add((box,Direction.RIGHT))
    
    return actionSet

def detectSimpleDeadlock(walls, targets):
    """
        Algorithm used here is a reverse search wherein a box is placed in the targets and a "player" attempts to pull.
        If a player was able to pull, its a good square, if not then its a dead square.
        For pruning in getActions.
    """
    """
        This gets all the non-wall tiles.
        Example:
    """
    validFloorCells = walls ^ gameBox
    
    # All squares from which a box can potentially reach a target
    goodCell = targets
    q = deque(getIndivBits(targets))

    while q:
        box = q.popleft()
        """
            You can look up the explanation to this in getAccessible Area.
            direction (1) is boxPullPos
        """
        up = box << gwidth
        """
            These player{Direction} ones just repeat the shift one more time.
            playerDirection (2) is playerPullPos
        """
        playerUp = up << gwidth
        down = box >> gwidth
        playerDown = down >> gwidth
        left = box << 1
        playerLeft = left << 1
        right = box >> 1
        playerRight = right >> 1

        directions = [(up,playerUp),(down,playerDown),(left,playerLeft),(right,playerRight)]

        for direction in directions:
            """
                These check if the bit values post-shit land on valid floor cells. Also checks if it is already in goodCell
                Example:
                Original Box    LeftOne     LeftTwo     validCells
                000             000         000         001
                001             010         100         111
                000             000         000         000
                LeftOne & validCells
                000     001     000
                010  &  111  =  010  = Truthy
                000     000     000
                LeftTwo & validCells
                000     001     000
                100  &  111  =  100  = Truthy
                000     000     000
                DownOne & validCells
                000     001     000
                000  &  111  =  000  = Falsy
                001     000     000
            """
            if direction[0] & validFloorCells and direction[1] & validFloorCells and not direction[0] & goodCell:
                goodCell |= direction[0]
                q.append(direction[0])

    # Every non-wall tile not found by reverse search is a dead square.
    # Returns every dead square
    return goodCell^gameBox

def isFrozen(box, boxes, walls, deadCells, checking):
    checking |= box
    blocked = walls | checking

    """
        Don't use lookup table for shifts if you need them all, just hardcode it.
    """
    up = box << gwidth
    down = box >> gwidth
    left = box << 1
    right = box >> 1

    horizontalBlock = ((left | right) & blocked
                        or (left & deadCells and right & deadCells)
                        or (left & boxes and isFrozen(left,boxes,walls,deadCells,checking))
                        or (right & boxes and isFrozen(right,boxes,walls,deadCells,checking))
                    )
    verticalBlock = ((up | down) & blocked
                        or (up & deadCells and down & deadCells)
                        or (up & boxes and isFrozen(up,boxes,walls,deadCells,checking))
                        or (down & boxes and isFrozen(down,boxes,walls,deadCells,checking))
                    )
    return horizontalBlock and verticalBlock

def detectFrozenDeadlock(movedBox, boxes, walls, deadCells, targets):
    toCheck = [movedBox]

    for dir in Direction:
        shift = shifts[dir]
        neighbor = movedBox << shift if shift > 0 else movedBox >> -shift
        if neighbor & boxes:
            toCheck.append(neighbor)

    for box in toCheck:
        checking = 0
        if not box & targets and isFrozen(box,boxes,walls,deadCells,checking):
            return True
    return False

def createState(walls, exploring, action):
    """
        Creates a new state given the current state and the given action.
    """
    boxes = exploring.boxes
    targetBox = action[0]
    direction = action[1]

    #Flips the bit of the targetBox, turning it off.
    boxes ^= targetBox
    #Flips the bit of the new box position, turning it on.
    #Alternatively, we could feed this the new box position instead of the direction later, but that might make other things confusing down the line.
    match (direction):
        case Direction.UP:
            boxes |= targetBox << gwidth
        case Direction.DOWN:
            boxes |= targetBox >> gwidth
        case Direction.LEFT:
            boxes |= targetBox << 1
        case Direction.RIGHT:
            boxes |= targetBox >> 1

    #Player should be standing in the opposite direction of where they pushed the box, so we can call the search here
    #Actually, the player could also be standing where they just pushed the box from, simpler to just call the search there actually.
    player = targetBox

    playerAccess = getAccessibleArea(walls, boxes, player)   #Flood fill algorithm, could find a faster one

    return State(boxes,playerAccess)

def findPath(start, goal, walls, boxes):
    """
        This finds the path from player start position to goal position using BFS (path for EACH box).
        for context: the goal position is the position beside the box opposite of the direction of the push.
    """
    if start == goal:
        return ""

    blocked = walls | boxes

    # dict to store prev position as (x,y) in this case, I just called it start; and direction as char, which is "None" at the start
    #Bitmap: bitmap to store the values of the prev positions
    cameFromMap = start

    #Added this type hint because vscode is complaining. ': dict[int, tuple[int, str] | None]'
    cameFrom: dict[int, tuple[int, str] | None] = {start: None}

    q = deque()
    q.append(start)
    
    # while loop to explore the grid until we reach the goal (BFS)
    while q:
        currPos = q.popleft()

        for direction in Direction:
            # calculates the new position based on the current position and the direction of movement
            shift = shifts[direction]
            newPos = currPos << shift if shift > 0 else currPos >> -shift

            if newPos & blocked or newPos & cameFromMap:
                continue

            # sets the previous position and direction for the new position in the cameFrom dictionary
            # this kind of simulates the way we solve Frontier and Explored in class
            # ex. cameFrom[(x,y)] = ((prevX, prevY), direction) to show where (x,y) came from and what direction we took to get there
            # take note that direction is parsed into its corresponding character here, as seen in the LETTERS dictionary above
            cameFromMap |= newPos
            cameFrom[newPos] = (currPos, LETTERS[direction])

            # once we reach the goal, reconstruct path
            if newPos == goal:
                return reconstructPath(cameFrom, start, goal)

            # if goal is not reached, continue exploring
            else:
                q.append(newPos)

    return ""

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

def boxPushesToMoves(pushSeq, player, boxes, walls):
    """
        This function takes the push sequence (basically, the single final push to get the box to the target) 
        from A* and converts it into a string of moves for the player to execute
        It does this by finding running findPath (which finds the path from player's current position to position beside the box opposite the direction of the push) 

        The result of this function is what is returned to the main.py file and printed out / used as the final solution
    """
    moves = ""

    currentBoxes = boxes
    
    for push in pushSeq:
        boxGoal, direction = push
        # Sets coords of player to position beside the box opposite of target. UP/DOWN, and LEFT/RIGHT are switched here as we are getting the opposite direction.
        playerReadyPos = 0
        match (direction):
            case Direction.DOWN:
                playerReadyPos = boxGoal << gwidth
            case Direction.UP:
                playerReadyPos = boxGoal >> gwidth
            case Direction.RIGHT:
                playerReadyPos = boxGoal << 1
            case Direction.LEFT:
                playerReadyPos = boxGoal >> 1

        moves += findPath(player, playerReadyPos, walls, currentBoxes)
        # adds extra letter to string for the actual push to target
        moves += LETTERS[direction]
        # player assumes old pos of box after push
        player = boxGoal
        currentBoxes ^= boxGoal
        # box is now in the new position
        match (direction):
            case Direction.UP:
                currentBoxes |= boxGoal << gwidth
            case Direction.DOWN:
                currentBoxes |= boxGoal >> gwidth
            case Direction.LEFT:
                currentBoxes |= boxGoal << 1
            case Direction.RIGHT:
                currentBoxes |= boxGoal >> 1

    return moves



#For testing
def printGrid(grid):
    for x in range(len(grid)):
        for y in range(len(grid[x])):
            print(grid[x][y], end="")
        print()

def printBitMap(bitmap, display='X'):
    n = gwidth * gheight
    for r in range(gheight):
        print("".join(
            display if (bitmap >> (n - 1 - (r * gwidth + c))) & 1 else "."
            for c in range(gwidth)
        ))
    print()

def printBitMap2(bitmap, display = 'X'):
    for r in range(gheight):
        print("".join(display if (bitmap >> (r * gwidth + c)) & 1 else "." for c in range(gwidth)))
    print()

