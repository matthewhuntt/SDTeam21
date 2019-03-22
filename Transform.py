
import csv
import re
import datetime
import pandas as pd
from openpyxl import load_workbook

def setupDataReader(filename):
    with open(filename, "r") as f:
        reader = csv.reader(f)
        rows = []
        for row in reader:
            rows.append(row)
    echelon_dict = {}
    echelon_dict_reverse = {}
    event_room_list = []
    item_list = []
    requirement_dict = {}
    for row in rows:
        if row[1] not in echelon_dict.values():
            echelon_dict[len(echelon_dict) + 1] = row[1]
            echelon_dict_reverse[row[1]] = len(echelon_dict_reverse) + 1
        if (row[4], echelon_dict_reverse[row[1]]) not in requirement_dict:
            requirement_dict[(row[4], echelon_dict_reverse[row[1]])] = []
        if row[4] not in event_room_list:
            event_room_list.append(row[4])
        if row[5] not in item_list:
            item_list.append(row[5])
        requirement_dict[(row[4], echelon_dict_reverse[row[1]])].append((row[5], row[6]))
    for echelon in echelon_dict:
        echelon_dict[echelon] = datetimeReader(echelon_dict[echelon])
    return (echelon_dict, event_room_list, item_list, requirement_dict)

def currentStateReader(filename):

    #Read in current inventory levels for storage

    xl = pd.ExcelFile(filename)
    inventory_df = xl.parse("Inventory by Room")
    inventory_rows = inventory_df.values.tolist()

    inventory_dict = {}
    for row in inventory_rows:
        inventory_dict[(row[0], row[1])] = row[2]

    #Read in active room requirements
    #Notes:
    #   Echelons are based on set up start times

    xl = pd.ExcelFile(filename)
    requirement_df = xl.parse("Event Requirements")
    requirement_rows = requirement_df.values.tolist()

    echelon_dict = {}
    echelon_dict_reverse = {}
    event_room_list = []
    item_list = []
    requirement_dict = {}
    for row in requirement_rows:
        if row[2] not in echelon_dict.values():
            echelon_dict[len(echelon_dict) + 1] = row[2]
            echelon_dict_reverse[row[2]] = len(echelon_dict_reverse) + 1
        if (row[1], echelon_dict_reverse[row[2]]) not in requirement_dict:
            requirement_dict[(row[1], echelon_dict_reverse[row[2]])] = []
        if row[1] not in event_room_list:
            event_room_list.append(row[1])
        if row[6] not in item_list:
            item_list.append(row[6])
        requirement_dict[(row[1], echelon_dict_reverse[row[2]])].append((row[6], row[7]))
    #for echelon in echelon_dict:
    #    echelon_dict[echelon] = datetimeReader(echelon_dict[echelon])

    return(inventory_dict, echelon_dict, event_room_list, item_list, requirement_dict)

def costDataReader(filename):
    with open(filename, "r") as f:
        reader = csv.reader(f)
        rows = []
        for row in reader:
            rows.append(row)
    cost_dict = {}
    for rowIndex in range (1, len(rows)):
        for columnIndex in range (1, len(rows)):
            cost_dict[(rows[rowIndex][0], rows[0][columnIndex])] = rows[rowIndex][columnIndex]
    return cost_dict

def datetimeReader(date):
    searchObject = re.search("(\d{1,2})\/(\d{1,2})\/(\d{1,2}) (\d{1,2}):(\d{2})", date)
    (month, day, year, hour, minute) = searchObject.groups()
    date = datetime.datetime(int(year), int(month), int(day), int(hour), int(minute))
    return date

