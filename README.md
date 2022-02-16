# cnbmon
cnbmon is a tool to track latency of the router and the gateway and then when a
problem is detected (packet loss) pull modem stats for comparison.

Thats the plan anyway.

## Running

You can run like so:

```python cnbmon.py -u USERNAME -p PASSWORD -m http://localhost:8080 -o output```

This will login in to the modem using USERNAME and PASSWORD, discover the local
gateway (eg: your router) and the external gateway (eg: the first hop outside your)
lan, and start recording:

* Modem stats for each upstream and downstream channel
* Latency to the internal gateway (not done yet)
* Latency to the external gateway (not done yet)

