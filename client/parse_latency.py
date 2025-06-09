import subprocess
from datetime import datetime
import requests

import requests

headers = {'Accept': 'application/json'}

r = requests.get('http://127.0.0.1:5010/endpointIP', headers=headers)

endpointIpJSON = r.json()
endpointIP = endpointIpJSON[0]['endpointIP']

r = requests.get('http://127.0.0.1:5010/technology', headers=headers)
technologyJSON = r.json()
technology = technologyJSON[0]['technology']

r = requests.get('http://127.0.0.1:5010/measurementNetworkNamespace', headers=headers)
measurementNetworkNamespaceJSON = r.json()
measurementNetworkNamespace = measurementNetworkNamespaceJSON[0]['measurementNetworkNamespace']

cmdPing_5G = [ 'sudo', 'ip', 'netns', 'exec', '5gns', 'ping', endpointIP ]
cmdPing_WIFI = [ 'ping', endpointIP ]

if technology == "5G":
  cmdPing = cmdPing_5G
elif technology == "WIFI":
  cmdPing = cmdPing_WIFI
else:
  print("Error: Unknown technology: " + technology)

print("Using technology: " + technology + " with command " + str(cmdPing))

with subprocess.Popen(cmdPing, stdout=subprocess.PIPE) as p:
    while p.poll() is None:
        text = p.stdout.read1().decode("utf-8")
        try:
          listOfWords=text.split('=')
          latency=listOfWords[3].split(' ')[0]
          res = requests.post('http://127.0.0.1:5010/latency', json={"latency" : latency, "timestamp" : str(datetime.now())})
        except:
           print("Error parsing latency.")
           pass