def constructor(echelon_dict, eventRoomList, itemList, costDict, requirementDict, inventory_dict):

    #Creates 4 sets of arcs:
    #   movement_arc_dict       All b to a, room to room movement arcs (decisions)
    #   storage_cap_arc_dict    All a to b storage arcs (decisions)
    #   event_req_arc_dict      All a to b event requirement arcs (givens)
    #   utility_arc_dict        All arcs originating at the s node or between t nodes (givens)

    storageRoomList = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10"]
    allRoomList = eventRoomList + storageRoomList
    roomDict = {}
    for i in range (len(allRoomList)):
        roomDict[i + 1] = allRoomList[i]
    movement_arc_dict = {}
    storage_cap_arc_dict = {}
    event_req_arc_dict = {}
    utility_arc_dict = {}

    #Create general set of arcs for all time echelons other than the first and
    #last

    for echelon in echelon_dict:
        for roomI in roomDict:
            for roomJ in roomDict:
                for ab in ["a", "b"]:
                    if ab == "a":
                        if roomI == roomJ:
                            if (roomDict[roomI], echelon) in requirementDict:
                                for requirement in requirementDict[(roomDict[roomI], echelon)]:
                                    item, qty = requirement[0], requirement[1]
                                    event_req_arc_dict[((roomI, echelon, "a"),(roomJ, echelon, "b"), item)] = (qty, qty, 0)
                            if roomDict[roomI] in storageRoomList:
                                for item in itemList:
                                    storage_cap_arc_dict[((roomI, echelon, "a"),(roomJ, echelon, "b"), item)] = (0, 100000000, 0)
                    if ab == "b":
                        if echelon != len(echelon_dict.keys()):
                            for item in itemList:
                                movement_arc_dict[((roomI, echelon, "b"), (roomJ, echelon + 1, "a"), item)] = (0, 100000000, costDict[(roomDict[roomI], roomDict[roomJ])])

    #Create set of arcs for inital starting conditions from s node to each room

    for room in roomDict:
        for item in itemList:
            utility_arc_dict[(("s", 0, "a"), (room, 0, "b"), item)] = (100000, 100000, 0)
            movement_arc_dict[((room, (len(echelon_dict.keys())), "b"), ("t", (len(echelon_dict.keys()) + 1), "a"), item)] = (0, 1000000000, 0)

    #Create set of movement arcs for the first movement period

    for roomI in roomDict:
        for roomJ in roomDict:
            for item in itemList:
                movement_arc_dict[((roomI, 0, "b"), (roomJ, 1, "a"), item)] = (0, 100000000, costDict[(roomDict[roomI], roomDict[roomJ])])

    rooms = len(roomDict.keys())
    for item in itemList:
        utility_arc_dict[(("t", (len(echelon_dict.keys()) + 1), "a"), ("t", (len(echelon_dict.keys()) + 1), "b"), item)] = (100000 * rooms, 100000 * rooms, 0)

    return movement_arc_dict, storage_cap_arc_dict, event_req_arc_dict, utility_arc_dict, roomDict

def arcDictWriter(arcDict, filename):
    #Writes to csv file
    arcList = []
    for arc in arcDict.keys():
        arcList.append([arc[0][0], arc[0][1], arc[0][2], arc[1][0], arc[1][1],
            arc[1][2], arc[2], arcDict[arc][0], arcDict[arc][1], arcDict[arc][2]])
    with open(filename, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["Xi", "Yi", "Zi", "Xj", "Yj", "Zj", "Item", "Lij", "Uij", "Cij"])
        writer.writerows(arcList)

def excelWriter(arcDict, filename, sheet_name):
    arcList = []
    for arc in arcDict.keys():
        arcList.append([arc[0][0], arc[0][1], arc[0][2], arc[1][0], arc[1][1],
            arc[1][2], arc[2], arcDict[arc][0], arcDict[arc][1], arcDict[arc][2]])

    #Writes to master excel sheet
    book = load_workbook("EquipmentInventory.xlsx")
    df = pd.DataFrame(arcList)
    writer = pd.ExcelWriter("EquipmentInventory.xlsx", engine='openpyxl')
    writer.book = book
    writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
    df.to_excel(writer, sheet_name=sheet_name, index=False, index_label=False)
    writer.save()
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
    #(echelon_dict, eventRoomList, itemList, requirementDict) = setupDataReader("SetupData.csv")
    cost_dict = costDataReader("CostData.csv")
    (inventory_dict, echelon_dict, event_room_list, item_list, requirement_dict) = currentStateReader("EquipmentInventory.xlsx")
    print(inventory_dict)
    print("\n\n")
    print(requirement_dict)
    print("\n\n")
    print(echelon_dict)
    print("\n\n")
    print(event_room_list)
    print("\n\n")
    print(item_list)

    movement_arc_dict, storage_cap_arc_dict, event_req_arc_dict, utility_arc_dict, room_dict = constructor(echelon_dict, event_room_list, item_list, cost_dict, requirement_dict, inventory_dict)
    arcDictWriter(movement_arc_dict, "MovementArcs.csv")
    arcDictWriter(storage_cap_arc_dict, "StorageCapacityArcs.csv")
    arcDictWriter(event_req_arc_dict, "EventRequirementArcs.csv")
    arcDictWriter(utility_arc_dict, "UtilityArcs.csv")
    excelWriter(movement_arc_dict, "EquipmentInventory.xlsx", "Movement Arcs")
    excelWriter(storage_cap_arc_dict, "EquipmentInventory.xlsx", "Storage Room Arcs")
    excelWriter(event_req_arc_dict, "EquipmentInventory.xlsx", "Event Room Arcs")
    excelWriter(utility_arc_dict, "EquipmentInventory.xlsx", "Utility Arcs")
    auxiliaryWriter(room_dict, "RoomDictionary.csv")
    #print(eventRoomList)
    #print(itemList)
    print((len(movement_arc_dict) + len(storage_cap_arc_dict) + len(event_req_arc_dict)))
    print(len(room_dict.keys()))
    print(room_dict)
    print(len(event_room_list))
    print(len(echelon_dict.keys()))

if __name__ == '__main__':
    import sys
    main(sys.argv)

