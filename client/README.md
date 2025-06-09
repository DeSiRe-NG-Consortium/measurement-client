# Overview Measurement Client (MC)

The Measurement Client features an own internal API. This API is used by the Measurement Orchestrator to start and stop measurements and to set parameters.

There is no manual configuration required for the Measurement Client. However, if you want to use 5G as a measurement technology, please read the next section.

# 5G Setup
The setup to use a connected smartphone as USB-tethered modem is done automatically on startup. However, in certain situations (smartphone had turned off USB tethering after boot of the Measurement Client, loss of connection, ...) it might be necessary to repeat the setup by running the following:

./setup5GNS.sh

You can run commands over the 5G connection as follows:

sudo ip netns exec 5gns ping 192.168.100.100


## Measurement Client Services
There are two measurement services, iperfClient.service and latencyClient.service. These are NOT enabled and need to be started by the API, see next section.
The purpose of these services is to start the corresponding measurements and parse the results in real-time.
After start, the services collect the measurement endpoint IP from the internal API.
The results are inserted into the internal API to allow for asynchronous operation.

### Setup

From the `measurement-client/client` subdirectory, run:

```
sudo bash setup
```


