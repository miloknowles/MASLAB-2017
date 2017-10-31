import math
import numpy as np, vectors2d as vec
import time
import cv2

class Node(object):
    def __init__(self, x, y, f = 0, g = 0, h = 0):
        self.x = x
        self.y = y
        self.f = f
        self.g = g
        self.h = h
        self.parent = None

    def set_parent(self, parent):
        self.parent = parent    

    def __str__(self):
        return "(" + str(self.x) + ", " + str(self.y) + ")"
    def compare(self, other):
        """
        returns True if other has the same coordinates but lower f
        """
        return (self.x == other.x and self.y == other.y and self.f >= other.f)
    def get_coord(self):
        return (self.x, self.y)
    def get_dist(self, other):
        return math.sqrt((self.x - other.x)**2 + (self.y -  other.y)**2)

    def is_obstacle(self, grid, maxY):
        #return if the node is on an obstacle -- if grid[yMax - 1 - self.y][self.x] == 1
        return grid[maxY -1 - self.y][self.x] == 1


def generate_successors(parent_node):
    node = parent_node.get_coord()
    successors = [] # a list of successor coordinates
    successors.append((node[0],node[1] + 1))
    successors.append((node[0] + 1,node[1]))
    successors.append((node[0],node[1] - 1))
    successors.append((node[0] - 1,node[1]))
    successors.append((node[0] + 1,node[1] + 1))
    successors.append((node[0] + 1,node[1] - 1))
    successors.append((node[0] - 1,node[1] + 1))
    successors.append((node[0] - 1,node[1] - 1))

    succ_nodes = []
   # print successors
    for succ in successors:
        succ_node = Node(*succ) #make the nodes
        succ_node.set_parent(parent_node) # set the parent node to the parent node
        succ_nodes.append(succ_node) # add to the list of successors
    return succ_nodes


def find_path(start, goal, grid, maxY):
    """
    start, and goal are tuples (x, y)
    grid is a grid with obstacles
    return a list of coordinates and a list of nodes
    """
    stopSearch = False
    begin = time.time()
    startNode = Node(*start)
    goalNode = Node(*goal)
    openNodes = [startNode] # f value and node
    closedNodes = []
    path = []
    while len(openNodes) > 0 and not stopSearch:
        #find the node with the least f on the open list call it q
        if time.time() - begin >= 20:
            stopSearch = True
        ind = 0
        min_f = openNodes[0].f
        for i in range(len(openNodes)):
            if min_f >= openNodes[i].f:
                min_f = openNodes[i].f
                ind = i
        q = openNodes.pop(ind)
        
        """
        generate q's 8 successors and set their parents to q
        for each successor
            if successor is the goal, stop the search
            successor.g = q.g + distance between successor and q
            successor.h = distance from goal to successor
            successor.f = successor.g + successor.h
        """
        successors = generate_successors(q)
        for successor in successors:
            if successor.x == goalNode.x and successor.y == goalNode.y:
                stopSearch = True
                goalNode.parent =  q
                break
            successor.g = q.g + successor.get_dist(q)
            successor.h = successor.get_dist(goalNode)
            successor.f = successor.g + successor.h

            """
                if a node with the same position as successor is in the OPEN list \
                    which has a lower f than successor, skip this successor
                if a node with the same position as successor is in the CLOSED list \ 
                    which has a lower f than successor, skip this successor
                otherwise, add the node to the open list
            end
            push q on the closed list
            """
            skip = False
            for node in openNodes:
                if successor.compare(node):
                    skip = True
            for node in closedNodes:
                if successor.compare(node):
                    skip = True
            if not skip and not successor.is_obstacle(grid, maxY):
                openNodes.append(successor)

        closedNodes.append(q)
        path.append(q.get_coord())

    closedNodes.append(goalNode)
    path.append(goalNode.get_coord())
    
    return path, closedNodes
  

def draw_path(path, maxX, maxY, clearance = 1.0):
    pathGrid = np.zeros([maxY,maxX])
#    for x in range(maxX):
#        for y in range(maxY):
#            for p in range(len(path)):
#                try:
#                    isClear = (vec.pnt2line([x,y], path[p], path[p+1])[0]<=clearance)
#                except IndexError:
#                    isClear = (vec.pnt2line([x,y], path[p], path[0])[0]<=clearance)
#                if isClear:
#                    pathGrid[maxY-1-y][x] = 1
#                    break
    for step in path:
        x =maxY- step[1] -1
        y = step[0]
        pathGrid[x][y] = 1.0
    return pathGrid


def find_path_1(closedNodes):
    """
    find the actual path from exlored nodes
    """
    #end_p0 = closedNodes[len(closedNodes) -1]
    #end_coord0 = end_p0.get_coord()
    end_point =  closedNodes[len(closedNodes) - 1]
    start_point = closedNodes[0]
    end_coord = end_point.get_coord()
    start_coord = start_point.get_coord()
    #path = [end_coord0, end_coord]
    path = [end_coord]
    while end_point.parent != None and (end_coord[0] != start_coord[0] or end_coord[1] != start_coord[1]):
        path.append(end_point.parent.get_coord())
        end_point =  end_point.parent
    return path

