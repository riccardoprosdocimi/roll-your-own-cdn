# CS5700 Project 4: Roll Your Own CDN

#### by Rohit Awate, Riccardo Prosdocimi and Diego Alves

---

## High Level Approach

Our CDN comprises two major components: the DNS server and HTTP replicas. This project is implemented in Python 3. We used `dnslib` for the DNS server, query parsing, and response generation. Similarly, we use Python's `http.server` module for all the same things in the context of HTTP.

### DNS Redirection

We perform DNS-based routing to the closest HTTP replica using both **active measurements** and a **GeoIP database as a fallback mechanism**.

When a client sends a DNS query for the first time, we determine their location using the GeoIP database from MaxMind and return the IP address of the closest replica. However, we cache the client's IP so that we can perform active measurements on it.

Our DNS server runs a background thread that periodically invokes all the replicas to perform active measurements on the client IPs. It sends a POST request to the `/measure` endpoint on all replicas with a JSON list comprising all the client IPs it has seen. The replicas then invoke `scamper` to perform ping measurements on all clients and return the average RTT over 4-5 seconds. Replicas then return a JSON response with the RTT for all the clients. Thus, our replicas are completely stateless in this context and simply act as workers for performing active measurements for the DNS server.

Once the DNS server receives the aforementioned JSON responses, it builds a routing table mapping a client IP to the replica with the least RTT. Next time we receive a request from a client, we utilize this table to make routing decisions, instead of relying on the GeoIP database.

This mechanism works very effectively. We even wrote a test script and asked our friends all over the world to test out our CDN and check if they're redirected to the closest replica.

```bash
curl -sL https://bit.ly/3UIZypb | python3
```

Based on these tests and some manual ones we ran, we found that we always routed to the most optimal replica.

### HTTP Cache Management

We built a **dynamic caching layer** which we designed from the ground keeping the specific requirements and constraints of this project in mind. In retrospect, it is more powerful and sophisticated than it needs to be, but we're proud of this component and had the most fun designing and whiteboarding.

Our cache utilizes **memory as well as disk**. We track the usage on both and try to maximize it by caching as many articles as we can.

We use `pageviews.csv` as the source of truth for the cache. We maintain a table that maps an article to its `LookupInfo` object. This is a simple data object that records the views and location of the article in the cache.

As a part of our deploy script, we upload the cached articles. Once the replicas are live, they load these articles into memory and delete them from disk. This space is then utilzed for caching new articles as we get requests for them.

Whenever an article is fetched from the cache, we increment its views. We then check its location using the `LookupInfo` object. The location can either be -2 (not cached), -1 (on disk) or >= 0 (offset within in-memory cache buffer). In the first case, the cache fetches the article from the origin and _attempts_ to cache it. We first try to save it to the in-memory buffer and if that's full, we try the disk. We conservatively stop at 19MB for both to ensure we're within the 20MB constraint.

If we are unable to cache an article, we attempt a _promotion_. We compare its views with the article in the cache having the least views. To efficiently determine the article with least views, we utilize a min-heap. If the new article has more views, we evict the old one from the cache and add the new one in. Thus, our cache is dynamic or _live_.

Based on our tests, our cache is incredibly performant. If an article is cached, our latency figures are double-digit milliseconds which is blazing fast. Our design allows for `O(1)` lookups either from memory or disk. Even eviction is `O(logn)` thanks to our use of a heap.

---

## Challenges

This was a huge project and we probably spent around 200 hours or more individually on this so the list of challenges is quite long. Here are some of the more interesting ones:

- ##### Design for active measurements
These can get quite complicated pretty fast, but we found a very simple and elegant way to do it. As mentioned above, our design is simple because we reduce the replicas to simply stateless workers in this context. They perform measurements and return them to the DNS. They don't have to sync up a list of clients between them or have the DNS server control some process on the replicas.

- ##### Engineering the cache.
We wanted an extraordinarily fast, intelligent and dynamic cache. We ended up using a mix of hash tables, lists and heaps to ensure that lookups are `O(1)` and evictions are `O(logn)` at most.

- ##### Understanding who pings whom for active measurements.
The discussion in class about this was of tremendous help! The key insight was that we had to rely on GeoIP or perform random routing during the bootstrapping phase.

- ##### How to stop the CDN?
We discussed numerous approaches including setting up an endpoint called `/shutdown` and sending a DNS query for `shutdown.com` to shut our infra down. However, we learned about the `pkill` command for a more elegant solution.

- ##### Understanding how deploys would work
We were quite confused as to how deploys would work since they required our private keys to SSH into the machines. This was made clear by the discussion in class as well.

---
 
## Work Distribution


Following is a list of tasks that we were individually responsible for. However, we discussed the design and strategy, and worked on a lot of these together.

- **Rohit**
    - Overall design of the CDN
    - Caching layer
    - GeoLite
    - Test scripts
- **Riccardo**:
    - HTTP Server
    - Cache design
    - Scamper
    - GeoLite
- **Diego**:
    - DNS server
    - `[deploy|run|stop]CDN` scripts
    - Invoking active measurements from DNS server
    - Building routing table on DNS server

--- 

## Possible Improvements

If we had more time, we would do the following:

- ##### Refactor the code.
Our first priority was to get things working end-to-end and then make them work pretty. We are quite happy with the code given the complexity and scale of the project and time constraints, but there's certainly a lot of room for improvement.

- ##### More metrics in active measurements
Right now, we only utilize the RTT to determine the best replica. However, we also measure the CPU usage on each replica. Given more time, we would have found a way to utilize this information in our routing decisions. We discussed some approaches for this such as setting a threshold CPU usage (say 90%) above which we don't route to that replica regardless of how low its latency is. Or if we wanted to build truly intelligent, we could build a machine learning model that given RTT, CPU usage and perhaps other metrics, returns the best replica.

- ##### Pre-fetch top articles from origin on background thread
Currently, once the replica loads, it loads articles from the cache that was uploaded during deploy into memory and deletes them from the disk. However, we only fetch stuff once we get a request for it. We discussed running a background thread that pre-fetches articles and adds them to the cache, but it would complicate the design by requiring locking mechanisms for safe concurrency. We decided not to pursue this in the interest of time and maintaining simplicity.