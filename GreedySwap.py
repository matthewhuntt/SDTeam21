import csv
import pandas as pd
from openpyxl import load_workbook

class DataStorage:
    '''Class to store network data.'''
    pass

def excelReader(filename, sheet_name):
    '''Reads supporting data from master excel file into a dictionary'''

    excel_data = {}
    xl = pd.ExcelFile(filename)
    inventory_df = xl.parse(sheet_name)
    inventory_rows = inventory_df.values.tolist()
    if sheet_name == 'Commodities':
        for row in inventory_rows:
            if any(row): # Handles Empty Lines from OS swap
                excel_data[row[0]] = row[1]
    if sheet_name == 'Storage Rooms':
        for row in inventory_rows:
            if any(row): # Handles Empty Lines from OS swap
                excel_data[row[0]] = row[3]
    if sheet_name == 'Room Dictionary':
        for row in inventory_rows:
            if any(row): # Handles Empty Lines from OS swap
                excel_data[str(row[0])] = row[1]
    return excel_data

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

def csvReader(filename):
    dictionary = {}
    with open(filename) as f:
        reader = csv.reader(f, delimiter='|')
        if filename == "ModelOutput.csv":
            for row in reader:
                if any(row):
                    dictionary[((row[0], row[1], row[2]), (row[3], row[4], row[5]), row[6])] = float(row[7])
        if filename == "UnderCap.csv":
            for row in reader:
                if any(row):
                    if row[1] in dictionary:
                        dictionary[row[1]][(row[0], row[1], "a")] = float(row[3])
                    else:
                        dictionary[row[1]] = {(row[0], row[1], "a"): float(row[3])}
        if filename == "OverCap.csv":
            for row in reader:
                if any(row):
                    if row[1] in dictionary:
                        dictionary[row[1]][(row[0], row[1], "a")] = float(row[3])
                    else:
                        dictionary[row[1]] = {(row[0], row[1], "a"): float(row[3])}
    return dictionary

