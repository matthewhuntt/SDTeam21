class Satchel:
    def __init__(self):
        self.equip_dictionary = {}
    def add_item(self, item, quantity):
        if item in self.equip_dictionary.keys():
            self.equip_dictionary[item] += quantity
        else:
            self.equip_dictionary[item] = quantity
    def remove_item(self, item, quantity):
        if item in self.equip_dictionary.keys():
            if self.equip_dictionary[item] < quantity:
                ret_quantity = self.equip_dictionary[item]
                self.equip_dictionary[item] = 0
                return ret_quantity
            else:
                self.equip_dictionary[item] -= quantity
                return quantity
        else:
            return 0
    def get_level(self, item):
        if item in self.equip_dictionary.keys():
            return self.equip_dictionary[item]
        else:
            return 0
    # get shortfall when compared to satchel_b
    def get_shortfall(self, satchel_b):
        shortfall = Satchel()
        for item in satchel_b.keys():
            cur_level = self.get_level(item)
            foreign_level = satchel_b.get_level(item)
            if (cur_level >= foreign_level):
                shortfall.add_item(item, 0)
            else:
                shortfall.add_item(item, foreign_level-cur_level)
        return shortfall
    def is_empty(self):
        for val in self.equip_dictionary.values():
            if val > 0:
                return False
        return True

class Room:
    def __init__(self, name, room_type, inventory, capacity, total_capacity):
        self.name = name
        self.inventory = inventory
        self.room_type = room_type
        self.distances = {}
        self.capacity  = capacity
        self.total_capacity = total_capacity
    def __hash__(self):
        return hash(self.name)
    def __eq__(self, other):
        return self.name == other.name
    def get_cumulative_dimension(self):
        cumulative_dimension = 0
        for item in self.inventory.equip_dictionary.keys():
            cumulative_dimension += self.inventory.get_level(item) * equipment_dimension_lookup[item]
        return cumulative_dimension
    def load_distances(self, distance_table, room_list):
        for room in room_list:
            if room == self:
                continue
            else:
                self.distances[room] = distance_table[(distance_table["Start"] == self.name) & (distance_table["End"] == room.name)]["Distance"].min()
    def get_closest_room (self, room_type):
        min_room = Room("dummy", "na", Satchel(), Satchel(), 0)
        min_distance = float('Inf')
        for room in self.distances.keys():
            if self.distances[room] < min_distance and room.room_type == room_type:
                min_room = room
                min_distance = self.distances[room]
        return min_room
    def find_new_room (self, room_type, leper_list):
        min_room = Room("dummy", "na", Satchel(), Satchel(), 0)
        min_distance = float('Inf')
        for room in self.distances.keys():
            if self.distances[room] < min_distance and room.room_type == room_type and room not in leper_list:
                min_room = room
                min_distance = self.distances[room]
        return min_room
    def remove_item(self,item, quantity):
        return self.inventory.remove_item(item, quantity)
    def add_item(self, item, quantity):
        cumulative_shortfall = 0
        cumulative_dimension = self.get_cumulative_dimension()
        if (cumulative_dimension + quantity * equipment_dimension_lookup[item]) > self.total_capacity:
            new_dimension = self.total_capacity - cumulative_dimension
            if new_dimension < 0:
                return quantity
            else:
                new_quantity = math.floor(new_dimension/equipment_dimension_lookup[item])
                cumulative_shortfall = quantity - new_quantity
                quantity = new_quantity
        if (self.inventory.get_level(item) + quantity) > self.capacity.get_level(item):
            amount_to_add = self.capacity.get_level(item) - self.inventory.get_level(item)
            self.inventory.add_item(item, amount_to_add)
            return (quantity - amount_to_add) + cumulative_shortfall
        else:
            self.inventory.add_item(item, quantity)
            return cumulative_shortfall

