from flask import Flask, json, request
import requests
import subprocess
from datetime import datetime
from getmac import get_mac_address as gma
import time
from McMeasurementPoint import McMeasurementPoint
from flask_apscheduler import APScheduler

api = Flask(__name__)
scheduler = APScheduler()

lastDatarate=0
lastLatency=0
lastDatarateReceivedAt = ""
lastLatencyReceivedAt = ""
measurementsStartedAt = ""
endpointIP="-"
measurementNetworkNamespace="5gns"
udpSpeed="-"
mPay="1460"
myMac=gma(interface="wlan0")
orchestratorPath=""
orchestratorIp=""
technology="5G"
mode="-R"
measurementPointList = []

# dirty flags for transmitting results. True if metric has been updated, but not yet been sent to the server.
# initialised as False, so all metrics have to be updated once before they are sent.
flagDatarate = False
flagLatency = False
counterDatarateMissing = 0 # this will count up as new latency comes in and is reset after new datarate comes in
limitCounterDatarateMissing = 9 # after this many missed datarate measurements a message is sent to the orchestrator and endpoint gets reset

thresholdAgeOfMeasurement = 2 # time in seconds of no new data incoming, after which a -1 value is applied
timeToWaitBeforeTriggering = 4


def sendLogToOrch(logType, logMessage):
  global orchestratorIp
  global myMac
  orchestratorLogPath = "http://" + orchestratorIp +":5010/log"
  senderString = "MC " + str(myMac)
  myLog = {"sender": senderString, "type": logType, "message": logMessage}
  myLogJSON = json.dumps(myLog)
  res = requests.post(orchestratorLogPath, json=myLogJSON)



def resetFlags():
  global flagDatarate
  global flagLatency
  flagDatarate = False
  flagLatency = False

# return true if all flags are set
def handleDirty():
  global counterDatarateMissing
  global limitCounterDatarateMissing
  if flagDatarate and flagLatency:
    #sendDataToOrchestrator()
    resetFlags()
  elif flagLatency:
    if counterDatarateMissing >= limitCounterDatarateMissing:
      # datarate has been not transmitted for some time - send a report to the orchestrator
      sendLogToOrch("issue", "No data rate for an extended period!")
      counterDatarateMissing = 0 # reset counter in order to not spam the orchestrator


# Set datarate
@api.route('/datarate', methods=['post'])
def post_datarate():
  global lastDatarate
  global flagDatarate
  global counterDatarateMissing
  global lastDatarateReceivedAt
  counterDatarateMissing = 0 # reset counter
  content=request.json
  lastDatarate=content['datarate']
  lastDatarateReceivedAt = content['timestamp']
  print("Received POST request for datarate:")
  print(str(content))
  flagDatarate = True
  handleDirty()
  return json.dumps({"success": True}), 201

# Set latency
@api.route('/latency', methods=['post'])
def post_latency():
  global lastLatency
  global flagLatency
  global counterDatarateMissing
  global lastLatencyReceivedAt
  content=request.json
  lastLatency=content['latency']
  lastLatencyReceivedAt = content['timestamp']
  print("Received POST request for latency: ")
  print(str(content))
  flagLatency = True
  handleDirty()
  counterDatarateMissing = counterDatarateMissing + 1 # increase counter for missing datarate
  return json.dumps({"success": True}), 201



# Get latest measurements as JSON
@api.route('/latestData', methods=['get'])
def get_latestData():
  print("Latest Data has been requested")
  return json.dumps(getLatestDataJSON())

# Get endpoint IP
@api.route('/endpointIP', methods=['get'])
def get_endpointIP():
  global endpointIP
  resultJSON= [{"endpointIP": endpointIP}]
  print("EndpointIP has been requested")
  return json.dumps(resultJSON)

# Get technology
@api.route('/technology', methods=['get'])
def get_technology():
  global technology
  resultJSON= [{"technology": technology}]
  print("Technology has been requested")
  return json.dumps(resultJSON)

