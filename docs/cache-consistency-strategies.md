86.5% accuracy. ~$0.07 per session. See how Redis stacks up in the Agent Memory Benchmark.

[Read the report](https://redis.io/resources/agent-memory-benchmark-report/)

Resource Center

[Events & webinars](https://redis.io/events/) [Blog](https://redis.io/blog/) [Videos](https://redis.io/resources/videos/) [Glossary](https://redis.io/glossary/) [Resources](https://redis.io/resources/all/) [Architecture Diagrams](https://redis.io/resources/architecture-diagrams/) [Demo Center](https://redis.io/demo-center/)

Blog

[Events & webinars](https://redis.io/events/) [Videos](https://redis.io/resources/videos/) [Glossary](https://redis.io/glossary/) [Resources](https://redis.io/resources/all/) [Architecture Diagrams](https://redis.io/resources/architecture-diagrams/) [Demo Center](https://redis.io/demo-center/)

[Back to blog](https://redis.io/en/blog/)

Blog

# Cache consistency: strategies to keep data fresh

July 20, 202610 minute read

[Jeff Mills](https://redis.io/blog/author/jeff-mills/)

![Jeff Mills](https://cdn.sanity.io/images/sy1jschh/production/c64e2c85bdd4ae99067b098f9709653a3ad0a6e3-1280x1132.jpg?w=3840&q=80&fit=clip&auto=format)

Jeff Mills

Summarize with AI

- [Open prompt in ChatGPT](https://chatgpt.com/?q=Summarize%20this%20Redis%20blog%20post%3A%20%22Cache%20consistency%3A%20strategies%20to%20keep%20data%20fresh%22%20%E2%80%94%20https%3A%2F%2Fredis.io%2Fblog%2Fcache-consistency-strategies.md)
- [Open prompt in Claude](https://claude.ai/new?q=Search%20the%20web%20and%20answer%3A%20Summarize%20this%20Redis%20blog%20post%3A%20%22Cache%20consistency%3A%20strategies%20to%20keep%20data%20fresh%22%20%E2%80%94%20https%3A%2F%2Fredis.io%2Fblog%2Fcache-consistency-strategies.md)
- [Open prompt in Perplexity](https://www.perplexity.ai/search/new?q=Summarize%20this%20Redis%20blog%20post%3A%20%22Cache%20consistency%3A%20strategies%20to%20keep%20data%20fresh%22%20%E2%80%94%20https%3A%2F%2Fredis.io%2Fblog%2Fcache-consistency-strategies.md)

A cache that has drifted from your database will happily serve wrong prices, expired permissions, or phantom inventory, and it won't feel a shred of guilt about it. Cache consistency is the discipline behind keeping that drift small, so cached values don't wander away from the source database. The speed advantage of caching depends on knowing how far cached values can drift from the source data, then keeping that drift within the bounds your app can handle.

Caches sit in front of nearly every high-traffic system today, which means keeping them in sync with a source database is a question that comes up constantly. This guide covers what cache consistency means, why caches drift, how the classic patterns trade off, and how event-driven sync keeps data fresh when time-to-live (TTL) timers alone can't.

## What cache consistency means

A cache is consistent when its values match the source of truth, and every consistency strategy is really about shrinking the interval where the two disagree. That drift framing gives us the practical definition: stale cache entries appear whenever cached values fall out of step with the database behind them. Staleness isn't binary; it's a window. Every strategy in this article shrinks that window, bounds it, or decides which data deserves the tightest one.

How you propagate updates determines how consistent your reads are:

- Synchronous updates: propagate a change to every relevant node before readers see it, so clients are designed to see the same data once the update completes.
- Asynchronous updates: trade that guarantee for speed and land you in eventual consistency, where some nodes may temporarily serve stale data.

Most real systems sit somewhere on this spectrum, and picking your spot deliberately beats discovering it during an incident. Even hyperscalers treat this as a long-term engineering project: Meta improved TAO's cache consistency from six nines [to 10 nines](https://engineering.fb.com/2022/06/08/core-infra/cache-made-consistent) over years of dedicated invalidation work.

## Why caches drift: TTL timing, write ordering & instance races

Caches drift for three well-known reasons: TTL windows that outlast the data, write-ordering races between the cache and database, and multiple app instances stepping on each other during cache fills. The drift Meta spent years fighting comes from this same short list of mechanisms, and you'll likely recognize at least one from your own production history. The mechanics differ, but the result is the same: the cache keeps serving a value after the source of truth has moved on.

### TTL timing windows

In expiry-based caching patterns, each entry gets a TTL, a lifespan after which the entry counts as stale and gets removed or refreshed. But a cache relying on TTL alone serves stale data for the entire remaining window after the database changes. If your TTL is five minutes and the price changed ten seconds in, readers see the old price for four minutes and fifty seconds.

![Database](https://cdn.sanity.io/images/sy1jschh/production/bcfc53e71291d3d5d75ec30642114c4717c79133-64x64.svg)

## Get started with Redis for high-performance caching

Reduce latency and offload your database with in-memory caching.

[Try Redis](https://redis.io/try-free/)

The expiry mechanics themselves add wrinkles worth knowing, and Redis is a good concrete example because its behavior is well documented. Redis expires keys two ways: passively, when a client touches an already-expired key, and actively, through a background cycle that [samples 20 keys](https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency) every 100 milliseconds and reclaims the expired ones it finds, repeating whenever a sample turns up too many expired keys. That active pass keeps the count of expired-but-still-in-memory keys bounded instead of letting it grow. The lesson generalizes: no cache deletes keys the instant their TTL hits zero, so the "expired" window is always a little longer than the TTL suggests.

### Write-ordering races

TTL windows are at least predictable; races aren't. A race condition happens when two operations overlap in time and the outcome depends on which finishes first, which can leave the cache holding a value from the wrong moment. A stale set happens when [concurrent updates get reordered](https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final170_update.pdf), leaving the cache holding a value that doesn't reflect the latest write. A cache fill can interleave with a database transaction so the cache ends up with a mix of old and new data, and if the invalidation message then fails, nothing self-corrects until the next write or TTL expiry. The racing window for these interleavings is tiny, but at hyperscaler scale, with enormous query and cache-fill volumes, even rare races show up often enough to matter.

### Multi-instance population races

Horizontal scaling multiplies the racers. Picture two app instances: instance A deletes a cache entry and is about to update the database. Before A's write lands, instance B gets a cache miss, reads the old value from the database, and writes it back to the cache. A then commits. Now the database has the new value and the cache has the old one, with no invalidation coming to fix it.

Misses also pile up. A thundering herd happens when many requests miss simultaneously and hammer the database, each one racing to repopulate the same key with whatever snapshot it happened to read.

## Cache-aside vs. write-through: the classic trade-offs

These failure modes are why your caching pattern matters: each one draws the consistency line in a different place. That line determines whether writes wait, reads risk staleness, or your app carries more of the coordination work.

### Cache-aside (lazy loading)

In the cache-aside pattern, the app manages the cache directly. It loads data only on demand:

1. Check the cache: the app tries to read the item from the cache first.
2. Fall back to the database: on a miss, the app reads the item from the data store.
3. Populate and return: the app writes the item into the cache and returns it to the caller.

On writes, the app updates the database and then invalidates the cached entry so the next read repopulates it fresh. It's a flexible and common pattern, but the flexibility has costs. Cache-aside doesn't guarantee consistency: an external process can change the data store at any time, and the cache won't notice until the item reloads. The first request for uncached data pays the first-request latency penalty, running as slow as a normal database call. And the multi-instance races above are cache-aside's signature failure mode.

### Write-through

Write-through flips the write path: writes go to both the cache and database in the same synchronous operation, so readers typically see the new value after a successful write, assuming both writes complete. That buys you read-your-writes behavior, which matters a lot for data like balances and orders.

You pay for it three ways. Every write waits on two systems instead of one. A partial failure between the two writes leaves an inconsistency you have to resolve yourself. And everything written lands in the cache whether or not anyone ever reads it, which can waste memory on cold data. A freshly spun-up node also starts empty and stays that way until writes repopulate it. There's a third sibling worth knowing: write-behind, where writes hit the cache first and flush to the database asynchronously. It can offer faster writes, but it usually has weaker consistency, and a cache crash before flushing can lose data, so it fits write-heavy workloads with lower-risk data like analytics events and counters.

![Redis Cloud](https://cdn.sanity.io/images/sy1jschh/production/5f60e1427a8be962bb08ee8764c012b5e1f654f4-64x64.svg)

## Build faster with Redis Cloud

Get Redis up and running in minutes, then scale as you grow.

[Try for free](https://redis.io/try-free/)

## Event-driven sync closes the gap TTL can't

Neither classic pattern helps when data changes outside your app: a batch job, a database administrator (DBA) running a manual update, another service writing straight to the database. Event-driven invalidation reacts to the change itself instead of waiting for a timer.

### Keyspace notifications for cache-side changes

Redis ships a building block for this. [Keyspace notifications](https://redis.io/docs/latest/develop/pubsub/keyspace-notifications) let clients subscribe to publish/subscribe (pub/sub) channels and receive events when keys change, so one app instance can evict its local copy the moment another instance modifies a key. Pub/sub is fire and forget, though: a client that disconnects and reconnects misses every event in between, so consider adding a reconciliation path. Expired events also fire when Redis actually deletes the key, not the instant the TTL theoretically hits zero, so there can be a delay.

### Change data capture for database-side changes

For changes originating in your source database, change data capture (CDC) is the heavier-duty answer. Log-based CDC tools such as Debezium read the transaction log the database already maintains for replication, convert committed row changes into events, and let a consumer invalidate or refresh cache entries in near real time. Debezium provides [at-least-once delivery](https://debezium.io/documentation/faq/): it is designed so committed changes are not missed, but a record may arrive more than once, so consumers have to handle duplicates.

Uber's CacheFront shows both the power and the sweat involved. Its earlier design paired TTLs with CDC and hit read-your-writes problems, where a row that was read, cached, and then updated could keep serving [stale values until invalidated](https://www.infoq.com/news/2025/10/uber-cachefront-150m-reads) or expired. That kind of race shows why cache writes need freshness checks instead of accepting whichever value arrives last. Even then, the eventual consistency of TTL plus CDC became a limiting factor in some cases, so Uber layered on a write-through protocol where each node validates freshness with the database before serving. That system later saw a higher cache hit rate with longer TTLs.

Across these systems, event-driven signals often do most of the freshness work while TTL stays on as a safety net; the ordering, dedup, and replay logic is where the engineering hours go.

## Picking a strategy: write volume & staleness tolerance

You probably don't need Uber's three-mechanism setup. Start with how much staleness your data can handle and how write-heavy the workload is, then map to a pattern. As general guidelines, depending on your workload:

- Read-heavy with data that can handle staleness: cache-aside with TTL usually works. A product catalog that's a few seconds stale is invisible to shoppers.
- Read-your-writes required: write-through fits data where correctness is the point, like account balances and payments. Users tend to handle write latency better than read latency, so the double-write cost lands in the right place.
- Write-heavy with lower-risk data: write-behind absorbs write bursts for counters and event streams, in exchange for a data-loss window on cache failure.
- Data changes outside your app, or staleness costs money: add event-driven invalidation on top of whichever pattern you run, and keep a conservative TTL as the backstop for missed events.

These are starting points, not laws, and TTL length alone can shift a strategy from fine to harmful. A five-minute TTL that's harmless for a homepage would be rough on live inventory, so segment TTLs by how fast each type of data actually changes.

## Keep your cache fresh with Redis

The teams getting cache consistency right layer their mechanisms: a pattern that matches the workload, a TTL backstop, and an event-driven freshness signal. The hard part is deciding how much of that third layer your team wants to build and operate itself.

Building that third layer by hand means running CDC connectors, managing ordering and duplicates, and writing your own race-condition logic. Redis Data Integration (RDI) builds that layer for you. RDI is a [change data capture system](https://redis.io/docs/latest/operate/rdi) that tracks changes in a source database and applies them to Redis, first through a full snapshot, then by streaming changes as they happen. In supported RDI deployments, updates from your source database can reach the cache [within a few seconds](https://redis.io/docs/latest/operate/rc/rdi), depending on source load, connector configuration, and network conditions, which helps prevent stale data without custom pipeline code. You define how relational tables map into Redis hashes, JSON, or streams in configuration files. Delivery is [at-least-once](https://redis.io/docs/latest/integrate/redis-data-integration), and RDI preserves the change order per source table, so updates arrive in the sequence they happened. Supported sources include major relational and document databases, and RDI runs self-managed or fully managed in Redis Cloud on Amazon Web Services.

Redis is a fast, in-memory, real-time data platform that serves your cache reads and keeps them in agreement with your source of truth. [Try Redis free](https://redis.io/try-free/) to see RDI against your own database, or [talk to our team](https://redis.io/meeting/) about your caching architecture.

![Redis Insight](https://cdn.sanity.io/images/sy1jschh/production/93e4c98fa38c161f5c90ed4b8896f868f5241349-64x64.svg)
