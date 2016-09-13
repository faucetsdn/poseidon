This is a collector for Vent that gets installed automatically when this repository is installed as a plugin in Vent.

Once this collector is installed on Vent, it can be started as a passive collector through the start menu under the mode menu on Vent.

Once this collector is started, it can be interacted with through it's RESTful interface.  To find the port it's exposed on, you can go into the shell and search for it using docker commands.

Once you have the IP and port it's running on, you can make a POST request that looks like this:

```
http://192.168.99.100:32815/create
```

Along with a payload that looks like this:

```
{"nic":"eth1","id":"foo","interval":"300","filter":"","iters":"-1"}
```
for a continuously running filter, or like:
```
{"nic":"eth1","id":"foo","interval":"300","filter":"","iters":"1"}
```
for a filter to run `1` capture.

In the payload, the `nic` will be the network controller you want to capture on, the `id` can be any unique value, the `interval` is the time in seconds to cut up the captures into for processing, the `filter` is for limiting what gets captured off the network controller, if it's an empty string as in this example, there is no filter applied, and the `iters` is for specifying the number of captures to make (if this is 0 or less then the collector will run until killed, otherwise it will make this many captures).