# requirements: a list of [(Event Room), Equipment, Quantity, Direction] representing requirements
#     Direction: True if equipment is coming in, False if equipment is coming out
def build_naive_movement(rooms, requirements):
    movement_matrix = pd.DataFrame(columns=["equip_type", "quantity", "start", "end"])
    prev_location = "null"
    req_len = len(requirements)
    for tup in requirements:
        event_room = tup[0]
        item = tup[1]
        quantity = tup[2]
        direction = tup[3]
        
        print(str((requirements.index(tup)/req_len)*100) + "%")
        
        if prev_location == "null":
            prev_location = event_room.name
        else:
            movement_matrix = movement_matrix.append({"equip_type": "WORKER", "quantity": 1, "start": prev_location, "end": event_room.name}, ignore_index=True)
            prev_location = event_room.name
        
        if direction:
            # go to closest storage room recursively until all quantity has been gathered
            storage_room = event_room.get_closest_room("storage")
            quantity_fulfilled = 0
            trip_quantity = 0
            visited_rooms = []
            while quantity_fulfilled < quantity:
                if storage_room.name == "dummy":
                    print(tup[0].name)
                    print(tup)
                    return
                if quantity_fulfilled == 0:
                    movement_matrix = movement_matrix.append({"equip_type": "WORKER", "quantity": 1, "start": prev_location, "end": storage_room.name}, ignore_index = True)
                else:
                    movement_matrix = movement_matrix.append({"equip_type": item, "quantity": trip_quantity, "start": prev_location, "end": storage_room.name}, ignore_index = True)
                #print ("------------------")
                old_tc = trip_quantity
                #print ("Trying to find " + str(quantity - quantity_fulfilled) + " " + item + "(s)")
                #print ("STORAGE ROOM " + storage_room.name + " has " + str(storage_room.inventory.equip_dictionary[item]) + " " + item + "(s)")
                trip_quantity += storage_room.remove_item(item, quantity - quantity_fulfilled)
                #print("Removed " + str(trip_quantity - old_tc))
                #print ("Now STORAGE ROOM " + storage_room.name + " has " + str(storage_room.inventory.equip_dictionary[item]) + " " + item + "(s)")
                quantity_fulfilled += (trip_quantity-old_tc)
                while trip_quantity > equipment_capacity_lookup[item]:
                    movement_matrix = movement_matrix.append({"equip_type": item, "quantity": equipment_capacity_lookup[item], "start": storage_room.name, "end": event_room.name}, ignore_index = True)
                    movement_matrix = movement_matrix.append({"equip_type": "WORKER", "quantity": 1, "start": event_room.name, "end": storage_room.name}, ignore_index = True)
                    trip_quantity -= equipment_capacity_lookup[item]
                prev_location = storage_room.name
                visited_rooms.append(storage_room)
                storage_room = storage_room.find_new_room("storage", visited_rooms)
            # return to event room
            movement_matrix = movement_matrix.append({"equip_type": item, "quantity": trip_quantity, "start": prev_location, "end": event_room.name}, ignore_index = True)
        else:
            # go to closest storage room recursively
            storage_room = event_room.get_closest_room("storage")
            quantity_to_dispose = quantity
            visited_rooms = []
            trip_quantity = 0
            prev_location = event_room.name
            while quantity_to_dispose > 0:
                trip_quantity = min(equipment_capacity_lookup[item], quantity_to_dispose)
                quantity_to_dispose -= trip_quantity
                while trip_quantity > 0:
                    if storage_room.name == "dummy":
                        print(tup[0].name)
                        print(tup)
                        return movement_matrix
                    movement_matrix = movement_matrix.append({"equip_type": item, "quantity": trip_quantity, "start": prev_location, "end": storage_room.name}, ignore_index = True)
                    trip_quantity = storage_room.add_item(item, trip_quantity)
                    if trip_quantity > 0:
                        prev_location = storage_room.name
                        visited_rooms.append(storage_room)
                        storage_room = storage_room.find_new_room("storage", visited_rooms)
                movement_matrix = movement_matrix.append({"equip_type": "WORKER", "quantity": 1, "start": storage_room.name, "end": event_room.name}, ignore_index = True)
    
    return movement_matrix