def greedy_swap(statics, movement_arcs_dict, under_cap, over_cap, model_cost):
    print("greedy_swap")
    original_cost = model_cost
    cost_dict = statics.cost_dict
    priority_list = statics.priority_list

    time_echelons = {} ## TODO: Rename?
    for time in over_cap:
        time_echelons[time] = sorted(over_cap[time], key=lambda k: over_cap[time][k], reverse=True)
        # Sort:
        #     reverse = True
        #       - descending
        #     key = lambda (argument : expression)
        #       - Iterate over_cap[time].keys() to sort
        #            for k in over_cap[time].keys():
        #                k -> over_cap[time][k]

    with open("log_file.txt","w") as f:
        for time in sorted(list(time_echelons))[:-1]:
            for over_node in time_echelons[time]:
                # f.write("__________________________________\n")
                # f.write("Over Node: " + str(over_node) + "\n")
                # f.write("----------------------------------\n")
                # print("__________________________________")
                # print("Over Node: " + str(over_node))

                blue_arc_dict = {}
                green_arc_dict = {}
                for arc in movement_arcs_dict:
                    tail, head, commodity = arc
                    if tail == (over_node[0], over_node[1], 'b'):
                        if movement_arcs_dict[arc] > 0:
                            if commodity in green_arc_dict:
                                green_arc_dict[commodity].append(arc)
                            else:
                                green_arc_dict[commodity] = [arc]
                    if head == over_node:
                        if movement_arcs_dict[arc] > 0:
                            if commodity in blue_arc_dict:
                                blue_arc_dict[commodity].append(arc)
                            else:
                                blue_arc_dict[commodity] = [arc]

                for commodity in priority_list:
                    # f.write("\n")
                    # f.write("Now moving " + str(commodity) + "\n")
                    # print("Now moving " + str(commodity))

                    red_arc_dict = {}
                    orange_arc_dict = {}
                    if commodity in blue_arc_dict:
                        for blue_arc in blue_arc_dict[commodity]:
                            for under_node in under_cap[time]:
                                origin_node = blue_arc[0]
                                cost = cost_dict[(origin_node[0], under_node[0])] - cost_dict[(origin_node[0], over_node[0])]
                                red_arc_dict[(origin_node, under_node, commodity)] = cost
                                # cost to add red_arc to current under_node and remove blue arc to over_node
                                # All within a single commodity type!
                    if commodity in green_arc_dict:
                        for green_arc in green_arc_dict[commodity]:
                            for under_node in under_cap[time]:
                                destination_node = green_arc[1]
                                cost = cost_dict[(under_node[0], destination_node[0])] - cost_dict[(over_node[0], destination_node[0])]
                                orange_arc_dict[((under_node[0], time, 'b'), destination, commodity)] = cost

                    insertion_dict = {}
                    for red in red_arc_dict:
                        for orange in orange_arc_dict:
                            insertion_dict[(red, orange)] = red_arc_dict[red] + orange_arc_dict[orange]

                    # below func gives [(key_with_lowest_value), (key_with_second_lowest_value), ...]
                    sorted_insertion_list = sorted(insertion_dict, key=lambda k: insertion_dict[k])
                    for red_arc, orange_arc in sorted_insertion_list:
                        # f.write("__________________________________\n")
                        # f.write("Red Arc: " +str(red_arc) + "\n")
                        origin_node = red_arc[0]
                        under_node = red_arc[1]
                        destination_node = orange_arc[1]

                        blue_arc = (origin_node, over_node, commodity)
                        green_arc = (over_node, destination_node, commodity)

                        if (over_node in over_cap[time]) and (movement_arcs_dict[blue_arc] > 0) and (movement_arcs_dict[green_arc] > 0):
                            if under_node in under_cap[time]:
                                # f.write("----------------------------------\n")
                                # f.write("Rerouting " +str(commodity) + " from " + str(origin_node) + "\n")
                                # f.write("Now checking " + str(under_node) + "\n")
                                a = abs(over_cap[time][over_node]) # Volume over capacity still to move from over_node
                                b = abs(under_cap[time][under_node]) # Spare capacity in under_node
                                c = abs(movement_arcs_dict[blue_arc]) # Volume available to move from origin_node
                                d = abs(movement_arcs_dict[green_arc]) # Volume available to move to destination_node
                                swap_count = min(a, b, c, d)
                                # f.write("    Volume to move from over_node     | "+ str(a) + "\n")
                                # f.write("    Space available in under_node     | "+ str(b) + "\n")
                                # f.write("    Num of commodity from origin_node | "+ str(c) + "\n")
                                # f.write("    Num of commodity to destination_node | "+ str(d) + "\n")
                                if swap_count > 0:
                                    # print("Moved " + str(swap_count) + " from " + str(over_node[0]) + " to " + str(under_node[0]) + " in t = " + str(over_node[1]))
                                    # f.write("Moved " + str(swap_count) + " from " + str(over_node[0]) + " to " + str(under_node[0]) + " in t = " + str(over_node[1]) + "\n")
                                    over_cap[time][over_node] -= swap_count
                                    under_cap[time][under_node] += swap_count

                                    movement_arcs_dict[blue_arc] -= swap_count
                                    movement_arcs_dict[red_arc] += swap_count
                                    movement_arcs_dict[green_arc] -= swap_count
                                    movement_arcs_dict[orange_arc] += swap_count

                                    model_cost += insertion_dict[(red_arc, orange_arc)] * swap_count

                                    # if movement_arcs_dict[(origin_node, over_node, commodity)] == 0:
                                    #     print(str(commodity) + " from " + str(origin_node) + " is now depleted. Move to next Blue Arc.")
                                    #     f.write(str(commodity) + " from " + str(origin_node) + " is now depleted. Move to next Blue Arc."+ "\n")
                                    if under_cap[time][under_node] == 0:
                                        # print(str(under_node) + " is now full")
                                        # f.write(str(under_node) + " is now full" + "\n")
                                        del under_cap[time][under_node]

                                    # print("Amount remaining: " + str(over_cap[time][over_node]))
                                    # f.write("Amount remaining: " + str(over_cap[time][over_node]) + "\n")

                                # f.write("----------------------------------\n")
                            if over_cap[time][over_node] == 0:
                                del over_cap[time][over_node]
                        # else:
                        #     f.write("    Num of commodity from origin_node: " + str(movement_arcs_dict[blue_arc]) + "\n")

                        #     if over_node in over_cap[time]:
                        #         f.write("    Volume to move from over_node: " + str(over_cap[time][over_node]) + "\n")
                        #     else:
                        #         f.write(str(over_node) + " not in over_cap[time]" + "\n")

                        #     if under_node in under_cap[time]:
                        #         f.write("    Space available in under_node: " + str(under_cap[time][under_node]) + "\n")
                        #     else:
                        #         f.write(str(under_node) + " not in under_cap[time]" + "\n")
        if any(time_echelons):
            time = sorted(list(time_echelons))[-1]
            for over_node in time_echelons[time]:
                    # f.write("__________________________________\n")
                    # f.write("Over Node: " + str(over_node) + "\n")
                    # f.write("----------------------------------\n")
                    print("__________________________________")
                    print("Over Node: " + str(over_node))

                    blue_arc_dict = {}
                    for arc in movement_arcs_dict:
                        tail, head, commodity = arc
                        if head == over_node:
                            if movement_arcs_dict[arc] > 0:
                                if commodity in blue_arc_dict:
                                    blue_arc_dict[commodity].append(arc)
                                else:
                                    blue_arc_dict[commodity] = [arc]

                    for commodity in priority_list:
                        # f.write("\n")
                        # f.write("Now moving " + str(commodity) + "\n")
                        print("Now moving " + str(commodity))

                        red_arc_dict = {}
                        if commodity in blue_arc_dict:
                            for blue_arc in blue_arc_dict[commodity]:
                                for under_node in under_cap[time]:
                                    origin_node = blue_arc[0]
                                    cost = cost_dict[(origin_node[0], under_node[0])] - cost_dict[(origin_node[0], over_node[0])]
                                    red_arc_dict[(origin_node, under_node, commodity)] = cost
                                    # cost to add red_arc to current under_node and remove blue arc to over_node
                                    # All within a single commodity type!

                        insertion_dict = red_arc_dict

                        # below func gives [(key_with_lowest_value), (key_with_second_lowest_value), ...]
                        sorted_insertion_list = sorted(insertion_dict, key=lambda k: insertion_dict[k])
                        for red_arc in sorted_insertion_list:
                            if insertion_dict[red_arc] < 0:
                                print(str(red_arc) + ":  " + str(insertion_dict[red_arc]) + "\n")
                            # f.write("__________________________________\n")
                            # f.write("Red Arc: " +str(red_arc) + "\n")
                            origin_node = red_arc[0]
                            under_node = red_arc[1]

                            blue_arc = (origin_node, over_node, commodity)

                            if (over_node in over_cap[time]) and (movement_arcs_dict[blue_arc] > 0):
                                if under_node in under_cap[time]:
                                    # f.write("----------------------------------\n")
                                    # f.write("Rerouting " +str(commodity) + " from " + str(origin_node) + "\n")
                                    # f.write("Now checking " + str(under_node) + "\n")
                                    a = abs(over_cap[time][over_node]) # Volume over capacity still to move from over_node
                                    b = abs(under_cap[time][under_node]) # Spare capacity in under_node
                                    c = abs(movement_arcs_dict[blue_arc]) # Volume available to move from origin_node
                                    swap_count = min(a, b, c)
                                    # f.write("    Volume to move from over_node     | "+ str(a) + "\n")
                                    # f.write("    Space available in under_node     | "+ str(b) + "\n")
                                    # f.write("    Num of commodity from origin_node | "+ str(c) + "\n")
                                    # f.write("    Num of commodity to destination_node | "+ str(d) + "\n")
                                    if swap_count > 0:

                                        # f.write("Moved " + str(swap_count) + " from " + str(over_node[0]) + " to " + str(under_node[0]) + " in t = " + str(over_node[1]) + "\n")
                                        over_cap[time][over_node] -= swap_count
                                        under_cap[time][under_node] += swap_count

                                        movement_arcs_dict[blue_arc] -= swap_count
                                        movement_arcs_dict[red_arc] += swap_count

                                        model_cost += insertion_dict[red_arc] * swap_count
                                        print("Moved " + str(swap_count) + " from " + str(over_node[0]) + " to " + str(under_node[0]) + " in t = " + str(over_node[1]) + " at a cost of " + str(insertion_dict[red_arc] * swap_count))

                                        # if movement_arcs_dict[(origin_node, over_node, commodity)] == 0:
                                        #     print(str(commodity) + " from " + str(origin_node) + " is now depleted. Move to next Blue Arc.")
                                        #     f.write(str(commodity) + " from " + str(origin_node) + " is now depleted. Move to next Blue Arc."+ "\n")
                                        if under_cap[time][under_node] == 0:
                                            # print(str(under_node) + " is now full")
                                            # f.write(str(under_node) + " is now full" + "\n")
                                            del under_cap[time][under_node]

                                        # print("Amount remaining: " + str(over_cap[time][over_node]))
                                        # f.write("Amount remaining: " + str(over_cap[time][over_node]) + "\n")

                                    # f.write("----------------------------------\n")
                                if over_cap[time][over_node] == 0:
                                    del over_cap[time][over_node]




        f.write("\nOUTPUT:\n")
        f.write("MCNF Cost: "+ str(original_cost)+ "\n")
        f.write("Updated Cost: "+ str(model_cost)+ "\n")
        f.write("Diff in Cost: "+ str(model_cost - original_cost)+ "\n")
        f.write("Remaining over nodes:\n")
        for time in  over_cap:
            for over_node in  over_cap[time]:
                f.write(": ".join([str(over_node), str(over_cap[time][over_node])])+ "\n")
        for time in  over_cap:
            for over_node in  over_cap[time]:
                for x in movement_arcs_dict:
                    if movement_arcs_dict[x] >0:
                        if x[1] == over_node:
                            f.write(str(x) + ": " + str(movement_arcs_dict[x]) + "\n")

        f.write("Remaining under nodes:\n")
        for time in under_cap:
            for under_node in  under_cap[time]:
                f.write(": ".join([str(under_node), str(under_cap[time][under_node])])+ "\n")
        # for time in under_cap:
        #     for under_node in  under_cap[time]:
        #         for x in movement_arcs_dict:
        #             if x[1] == under_node:
        #                 f.write(str(x) + ": " + str(movement_arcs_dict[x]) + "\n")

