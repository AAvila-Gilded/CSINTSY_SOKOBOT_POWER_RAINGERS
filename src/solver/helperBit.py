from enum import Enum

class State:
    #Constructor Method, boxes contain the bitmap of the boxes and playerAccess contains the bitmap of the area the player can access without any pushes
    def __init__(self, boxes, playerAccess):
        self.boxes = boxes
        self.playerAccess = playerAccess

    #Equality Override, States are equal if they have the same set of Boxes and PlayerAccess
    def __eq__(self, other):
        return self.boxes == other.boxes and self.playerAccess == other.playerAccess

    #A function to check if the current state has the same box positions as another state. For testing if its equal to the goal state as the current player position is unimportant here
    def areBoxesEqual(self, other):
        return self.boxes == other.boxes

    #Temp function to check how many boxes are aligned
    def checkProgress(self, other):
        """
            This applies the AND bitwise operator on the boxes bitmap and target bitmap.
            This means only the bits that have both a box and a target remain as 1.
            Afterwards, we run the .bit_count() method to check how many 1s there are.
            This is how many boxes are on the target position.
            Example:
            boxes
            0100    1000    0000
            1000    0100    0000
            0010  & 0010  = 0010
            1000    0001    0000

            0000 0000 0010 0000 .bit_count() = 1
            There is only 1 box on the target position, so it returns a count of 1.
        """
        return (self.boxes & other.boxes).bit_count()

    #Hash Override, sets the hash to use the tuple of box coordinates and player access.
    def __hash__(self):
        return hash((self.boxes,self.playerAccess))


class Direction(Enum):
    """
        The delta shortcuts are no longer used in bitmap version.
        These are used instead.
        up = pos << width & gameBox.
        down = pos >> width & gameBox.
        left = pos << 1 & (gameBox ^ rightColumn).
        right = pos >> 1 & (gameBox ^ leftColumn).
    """
    UP = (-1, 0)
    DOWN = (+1, 0)
    LEFT = (0, -1)
    RIGHT = (0, +1)

    #Enum library gets each element assigned to the enum key as a separate argument.
    #so element 1 is passed as row, element 2 is passed as column.
    def __init__(self, row, column):
        self.row = row
        self.column = column