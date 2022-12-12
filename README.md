# CS5700-Project-4

## High Level

### DNS Server

The DNS resolver takes a name from the client, checks that the name is within jurisdiction, and gets a replica IP address. The aux library dnslib has been used to facilitate implementation of main functionality.

### HTTP Replica Server

Each replica runs an http server to process client requests. It uses a page views csv file to determine caching priorities. When serving content to the client, if the content has not yet been cached to memory, it serves the content directly from the origin.

The server also has a measurements endpoint, which the DNS resolver uses to get active measurements from all replicas.

## Challenges

The following are key challenges we faced, and how they were addressed:

- 1.  Serving best replica to client: We want to deliver the best replica to a client without slowing down performance. If we were to ping different replicas from the resolver to determine the best RTT when a client first connects to the resolver, the outcome would be slow performance. As a result, the best approach at first is to serve the closest replica to the client. Then, the DNS resolver can ping replicas in the background to determine the best replica to server to a given client on any subsequent client requests once the initial TTL expires.

## Work Distribution

Together, we all strategized and contributed to all parts, with each person spending a bit more time developing the following:

- Diego: worked on deploy/run/stop scripts
- Ricardo: worked on http server
- Rohit: worked on dns server
