import threading
import string
import time
import os
import sqlite3
from noxLogger import noxLogger
from ThermometerItem import ThermometerItem
import random
from DatabaseManager import DatabaseManager
import re


# I am the relay service class.U
class TemperatureService:
    namespace = ""
    server = ""
    serverNamespace = ""
    root = ""
    items = []
    tree = {}
    DatabaseManager = None

    def __init__(self, server, servernamespace):
        self.DatabaseManager = DatabaseManager()
        self.scanThread = None
        self.scanEnable = False
        self.namespace = "nox.lightsystem.opc.temperature"
        self.server = server
        self.serverNamespace = servernamespace
        self.root = self.server.get_objects_node()

        # Read thermometer data
        queryString = """
SELECT
    `opc_item`.`opc_item_address`,
    `temperature`.`temperature_bus`
FROM 
    `temperature`
JOIN `opc_item` USING (`opc_item_id`)
JOIN `opc_server` USING (`opc_server_id`)
WHERE TRUE
	AND `opc_server`.`opc_server_id` &1 = 1
    AND `opc_item`.`opc_item_flags` &1 = 1
    AND `temperature`.`temperature_flags` &1 = 1
"""
        queryData = (1, 2, 3)
        thermometerCursor = self.DatabaseManager.read(queryString, queryData)
        for row in thermometerCursor:
            thermometerItem = ThermometerItem(row)
            thermometerItem.localNode = self.MakeNode(thermometerItem.thermometer_address)
            self.items.append(thermometerItem)

    # Create new branches to the end node
    def GetBranchedNode(self, tree):
        branches = tree.split(".")
        branchAddress = ""
        branchIndex = 1
        parentNode = self.root
        delim = ""
        del branches[-1]
        for branch in branches:
            branchAddress = branchAddress + delim + branch
            if not branchAddress in self.tree:
                parentNode = parentNode.add_object(self.serverNamespace, branch)
                self.tree[branchAddress] = parentNode
            else:
                parentNode = self.tree[branchAddress]
            delim = "."
            branchIndex = branchIndex + 1
        return parentNode

    # Return last Node name
    def GetEndNode(self, tree):
        return tree.split(".")[-1]

    # Generate Tree Branches and the end node.
    def MakeNode(self, tree):
        return self.GetBranchedNode(tree).add_variable(self.serverNamespace, self.GetEndNode(tree), 1)

    # Start the server
    def start(self):
        self.server.start()

    # Stop the server
    def stop(self):
        self.server.stop()

    # Scanner thread
    def _scan(self):
        while self.scanEnable:
            for temperatureItem in self.items:
                filename = "/sys/bus/w1/devices/" + temperatureItem.thermometer_bus + "/w1_slave"
                content = open(filename, 'r').read()
                split = re.split("(\w).[t][=]", content)
                strValue = split[2].strip()
                floatValue = float(strValue)
                centigrades = floatValue / 1000
                noxLogger.debug(temperatureItem.thermometer_address + " is now " + str(centigrades))
                temperatureItem.localNode.set_value(centigrades)
            time.sleep(10)

    # I will enable the scanner thread.
    def scan_on(self):
        self.scanThread = threading.Thread(target=self._scan)
        self.scanEnable = True
        self.scanThread.start()

    # I will disable the scanner thread.
    def scan_off(self):
        self.scanEnable = False
        self.scanThread.join()
