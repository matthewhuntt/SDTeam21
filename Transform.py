
import csv
import re
import datetime

def setupDataReader(filename):
    with open(filename, "r") as f:
        reader = csv.reader(f)
        rows = []
        for row in reader:
            rows.append(row)
    echelonDict = {}
    echelonDictReverse = {}
    eventRoomList = []
    itemList = []
    requirementDict = {}
    for row in rows:
        if row[1] not in echelonDict.values():
            echelonDict[len(echelonDict) + 1] = row[1]
            echelonDictReverse[row[1]] = len(echelonDictReverse) + 1
        if (row[4], echelonDictReverse[row[1]]) not in requirementDict:
            requirementDict[(row[4], echelonDictReverse[row[1]])] = []
        if row[4] not in eventRoomList:
            eventRoomList.append(row[4])
        if row[5] not in itemList:
            itemList.append(row[5])
        requirementDict[(row[4], echelonDictReverse[row[1]])].append((row[5], row[6]))
    for echelon in echelonDict:
        echelonDict[echelon] = datetimeReader(echelonDict[echelon])
    return (echelonDict, eventRoomList, itemList, requirementDict)

def costDataReader(filename):
    with open(filename, "r") as f:
        reader = csv.reader(f)
        rows = []
        for row in reader:
            rows.append(row)
    costDict = {}
    for rowIndex in range (1, len(rows)):
        for columnIndex in range (1, len(rows)):
            costDict[(rows[rowIndex][0], rows[0][columnIndex])] = rows[rowIndex][columnIndex]
    return costDict


def datetimeReader(date):
    searchObject = re.search("(\d{1,2})\/(\d{1,2})\/(\d{1,2}) (\d{1,2}):(\d{2})", date)
    (month, day, year, hour, minute) = searchObject.groups()
    date = datetime.datetime(int(year), int(month), int(day), int(hour), int(minute))
    return date

def constructor(echelonDict, eventRoomList, itemList, costDict, requirementDict):
    storageRoomList = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10"]
    allRoomList = eventRoomList + storageRoomList
    roomDict = {}
    for i in range (len(allRoomList)):
        roomDict[i + 1] = allRoomList[i]
    arcDict = {}
    for echelon in echelonDict:
        for roomI in roomDict:
            for roomJ in roomDict:
                for ab in ["a", "b"]:
                    if ab == "a":
                        if roomI == roomJ:
                            if (roomDict[roomI], echelon) in requirementDict:
                                for requirement in requirementDict[(roomDict[roomI], echelon)]:
                                    item, qty = requirement[0], requirement[1]
                                    arcDict[((roomI, echelon, "a"),(roomJ, echelon, "b"), item)] = (qty, qty, 0)
                    if ab == "b":
                        for item in itemList:
                            arcDict[((roomI, echelon, "b"),(roomJ, echelon + 1, "a"), item)] = (0, 0, costDict[(roomDict[roomI], roomDict[roomJ])])
    for room in roomDict:
        for item in itemList:
            arcDict[(("s", 0, "b"), (room, 1, "a"), item)] = (10000000, 10000000, 0)
            arcDict[((room, (len(echelonDict.keys()) + 1), "b"), ("t", (len(echelonDict.keys()) + 2), "a"), item)] = (10000000, 10000000, 0)
    return arcDict, roomDict

def arcDictWriter(arcDict, filename):
    arcList = []
    for arc in arcDict.keys():
        arcList.append([arc[0][0], arc[0][1], arc[0][2], arc[1][0], arc[1][1],
            arc[1][2], arc[2], arcDict[arc][0], arcDict[arc][1], arcDict[arc][2]])
    with open(filename, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["Xi", "Yi", "Zi", "Xj", "Yj", "Zj", "Item", "Lij", "Uij", "Cij"])
        writer.writerows(arcList)
    return None

def auxiliaryWriter(roomDict, filename):
    roomList = []
    for room in roomDict.keys():
        roomList.append([room, roomDict[room]])
    with open(filename, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["Room ID", "Room Name"])
        writer.writerows(roomList)

def main(args):
    (echelonDict, eventRoomList, itemList, requirementDict) = setupDataReader("SetupData.csv")
    costDict = costDataReader("CostData.csv")
    #print(requirementDict)
    #print("\n\n")

    #for room in eventRoomList:
    #    print(room)
    #print(echelonDict)
    arcDict, roomDict = constructor(echelonDict, eventRoomList, itemList, costDict, requirementDict)
    arcDictWriter(arcDict, "MCNFDataTest.csv")
    auxiliaryWriter(roomDict, "RoomDictionary.csv")
    #print(eventRoomList)
    #print(itemList)
    print(len(arcDict))

if __name__ == '__main__':
    import sys
    main(sys.argv)

