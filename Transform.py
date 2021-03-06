
import csv
import re
import datetime
import pandas as pd
from openpyxl import load_workbook

excel_filename = "EquipmentInventoryTest2.xlsx"

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
        inventory_dict[(row[0], row[1])] = float(row[2])

    total_inventory_dict = {}
    for (room, commodity) in inventory_dict.keys():
        if commodity in total_inventory_dict:
            total_inventory_dict[commodity] += inventory_dict[(room, commodity)]
        else:
            total_inventory_dict[commodity] = inventory_dict[(room, commodity)]

    xl = pd.ExcelFile(filename)
    storage_df = xl.parse("Storage Rooms")
    storage_rows = storage_df.values.tolist()

    storage_cap_dict = {}
    for row in storage_rows:
        storage_cap_dict[row[0]] = float(row[3])

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
    item_dict = {}
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

    xl = pd.ExcelFile(filename)
    items_df = xl.parse("Commodities")
    items_rows = items_df.values.tolist()

    for row in items_rows:
        if row[0] in item_list:
            item_dict[row[0]] = float(row[1])

    return(inventory_dict, echelon_dict, event_room_list, item_dict, requirement_dict, total_inventory_dict, storage_cap_dict)

def costDataReader(filename):
    xl = pd.ExcelFile(filename)
    df = xl.parse("Cost Data", header=None)
    rows = df.values.tolist()
    cost_dict = {}
    for rowIndex in range (1, len(rows)):
        for columnIndex in range (1, (rowIndex + 1)):
            cost_dict[(rows[rowIndex][0], rows[0][columnIndex])] = rows[rowIndex][columnIndex]
            cost_dict[(rows[0][columnIndex], rows[rowIndex][0])] = rows[rowIndex][columnIndex]
    return cost_dict

def datetimeReader(date):
    searchObject = re.search("(\d{1,2})\/(\d{1,2})\/(\d{1,2}) (\d{1,2}):(\d{2})", date)
    (month, day, year, hour, minute) = searchObject.groups()
    date = datetime.datetime(int(year), int(month), int(day), int(hour), int(minute))
    return date

def constructor(echelon_dict, eventRoomList, item_dict, costDict, requirementDict, inventory_dict, total_inventory_dict, storage_cap_dict):

    #Creates 4 sets of arcs:
    #   movement_arc_dict       All b to a, room to room movement arcs (decisions)
    #   storage_cap_arc_dict    All a to b storage arcs (decisions)
    #   event_req_arc_dict      All a to b event requirement arcs (givens)
    #   utility_arc_dict        All arcs originating at the s node or between t nodes (givens)

    storageRoomList = ["S1", "S2", "S3"]
    # , "S4", "S5", "S6", "S7", "S8", "S9", "S10",
    #         "S11", "S12", "S13", "S14", "S15", "S16", "S17", "S18", "S19", "S20",
    #         "S21", "S22", "S23", "S24", "S25", "S26", "S27", "S28", "S29", "S30",
    #         "S31", "S32", "S33", "S34", "S35", "S36", "S37", "S38", "S39", "S40",
    #         "S41", "S42", "S43", "S44", "S45", "S46", "S47", "S48", "S49", "S50",
    #         "S51", "S52", "S53", "S54", "S55", "S56", "S57", "S58", "S59"]
    allRoomList = eventRoomList + storageRoomList
    #print(allRoomList)
    movement_arc_dict = {}
    storage_cap_arc_dict = {}
    event_req_arc_dict = {}
    utility_arc_dict = {}
    itemList = item_dict.keys()

    #Create general set of arcs for all time echelons other than the first and
    #last

    for echelon in echelon_dict:
        for roomI in allRoomList:
            for roomJ in allRoomList:
                for ab in ["a", "b"]:
                    if ab == "a":
                        if roomI == roomJ:
                            if (roomI, echelon) in requirementDict:
                                for requirement in requirementDict[(roomI, echelon)]:
                                    item, qty = requirement[0], requirement[1]
                                    event_req_arc_dict[((roomI, echelon, "a"),(roomJ, echelon, "b"), item)] = (qty, qty, 0)
                            if roomI in storageRoomList:
                                for item in itemList:
                                    ub = int(storage_cap_dict[roomI] / item_dict[item])
                                    storage_cap_arc_dict[((roomI, echelon, "a"),(roomJ, echelon, "b"), item)] = (0, ub, 0)
                    if ab == "b":
                        if echelon != len(echelon_dict.keys()):
                            for item in itemList:
                                movement_arc_dict[((roomI, echelon, "b"), (roomJ, echelon + 1, "a"), item)] = (0, 100000000, costDict[(roomI, roomJ)])

    #Create set of arcs for inital starting conditions from s node to each room

    for room in allRoomList:
        for item in itemList:
            movement_arc_dict[((room, (len(echelon_dict.keys())), "b"), ("t", (len(echelon_dict.keys()) + 1), "a"), item)] = (0, 1000000000, 0)
            if room in storageRoomList:
                utility_arc_dict[(("s", 0, "a"), (room, 0, "b"), item)] = (inventory_dict[(room, item)], inventory_dict[(room, item)], 0)
            else:
                utility_arc_dict[(("s", 0, "a"), (room, 0, "b"), item)] = (0, 0, 0)

    #Create set of movement arcs for the first movement period

    for roomI in allRoomList:
        for roomJ in allRoomList:
            for item in itemList:
                movement_arc_dict[((roomI, 0, "b"), (roomJ, 1, "a"), item)] = (0, 100000000, costDict[(roomI, roomJ)])

    rooms = len(allRoomList)
    for item in itemList:
        utility_arc_dict[(("t", (len(echelon_dict.keys()) + 1), "a"), ("t", (len(echelon_dict.keys()) + 1), "b"), item)] = (total_inventory_dict[item], total_inventory_dict[item], 0)

    return movement_arc_dict, storage_cap_arc_dict, event_req_arc_dict, utility_arc_dict, allRoomList

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
    arcList.append(["Xi", "Yi", "Zi", "Xj", "Yj", "Zj", "Item", "Lij", "Uij", "Cij"])
    for arc in arcDict.keys():
        arcList.append([arc[0][0], arc[0][1], arc[0][2], arc[1][0], arc[1][1],
            arc[1][2], arc[2], arcDict[arc][0], arcDict[arc][1], arcDict[arc][2]])

    #Writes to master excel sheet
    book = load_workbook(excel_filename)
    df = pd.DataFrame(arcList)
    writer = pd.ExcelWriter(excel_filename, engine='openpyxl')
    writer.book = book
    writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
    df.to_excel(writer, sheet_name=sheet_name, index=False, index_label=False, header=False)
    writer.save()
    return None