# requirements: a list of [(Event Room), Equipment, Quantity, Direction] representing requirements
#     Direction: True if equipment is coming in, False if equipment is coming out
def build_enhanced_movement(rooms, requirements):
    movement_matrix = pd.DataFrame(columns=["equip_type", "quantity", "start", "end"])
    prev_location = "null"
    req_len = len(requirements)
    for tup in requirements:
        event_room = tup[0]
        item = tup[1]
        quantity = tup[2]
        direction = tup[3]
        
        print(str((requirements.index(tup)/req_len)*100) + "%")
        
        if prev_location == "null":
            prev_location = event_room.name
        else:
            movement_matrix = movement_matrix.append({"equip_type": "WORKER", "quantity": 1, "start": prev_location, "end": event_room.name}, ignore_index=True)
            prev_location = event_room.name
        
        if direction:
            # go to closest storage room recursively until all quantity has been gathered
            storage_room = event_room.get_closest_room("storage")
            quantity_fulfilled = 0
            trip_quantity = 0
            visited_rooms = []
            while quantity_fulfilled < quantity:
                if storage_room.name == "dummy":
                    print(tup[0].name)
                    print(tup)
                    return
                if storage_room.inventory.get_level(item) == 0:
                    visited_rooms.append(storage_room)
                    storage_room = storage_room.find_new_room("storage", visited_rooms)
                    continue
                if quantity_fulfilled == 0:
                    movement_matrix = movement_matrix.append({"equip_type": "WORKER", "quantity": 1, "start": prev_location, "end": storage_room.name}, ignore_index = True)
                else:
                    movement_matrix = movement_matrix.append({"equip_type": item, "quantity": trip_quantity, "start": prev_location, "end": storage_room.name}, ignore_index = True)
                #print ("------------------")
                old_tc = trip_quantity
                #print ("Trying to find " + str(quantity - quantity_fulfilled) + " " + item + "(s)")
                #print ("STORAGE ROOM " + storage_room.name + " has " + str(storage_room.inventory.equip_dictionary[item]) + " " + item + "(s)")
                trip_quantity += storage_room.remove_item(item, quantity - quantity_fulfilled)
                #print("Removed " + str(trip_quantity - old_tc))
                #print ("Now STORAGE ROOM " + storage_room.name + " has " + str(storage_room.inventory.equip_dictionary[item]) + " " + item + "(s)")
                quantity_fulfilled += (trip_quantity-old_tc)
                while trip_quantity > equipment_capacity_lookup[item]:
                    movement_matrix = movement_matrix.append({"equip_type": item, "quantity": equipment_capacity_lookup[item], "start": storage_room.name, "end": event_room.name}, ignore_index = True)
                    movement_matrix = movement_matrix.append({"equip_type": "WORKER", "quantity": 1, "start": event_room.name, "end": storage_room.name}, ignore_index = True)
                    trip_quantity -= equipment_capacity_lookup[item]
                prev_location = storage_room.name
                visited_rooms.append(storage_room)
                storage_room = storage_room.find_new_room("storage", visited_rooms)
            # return to event room
            movement_matrix = movement_matrix.append({"equip_type": item, "quantity": trip_quantity, "start": prev_location, "end": event_room.name}, ignore_index = True)
        else:
            # go to closest storage room recursively
            storage_room = event_room.get_closest_room("storage")
            quantity_to_dispose = quantity
            visited_rooms = []
            trip_quantity = 0
            prev_location = event_room.name
            while quantity_to_dispose > 0:
                trip_quantity = min(equipment_capacity_lookup[item], quantity_to_dispose)
                quantity_to_dispose -= trip_quantity
                while trip_quantity > 0:
                    if storage_room.name == "dummy":
                        print(tup[0].name)
                        print(tup)
                        return movement_matrix
                    movement_matrix = movement_matrix.append({"equip_type": item, "quantity": trip_quantity, "start": prev_location, "end": storage_room.name}, ignore_index = True)
                    trip_quantity = storage_room.add_item(item, trip_quantity)
                    if trip_quantity > 0:
                        prev_location = storage_room.name
                        visited_rooms.append(storage_room)
                        storage_room = storage_room.find_new_room("storage", visited_rooms)
                        while storage_room.inventory.get_level(item) == storage_room.capacity.get_level(item):
                            visited_rooms.append(storage_room)
                            storage_room = storage_room.find_new_room("storage", visited_rooms)
                movement_matrix = movement_matrix.append({"equip_type": "WORKER", "quantity": 1, "start": storage_room.name, "end": event_room.name}, ignore_index = True)
    
    return movement_matrix

def enhanced_cost_function(movement_matrix, distance_matrix, equip_capacity, speed):
    movement_matrix = movement_matrix.merge(distance_matrix, on=["Start", "End"])
    movement_matrix["trips"] = movement_matrix.apply(lambda x: math.ceil(x["quantity"]/equip_capacity[x["equip_type"]]), axis=1)
    movement_matrix["cost"] = movement_matrix["trips"] * movement_matrix["Distance"] / speed
    return movement_matrix["cost"].sum()