# Get measurement interface
@api.route('/measurementNetworkNamespace', methods=['get'])
def get_measurementNetworkNamespace():
  global measurementNetworkNamespace
  resultJSON= [{"measurementNetworkNamespace": measurementNetworkNamespace}]
  print("MeasurementNetworkNamespace has been requested")
  return json.dumps(resultJSON)

# Get udpSteps
@api.route('/udpSpeed', methods=['get'])
def get_udpSpeed():
  global udpSpeed
  resultJSON= [{"udpSpeed": udpSpeed}]
  return json.dumps(resultJSON)

# Get mode
@api.route('/mode', methods=['get'])
def get_mode():
  global mode
  resultJSON= [{"mode": mode}]
  return json.dumps(resultJSON)

# Get message Payload size
@api.route('/mPay', methods=['get'])
def get_mPay():
  global mPay
  resultJSON= [{"mPay": mPay}]
  return json.dumps(resultJSON)

# StartMeasurements
@api.route('/startMeasurements', methods=['post'])
def startMeasurements():
  global endpointIP
  global udpSpeed
  global measurementInterface
  global mPay
  global orchestratorPath
  global orchestratorIp
  global technology
  global mode
  global myMac
  global measurementsStartedAt
  print("Starting measurement routine! Resetting Endpoint...")
# reset endpoint
  content=request.json
  endpointIP=content['meIP']
  print("Endpoint IP is " + endpointIP)
  orchestratorIp=content['orchestratorIp']
  orchestratorPath="http://" + orchestratorIp + ":5010/measurements"
  technology=content['technology']
  if technology == "ETHERNET":
    myMac=gma(interface="enp1s0")
    print("Set interface to enp1s0 for technology ETHERNET, MAC address is " + str(myMac))
  mode=content['mode']
  print("Orchestrator IP is " + orchestratorIp)
  print("Technology is " + technology)
  udpSpeed=content['udpSpeed'] + 'M'
  mPay=content['mPay']
  print("Resetting endpoint @", endpointIP)
  endpointPath="http://" + endpointIP + ":5000/services"
  if technology == "5G":
    cmdResetEndpoint = [ 'sudo', 'ip', 'netns', 'exec', '5gns', 'curl', '--request', 'POST',  endpointPath ]
  elif technology == "WIFI":
    cmdResetEndpoint = [ 'curl', '--request', 'POST',  endpointPath ]
  elif technology == "ETHERNET":
    cmdResetEndpoint = [ 'curl', '--request', 'POST',  endpointPath ]
  resetEndpointState = subprocess.Popen( cmdResetEndpoint, stdout=subprocess.PIPE ).communicate()[0].decode('utf-8', 'ignore')
  time.sleep(2)
  try:
    if resetEndpointState is None:
      print("No response from Endpoint.")
  except:
    print("Error handling Endpoint response.")  
 
  print("Reset Endpoint State:" + str(resetEndpointState))
  sendLogToOrch("info", "Reset Endpoint with State: " + str(resetEndpointState))

  time.sleep(2)
  cmd = [ 'sudo', 'systemctl', 'stop', 'iperfClient' ]
  iperfClientState = subprocess.Popen( cmd, stdout=subprocess.PIPE ).communicate()[0].decode('utf-8', 'ignore')
  cmd = [ 'sudo', 'systemctl', 'start', 'iperfClient' ]
  iperfClientState = subprocess.Popen( cmd, stdout=subprocess.PIPE ).communicate()[0].decode('utf-8', 'ignore')
  print("Started iperfClient service")

  cmd = [ 'sudo', 'systemctl', 'stop', 'latencyClient' ]
  latencyClientState = subprocess.Popen( cmd, stdout=subprocess.PIPE ).communicate()[0].decode('utf-8', 'ignore')
  cmd = [ 'sudo', 'systemctl', 'start', 'latencyClient' ]
  latencyClientState = subprocess.Popen( cmd, stdout=subprocess.PIPE ).communicate()[0].decode('utf-8', 'ignore')
  print("Started latencyClient service") 

  measurementsStartedAt = datetime.now()
  scheduler.resume_job('measurementTrigger')
  return json.dumps({"success": True}), 200

