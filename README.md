# SDTeam21

MCNF.py

This file houses the optimization model. It runs in Gurobi using the data in MCNFdata.csv.

MCNFData.csv

<<<<<<< HEAD
This file holds the data for the optimization model.



=======
This file holds the data for the optimization model.

Transform.py

This file manipulates the data in SetupData.csv and outputs a file in the same format as MCNFData.csv.

SetupData.csv

This holds a sample of the manually input setup data for testing pruposes.

In the case where multiple rooms are combined into one space for an event setting , we will record the equipmet requirements as requirements for the loswest numbered room.
Ex:
The following requirement:
 - 20 Meeting Room Chairs to B 212/213
will be recorded as:
 - 20 Meeting Room Chairs to B 212


>>>>>>> 245619da98c20b857cd9fb677ff38427560a6c91
