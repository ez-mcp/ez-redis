{"categories":\["docs","develop","stack","oss","rs","rc"\],"description":"Cache database reads in Redis with TTL-bounded staleness.","duplicateOf":"head:data-ai-metadata","location":"body","title":"Redis cache-aside","tableOfContents":{"sections":\[{"id":"when-to-use-redis-cache-aside","title":"When to use Redis cache-aside"},{"id":"why-the-problem-is-hard","title":"Why the problem is hard"},{"id":"what-you-can-expect-from-a-redis-solution","title":"What you can expect from a Redis solution"},{"id":"how-redis-supports-the-solution","title":"How Redis supports the solution"},{"id":"ecosystem","title":"Ecosystem"},{"id":"code-examples-to-build-your-own-redis-cache-aside","title":"Code examples to build your own Redis cache-aside"}\]},"codeExamples":\[\]}

# Redis cache-aside

Cache database reads in Redis with TTL-bounded staleness.

## When to use Redis cache-aside  [Copy link to clipboard](https://redis.io/docs/latest/develop/use-cases/cache-aside/\#when-to-use-redis-cache-aside "Copy link to clipboard")

Use Redis cache-aside when you need to serve repeated reads at sub-millisecond latency without overloading your primary database, caching only the data that is actually requested.

## Why the problem is hard  [Copy link to clipboard](https://redis.io/docs/latest/develop/use-cases/cache-aside/\#why-the-problem-is-hard "Copy link to clipboard")

Read-heavy workloads (product catalogs, user profiles, API responses) hit the same records thousands of times between updates. Primary databases optimized for durability pay the full cost of a disk-based lookup on every request; as traffic grows, P95 latency degrades, connection pools exhaust, and brief spikes cascade into broader service degradation.

An in-process cache solves this for a single instance but breaks across multiple stateless services: each instance warms independently, duplicates memory, and cannot be invalidated consistently. When a popular cached key expires under high concurrency, dozens of processes simultaneously query the database for the same record — a cache stampede that amplifies the exact load spike caching was supposed to prevent.

This use case is distinct from write-through or write-behind caching, where the cache mirrors the full dataset on every write. It is also distinct from semantic caching, which matches LLM responses by embedding similarity rather than exact key lookup.

## What you can expect from a Redis solution  [Copy link to clipboard](https://redis.io/docs/latest/develop/use-cases/cache-aside/\#what-you-can-expect-from-a-redis-solution "Copy link to clipboard")

You can:

- Keep P95 read latency under 5 ms for cached entities at peak traffic.
- Reduce primary database load proportionally to hit rate without provisioning read replicas.
- Cache only actively requested data, keeping memory bounded to the working set.
- Invalidate on write so stale data windows stay within a configured bound.
- Survive popular-key expiration under load without stampeding the database.
- Update individual fields in a cached entity without deserializing and rewriting the full object.

## How Redis supports the solution  [Copy link to clipboard](https://redis.io/docs/latest/develop/use-cases/cache-aside/\#how-redis-supports-the-solution "Copy link to clipboard")

In practice, each cached entity is stored under a key like `cache:{entity}:{id}`, with a TTL that bounds how long stale data can be served. The application reads from Redis on every request, falls back to the primary on a miss, and writes the result back to Redis. On updates, the application writes the primary and invalidates the cache key.

Redis provides the following features that make it a good fit for cache-aside:

- [`GET`](https://redis.io/docs/latest/commands/get/) and
[`SET`](https://redis.io/docs/latest/commands/set/) with per-key
[`EX`/`PX`](https://redis.io/docs/latest/commands/set/) TTL so every entry has a bounded
staleness window, and [`DEL`](https://redis.io/docs/latest/commands/del/) on write for explicit
invalidation — keeping stale data confined to a known, configurable bound.
- [Hashes](https://redis.io/docs/latest/develop/data-types/hashes/)
( [`HSET`](https://redis.io/docs/latest/commands/hset/),
[`HGET`](https://redis.io/docs/latest/commands/hget/)) and native
[JSON](https://redis.io/docs/latest/develop/data-types/json/) path access
( [`JSON.SET`](https://redis.io/docs/latest/commands/json.set/),
[`JSON.GET`](https://redis.io/docs/latest/commands/json.get/)) for structured and
partial-field caching, avoiding full-object re-serialization on every read or update — a real
gap in string-only stores like Memcached.
- [Lua scripting](https://redis.io/docs/latest/develop/programmability/eval-intro/) with
[`EVAL`](https://redis.io/docs/latest/commands/eval/) for atomic stampede mitigation: mutex locks
or probabilistic early refresh execute in a single atomic step with no external locking.
- [`TTL`](https://redis.io/docs/latest/commands/ttl/) for monitoring remaining staleness on any cached
key without recomputing.
- Sub-millisecond reads from memory, so the cache check adds negligible overhead on the
request path. If Redis is already in the stack for sessions, rate limiting, or queues,
cache-aside runs on the same instance at zero marginal infrastructure cost.

## Ecosystem  [Copy link to clipboard](https://redis.io/docs/latest/develop/use-cases/cache-aside/\#ecosystem "Copy link to clipboard")

The following libraries and frameworks provide Redis-backed cache-aside integrations:

- **Java**:
[Spring Data Redis (`@Cacheable`/`@CacheEvict`)](https://docs.spring.io/spring-data/redis/reference/redis/redis-cache.html),
[Redis Smart Cache](https://github.com/redis-field-engineering/redis-smart-cache)
(transparent JDBC-layer cache-aside)
- **Python**: [Flask-Caching](https://flask-caching.readthedocs.io/)
(Redis backend),
[Django cache framework](https://docs.djangoproject.com/en/stable/topics/cache/)
(with [redis-py](https://redis.readthedocs.io/))
- **Node.js**: [node-redis](https://github.com/redis/node-redis),
[ioredis](https://github.com/redis/ioredis) (wrap route handlers with a cache-aside helper)
- **API gateways**:
[Kong Redis response caching](https://docs.konghq.com/hub/kong-inc/proxy-cache-advanced/)
(configurable TTL per route)

## Code examples to build your own Redis cache-aside  [Copy link to clipboard](https://redis.io/docs/latest/develop/use-cases/cache-aside/\#code-examples-to-build-your-own-redis-cache-aside "Copy link to clipboard")

The following guides show how to build a simple Redis-backed cache-aside layer in front
of a slow primary store. Each guide includes a runnable interactive demo for each of the
following client libraries:

- [redis-py (Python)](https://redis.io/docs/latest/develop/use-cases/cache-aside/redis-py/)
- [node-redis (Node.js)](https://redis.io/docs/latest/develop/use-cases/cache-aside/nodejs/)
- [go-redis (Go)](https://redis.io/docs/latest/develop/use-cases/cache-aside/go/)
- [Jedis (Java)](https://redis.io/docs/latest/develop/use-cases/cache-aside/java-jedis/)
- [Lettuce (Java)](https://redis.io/docs/latest/develop/use-cases/cache-aside/java-lettuce/)
- [StackExchange.Redis (C#)](https://redis.io/docs/latest/develop/use-cases/cache-aside/dotnet/)
- [Predis (PHP)](https://redis.io/docs/latest/develop/use-cases/cache-aside/php/)
- [redis-rb (Ruby)](https://redis.io/docs/latest/develop/use-cases/cache-aside/ruby/)
- [redis-rs (Rust)](https://redis.io/docs/latest/develop/use-cases/cache-aside/rust/)
