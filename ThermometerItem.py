# I am a Thermometer item.
class ThermometerItem:
    # I am the OPC address.
    thermometer_address = None
    # I am the 1-wire address.
    thermometer_bus = None

    # I will construct the ThermometerItem.
    def __init__(self, row):
        self.thermometer_address = row[0]
        self.thermometer_bus = row[1]

    # I will handle the update of the item.
    def update(self):
        return None