def main(args):
    statics = DataStorage()
    statics.room_caps = excelReader("EquipmentInventory.xlsx", "Storage Rooms")
    statics.commodity_vols = excelReader("EquipmentInventory.xlsx", "Commodities")
    statics.cost_dict = costDataReader("EquipmentInventory.xlsx")
    statics.priority_list = ["8 X 30 TABLES", "6 X 30 TABLES", "8 X 18 TABLES", "6 X 18 TABLES", "66 ROUND TABLES", "HIGH BOYS", "30 COCKTAIL ROUNDS",
        "MEETING ROOM CHAIRS", "PODIUMS", "STAGE SKIRT DOLLIES", "TABLE SKIRT DOLLIES", "MEETING ROOM CHAIR DOLLIES",
        "66 ROUND TABLE DOLLIES", "FOLDING CHAIR DOLLIES (V STACK)", "FOLDING CHAIR DOLLIES (SQUARE STACK)", "HIGH BOY DOLLIES",
        "LONG TABLE DOLLIES", "SHORT TABLE DOLLIES", "STAND UP TABLE DOLLIES", "16RISERS 6 X 8", "24RISERS 6 X 8", "32RISERS 6 X 8", "(3) STEP UNIT WITH RAIL",
        "(3) STEP UNIT WITHOUT RAIL", "(2) STEP UNIT WITH RAIL", "(2) STEP UNIT WITHOUT RAIL","SETS OF STAGE STEPS", "16RISERS 6 X 8", "24RISERS 6 X 8", "30 STAND-UP ROUNDS"]

    movement_arcs_dict = csvReader('ModelOutput.csv')
    under_cap = csvReader('UnderCap.csv')
    over_cap = csvReader('OverCap.csv')
    with open("output_cost.txt") as f:
        model_cost = float(f.readline())
    greedy_swap(statics, movement_arcs_dict, under_cap, over_cap, model_cost)
    print("\a")

if __name__ == '__main__':
    import sys
    main(sys.argv)