# StopMeasurements
@api.route('/stopMeasurements', methods=['post'])
def stopMeasurements():
  scheduler.pause_job(id="measurementTrigger")

  print("Stopped triggerMeasurement service")

  cmd = [ 'sudo', 'systemctl', 'stop', 'iperfClient' ]
  iperfClientState = subprocess.Popen( cmd, stdout=subprocess.PIPE ).communicate()[0].decode('utf-8', 'ignore')
  print("Stopped iperfClient service")

  cmd = [ 'sudo', 'systemctl', 'stop', 'latencyClient' ]
  latencyClientState = subprocess.Popen( cmd, stdout=subprocess.PIPE ).communicate()[0].decode('utf-8', 'ignore')
  print("Stopped latencyClient service") 


  return json.dumps({"success": True}), 200


# Trigger measurement - called periodically from inside this device
def triggerMeasurement():
  print("TriggerMeasurement!")
  datarate = lastDatarate
  latency = lastLatency
  # check if measurement values are outdated
  timeDeltaDatarateSecs = (datetime.now() - datetime.strptime(lastDatarateReceivedAt, '%Y-%m-%d %H:%M:%S.%f')).total_seconds()
  print("The data rate measurement is " + str(timeDeltaDatarateSecs) + " seconds old.")
  timeDeltaLatencySecs = (datetime.now() - datetime.strptime(lastLatencyReceivedAt, '%Y-%m-%d %H:%M:%S.%f')).total_seconds()
  print("The latency measurement is " + str(timeDeltaLatencySecs) + " seconds old.")

  if timeDeltaDatarateSecs > thresholdAgeOfMeasurement:
    datarate = -1
  if timeDeltaLatencySecs > thresholdAgeOfMeasurement:
    latency =  -1

  measurementData = McMeasurementPoint(myMac, datetime.now(), datarate, latency)
  measurementPointList.append(measurementData)
  print("There are " + str(len(measurementPointList)) + " measurement points in the output queue.")
  if (len(measurementPointList) > 0):
    if sendDataToOrchestrator():
      print("Sent data to orchestrator!")
      return json.dumps({"success": True}), 200
    else:
      return json.dumps({"success": False}), 400
  else: # measurementPointList is empty!
    print("No data to send!")
    return json.dumps({"success": False}), 400

def sendDataToOrchestrator():
  json_data=[]
  for mp in measurementPointList:
    currentRow = {
      "mcMac": mp.mcMac,
      "timestamp": json.dumps(mp.timestamp, indent=4, sort_keys=True, default=str),
      "datarate": mp.datarate,
      "latency": mp.latency
      }
    json_data.append(currentRow)

  try:
    res = requests.post(orchestratorPath, json=json_data, timeout=0.75)
    if res.status_code == 201:
      measurementPointList.clear() # clear list to avoid duplicate result transmission
      return True
    else:
      print("Error when sending data to orchestrator: Response code " + str(res.status_code))
      return False
  except:
    print("Error communicating with the Measurement Orchestrator - Is the Out-of-Band connection down?")


@scheduler.task('interval', id='measurementTrigger', seconds=1)
def measurementTrigger():
  timeDeltaSinceMeasurementsStarted = (datetime.now() - measurementsStartedAt).total_seconds()

  if timeDeltaSinceMeasurementsStarted < timeToWaitBeforeTriggering: # Measurements started recently - don't start triggering yet
    print("Trigger: Measurements started " + str(timeDeltaSinceMeasurementsStarted) + " seconds ago - waiting...")
    return
  print("Scheduler: Triggering Measurement")
  try:
    triggerMeasurement()
  except:
    print("Scheduler: Error")

if __name__ == '__main__':
    stopMeasurements() # Stop any running measurements at startup
    scheduler.init_app(api)
    scheduler.start()
    scheduler.pause_job(id='measurementTrigger')
    api.run(host="0.0.0.0", port="5010")
