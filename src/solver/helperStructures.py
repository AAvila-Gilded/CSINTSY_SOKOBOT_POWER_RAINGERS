from enum import Enum

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

    #Temp function to check how many boxes are aligned
    def checkProgress(self, other):
        progress = 0
        for x in self.boxes:
            if x in other.boxes:
                progress += 1
        return progress

    #Hash Override, sets the hash to use the tuple of box coordinates and player access.
    def __hash__(self):
        return hash((self.boxes,self.playerAccess))


class Direction(Enum):
    UP = (-1, 0)
    DOWN = (+1, 0)
    LEFT = (0, -1)
    RIGHT = (0, +1)

    #Enum library gets each element assigned to the enum key as a separate argument
    #so element 1 is passed as row, element 2 is passed as column
    def __init__(self, row, column):
        self.row = row
        self.column = column