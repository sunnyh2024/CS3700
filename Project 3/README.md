The high level approach of this router stores routes in a dictionary, where the keys are the source ips and the values are a list of all the routes from that ip. Sending packets is based off of this design, using the template given to us, we first find valid routes with the given dest address. Based on these routes, we then find the best route possible with certain conditions, then use this route to forward the packet, update the routing table, and dump said table. In addition, everytime the table is dumped, the table that is dumped is only then aggregated so that when an ip is revoked, we wouldn't need to deaggregate. 

The biggest challenge that we faced was designing the aggregation functions as debugging this function was really difficult and took a long time. In addition the general structure of our routes was difficult to design as we wanted a structure that would be easy to get the information we wanted. For that reason, it took a long time to get our current route storage of a dictionary of lists of dictionaries. 

In order to test our code, we ran the sim with all the given test cases in the Khoury Linux Server, and used the error messages as well as print st to debug.