def draw_path_1(path, maxX, maxY, clearance = 1.0):
    """
    draw the actual path
    """
    pathGrid = np.zeros([maxY,maxX])
    for x in range(maxX):
        for y in range(maxY):
            for p in range(len(path) - 1):
                try:
                    isClear = (vec.pnt2line([x,y], path[p], path[p+1])[0]<=clearance)
                except IndexError:
                    isClear = (vec.pnt2line([x,y], path[p], path[0])[0]<=clearance)
                if isClear:
                    pathGrid[maxY-1-y][x] = 1
                    break
    return pathGrid
    
def makeMap(mapFileName,factor=1.0,clearance = 1.0):
    """
    returns a map enlarged by factor (should be 24)
    """    
    
    walls,greenDispensors,redDispensor,homeBase,stacks,startingPosition, maxX, maxY = parseFile(mapFileName,factor)
    
    #Calculate max x and y from walls and dispensors
#    maxX = 9 * factor
#    maxY = 10 * factor
#    def transform(x):
#        
#        return x * factor
#    
    #use walls and dispensors (and blocks maybe) to input obstacles in list of lines
    boundaries = walls + [greenDispensors] + [redDispensor]
    dispensors = [greenDispensors] + [redDispensor]
#    print boundaries

        
    print "grid size:", maxX, maxY
    
    boundaryGrid = np.zeros([maxY,maxX])
    dispensorGrid = np.zeros([maxY,maxX])
    baseGrid = np.zeros([maxY,maxX])
    stackGrid = np.zeros([maxY,maxX])
    
#   fill in grids
    for x in range(maxX):
        for y in range(maxY):
            for line in boundaries:
                if vec.pnt2line([x,y], line[0], line[1])[0]<=clearance:
                    boundaryGrid[maxY-1-y][x] = 1
                    break
                
    for x in range(maxX):
        for y in range(maxY):
            for line in dispensors:
                if vec.pnt2line([x,y], line[0], line[1])[0]<=clearance:
                    dispensorGrid[maxY-1-y][x] = 1
                    break
    
    for x in range(maxX):
        for y in range(maxY):
            for hb in range(len(homeBase)):
                try:
                    isClear = (vec.pnt2line([x,y], homeBase[hb], homeBase[hb+1])[0]<=clearance)
                except IndexError:
                    isClear = (vec.pnt2line([x,y], homeBase[hb], homeBase[0])[0]<=clearance)
                if isClear:
                    baseGrid[maxY-1-y][x] = 1
                    break
                
    for x in range(maxX):
        for y in range(maxY):
            for sk in range(len(stacks)):
                if vec.pnt2line([x,y], stacks[sk], stacks[sk])[0]<=clearance:
                    stackGrid[maxY-1-y][x] = 1
                    break
    
                
#    print boundaryGrid
#    print "---------------------"
#    print dispensorGrid
#    print "---------------------"
#    print baseGrid
#    print "---------------------"
#    print stackGrid
#    print "---------------------"
    return boundaryGrid,dispensorGrid,baseGrid,stackGrid,walls,greenDispensors,redDispensor,homeBase,stacks,startingPosition, maxX, maxY

def parseFile(mapFileName,scale=1):
    """
    parses a mapfile, type(mapFileName) == str
    for walls and home base, return a list of line segments, which are lists of two coordinates, [x,y]
    for stacks,return a list of coordinates, [x, y]
    for startPos, return [x, y, heading], heading is a string 'N', 'E', 'S', 'W'
    for dispensers, return two coordinates[x, y]
    
    """
    f = open(mapFileName, 'r') 

    allXValues = []
    allYValues = []
    
    walls = []
    dispenser_g = []
    dispenser_r = []
    homeBase = []
    stacks = []
    startPos = []
    
    for line in f:
    
        item = line.split(',')
    #    print line
        
        if item[0] == 'W':
            coordinate = []
            x1, y1 = scale*int(item[1]), scale*int(item[2])
            x2, y2 = scale*int(item[3]), scale*int(item[4][0])
            coordinate.append((x1, y1))
            coordinate.append((x2, y2))
            allXValues.append(x1)
            allXValues.append(x2)
            allYValues.append(y1)
            allYValues.append(y2)
    
            walls.append(coordinate)
        elif item[0] == 'D':
            x1, y1 = scale*int(item[1]), scale*int(item[2])
            x2, y2 = scale*int(item[3]), scale*int(item[4])

            allXValues.append(x1)
            allXValues.append(x2)
            allYValues.append(y1)
            allYValues.append(y2)
