- add endpoint to http server which reports the current CPU usage
- save log file on the server instead of the local machine
- heapq to 

maxmind username: shutupandletrohitin@gmail.com
maxmind password: cs5700p4123


DONE:
- ask professor how to do active measurements without having access to clients
    - WHAT to ping from the HTTP servers?

TO ASK:
- Can we assume client is capable of accepting a gzip compressed file using the Content-Encoding: gzip header?
- How long can the deploy stage take? We want to pre-cache top pages beforehand on disk and load them at runtime.
- This should take a minute or two during the deploy stage. Is that acceptable?

Add another layer of indirection by not using article names anywhere internally within the cache. Have a dictionary
at the entry which maps a string to an int or something which is lighter to duplicate within a LookupInfo object

How to test this out?
- easy to test: uncached and in-memory cache
- moderately hard to test: on disk cache
    - first request will lead to uncached, which gets cached to disk
    - subsequent requests should be served from disk
- hard to test: promotion
    - setup a test example
    - 