# def auxiliaryWriter(filename, sheet_name):
#     room_list = []
#     room_list.append(["Room ID", "Room Name"])
#     for room in roomDict.keys():
#         room_list.append([room, roomDict[room]])
#     book = load_workbook("EquipmentInventory.xlsx")
#     df = pd.DataFrame(room_list)
#     writer = pd.ExcelWriter("EquipmentInventory.xlsx", engine='openpyxl')
#     writer.book = book
#     writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
#     df.to_excel(writer, sheet_name=sheet_name, index=False, index_label=False, header=False)
#     writer.save()
#     return None

def main(args):

    cost_dict = costDataReader(excel_filename)
    #print(cost_dict)
    (inventory_dict, echelon_dict, event_room_list, item_list, requirement_dict, total_inventory_dict, storage_cap_dict) = currentStateReader(excel_filename)
    #print(total_inventory_dict)
    # print(inventory_dict)
    # print("\n\n")
    # print(requirement_dict)
    # print("\n\n")
    # print(echelon_dict)
    # print("\n\n")
    # print(event_room_list)
    # print("\n\n")
    # print(item_list)

    movement_arc_dict, storage_cap_arc_dict, event_req_arc_dict, utility_arc_dict, allRoomList = constructor(echelon_dict, event_room_list, item_list, cost_dict, requirement_dict, inventory_dict, total_inventory_dict, storage_cap_dict)
    # arcDictWriter(movement_arc_dict, "MovementArcs.csv")
    # arcDictWriter(storage_cap_arc_dict, "StorageCapacityArcs.csv")
    # arcDictWriter(event_req_arc_dict, "EventRequirementArcs.csv")
    # arcDictWriter(utility_arc_dict, "UtilityArcs.csv")
    excelWriter(movement_arc_dict, excel_filename, "Movement Arcs")
    excelWriter(storage_cap_arc_dict, excel_filename, "Storage Room Arcs")
    excelWriter(event_req_arc_dict, excel_filename, "Event Room Arcs")
    excelWriter(utility_arc_dict, excel_filename, "Utility Arcs")
    #auxiliaryWriter(room_dict, "EquipmentInventory.xlsx", "Room Dictionary")
    #print(eventRoomList)
    #print(itemList)
    # print((len(movement_arc_dict) + len(storage_cap_arc_dict) + len(event_req_arc_dict)))
    # print(len(allRoomList))
    # print(len(event_room_list))
    # print(len(echelon_dict.keys()))
    print("\a")

if __name__ == '__main__':
    import sys
    main(sys.argv)

