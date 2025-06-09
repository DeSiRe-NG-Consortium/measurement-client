import subprocess
from datetime import datetime
import requests
import requests

def postDatarate(datarate):
  jsonToSend = {"datarate" : datarate, "timestamp" : str(datetime.now())}
  print("Sending to orchestrator: " + str(jsonToSend))
  res = requests.post('http://127.0.0.1:5010/datarate', json=jsonToSend)

### Get configuration from local API

headers = {'Accept': 'application/json'}

r = requests.get('http://127.0.0.1:5010/endpointIP', headers=headers)
endpointIpJSON = r.json()
endpointIP = endpointIpJSON[0]['endpointIP']

r = requests.get('http://127.0.0.1:5010/measurementNetworkNamespace', headers=headers)
measurementNetworkNamespaceJSON = r.json()
measurementNetworkNamespace = measurementNetworkNamespaceJSON[0]['measurementNetworkNamespace']

r = requests.get('http://127.0.0.1:5010/udpSpeed', headers=headers)
udpSpeedJSON = r.json()
udpSpeed = udpSpeedJSON[0]['udpSpeed']

r = requests.get('http://127.0.0.1:5010/mode', headers=headers)
modeJSON = r.json()
mode = modeJSON[0]['mode']

r = requests.get('http://127.0.0.1:5010/mPay', headers=headers)
mPayJSON = r.json()
mPay = 1460
iperfPort = '5201'

r = requests.get('http://127.0.0.1:5010/technology', headers=headers)
technologyJSON = r.json()
technology = technologyJSON[0]['technology']

### Configuration of the used technologies. Adapt this to your needs when adding/ modifying a technology you want to use for measurements.

if mode == "REVERSE":
  cmdIperf_5G = [ 'sudo', 'ip', 'netns', 'exec', '5gns', 'iperf3', '-c', endpointIP, '-u', '-b', udpSpeed, '-R', '-p', iperfPort, '-t', '3600', '--forceflush' ]
else:
  cmdIperf_5G = [ 'sudo', 'ip', 'netns', 'exec', '5gns', 'iperf3', '-c', endpointIP, '-u', '-b', udpSpeed, '-p', iperfPort, '-t', '3600', '--forceflush' ]

if mode == "REVERSE":
  cmdIperf_WIFI = [ 'iperf3', '-c', endpointIP, '-u', '-b', udpSpeed, '-R', '-p', iperfPort, '-t', '3600', '--forceflush' ]
else:
  cmdIperf_WIFI = [ 'iperf3', '-c', endpointIP, '-u', '-b', udpSpeed, '-p', iperfPort, '-t', '3600', '--forceflush' ]

if mode == "REVERSE":
  cmdIperf_ETHERNET = [ 'iperf3', '-c', endpointIP, '-u', '-b', udpSpeed, '-R', '-p', iperfPort, '-t', '3600', '--forceflush' ]
else:
  cmdIperf_ETHERNET = [ 'iperf3', '-c', endpointIP, '-u', '-b', udpSpeed, '-p', iperfPort, '-t', '3600', '--forceflush' ]

if technology == "5G":
  cmdIperf = cmdIperf_5G
elif technology == "WIFI":
  cmdIperf = cmdIperf_WIFI
elif technology == "ETHERNET":
  cmdIperf = cmdIperf_ETHERNET
else:
  print("Error: Unknown technology: " + technology)

print("Using technology: " + technology + " with command " + str(cmdIperf))

with subprocess.Popen(cmdIperf, stdout=subprocess.PIPE) as p:
  while True:
    while p.poll() is None:
        text = p.stdout.read1().decode("utf-8")
        onlySingleSpaces=" ".join(text.split())
        listOfWords=onlySingleSpaces.split(' ')
        datarate=-1
        indexInListOfWords = 0
        while indexInListOfWords < len(listOfWords) and datarate == -1:
          try:
            if listOfWords[indexInListOfWords]=="Mbits/sec":
              datarate=float(listOfWords[indexInListOfWords-1])
              print("Found datarate: " + str(datarate))
              postDatarate(datarate)
            elif listOfWords[indexInListOfWords]=="Gbits/sec":
              datarate=float(listOfWords[indexInListOfWords-1])*1000
              postDatarate(datarate)
            elif listOfWords[indexInListOfWords]=="bits/sec":
              datarate=0
              postDatarate(datarate)
          except:
            print("ERROR while parsing iperf3 output!")

          indexInListOfWords = indexInListOfWords + 1
