# Representation of a Measurement Point, which is a single measurement.
class McMeasurementPoint:
  def __init__(self, mcMac, timestamp, datarate, latency):
    self.mcMac = mcMac
    self.timestamp = timestamp
    self.datarate = datarate
    self.latency = latency

  def __str__(self):
      return ("mcMac: " + self.mcMac
  + "; timestamp: " + str(self.timestamp)
  + "; datarate: " + str(self.datarate)
  + "; latency: " + str(self.latency))