#            coordinate.append([x1, y1])
#            coordinate.append([x2, y2])
            if item[len(item) -1][0] == 'R':
                dispenser_r.append((x1, y1))
                dispenser_r.append((x2, y2))
            else:
                dispenser_g.append((x1, y1))
                dispenser_g.append((x2, y2))
        elif item[0] == 'H':
            for i in range(2, len(item),2):
                x1, y1 = scale*int(item[i]), scale*int(item[i +1])
                allXValues.append(x1)
                allYValues.append(y1)
                homeBase.append((x1, y1))
        elif item[0] == 'S':
            x1, y1 = scale*int(item[1]), scale*int(item[2])
            allXValues.append(x1)
            allYValues.append(y1)
            stacks.append((x1, y1))
    
        elif item[0] == 'L':
            x1,y1 = scale*int(item[1]),scale*int(item[2])
            startPos.append((x1,y1))
            startPos.append(item[3][0])        

            allXValues.append(x1)
            allYValues.append(y1)
            
    minX = int(min(allXValues)*0.9)
    minY = int(min(allYValues)*0.9)
    maxX = int(max(allXValues) * 1.1)
    maxY = int(max(allYValues) * 1.1)
    maxX = maxX-minX
    maxY = maxY-minY

    f.close()
    
#    print "walls:", walls
#    print "dispensor_green:", dispenser_g
#    print "dispensor_red:", dispenser_r
#    print "home base:", homeBase
#    print "stacks:" , stacks
#    print "starting position:", startPos

    walls, dispenser_g, dispenser_r, homeBase, stacks, startPos = shiftPoints(walls, dispenser_g, dispenser_r, homeBase, stacks, startPos,minX,minY)

#    print "walls:", walls
#    print "dispensor_green:", dispenser_g
#    print "dispensor_red:", dispenser_r
#    print "home base:", homeBase
#    print "stacks:" , stacks
#    print "starting position:", startPos    
    
    return walls, dispenser_g, dispenser_r, homeBase, stacks, startPos, maxX, maxY
    
   
def shiftPoints(walls, dispenser_g, dispenser_r, homeBase, stacks, startPos,minX,minY):
    
    walls2 = []
    for w in walls:
        p1 = (w[0][0]-minX,w[0][1]-minY)
        p2 = (w[1][0]-minX,w[1][1]-minY)
        walls2.append([p1,p2])
    
    dispenser_g2 = []
    dispenser_r2 = []
    
    for p in dispenser_g:
        dispenser_g2.append((p[0]-minX,p[1]-minY))
    for p in dispenser_r:
        dispenser_r2.append((p[0]-minX,p[1]-minY))

    homeBase2 = []
    for p in homeBase:
        homeBase2.append((p[0]-minX,p[1]-minY))
        
    stacks2 = []
    for p in stacks:
        stacks2.append((p[0]-minX,p[1]-minY))
        
    startPos2 = [(startPos[0][0]-minX,startPos[0][1]-minY),startPos[1]]
    
    return  walls2, dispenser_g2, dispenser_r2, homeBase2, stacks2, startPos2



def displayMap(boundaryGrid,dispensorGrid,baseGrid,stackGrid,pathGrid, walls,greenDispensors,redDispensor,homeBase,stacks,startingPosition, maxX, maxY):
    
    mapImage = 255*np.ones([maxY,maxX,3])
    mapImage[boundaryGrid==1] = [255,0,0]
    mapImage[dispensorGrid==1] = [0,255,255]
    mapImage[baseGrid==1] = [255,0,255]
    mapImage[stackGrid==1] = [0,0,255]
    mapImage[pathGrid==1] = [0,0,0]
    
    cv2.imshow("map",mapImage)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def displayPath(pathGrid, maxX, maxY):
    
    mapImage = 255*np.ones([maxY,maxX,3])
    mapImage[pathGrid==1] = [0,0,0]
    cv2.imshow("map",mapImage)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    mapFileName = "PracticeMap.txt"
    factor = 24
    clearance = 2
    
    boundaryGrid,dispensorGrid,baseGrid,stackGrid,walls,greenDispensors,redDispensor,homeBase,stacks,startingPosition, maxX, maxY = makeMap(mapFileName, factor, clearance)
    start = startingPosition[0]#(2, 9)
    goal = stacks[4] #bug at stack[3], stack[4]

    path, cNodes = find_path(start, goal, boundaryGrid, maxY)
    path1 = find_path_1(cNodes)
    pathGrid1 = draw_path_1(path1, maxX, maxY)
    #pathGrid = draw_path(path, maxX, maxY)
    displayMap(boundaryGrid,dispensorGrid,baseGrid,stackGrid,pathGrid1, walls,greenDispensors,redDispensor,homeBase,stacks,startingPosition, maxX, maxY)
    
    #displayPath(pathGrid, maxX, maxY)
