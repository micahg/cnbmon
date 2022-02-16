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

## Plotting Output

Run GNU Plot, then something like:

```
gnuplot> set timefmt "%Y-%m-%d %H:%M:%S"
gnuplot> set datafile separator ","
gnuplot> plot "dn_11_615000000_256QAM.dat" using 2:3 title "LSKJ" with lines
```

or, equivalently,

```
gnuplot -e "set term svg;set output 'plot.svg';set timefmt '%Y-%m-%d %H:%M:%S';set datafile separator ',';plot 'dn_11_615000000_256QAM.dat' using 2 title 'Downstream Channel 11 Power' with lines;plot 'dn_11_615000000_256QAM.dat' using 3 title 'Downstream Channel 11 SNR' with lines"
```
``````
gnuplot -e "set term svg;set output 'plot.svg';set timefmt '%Y-%m-%d %H:%M:%S';set datafile separator ',';set xdata time;set format x '%Y-%m-%d %H:%M';set xtics rotate;plot 'dn_11_615000000_256QAM.dat' using 1:2 title 'Downstream Channel 11 Power' with lines"
```