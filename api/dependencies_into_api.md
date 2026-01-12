# ✏️ How Dependencies Work In Ts App

Statful vs Stateless Dependencies

- Workout what's a database connection pool, long lived vs just a http wrapper that you can spin up every time

## Dependencies That Are Long Lived

1) Vector Database (Opens a conn pool)
2) Redis (Opens a conn pool)
3) Supabase Auth
4) LLM Connections
5) Embed Connections

## Dependencies That Are Wrappers
1) Shopify Store
3) Scraper


Dependency | long or short | Reason | Notes
Vector Database | long lived | long lived | vars: grpc_pool & pool size, opening a conn pool
Redis | long lived | vars: connection_pool, keepalive
Supabase Auth | long lived | Yet to implement
LLM Connections | long lived | vars: httpx client | Could be subject to change if tests are run regarding different LLMS & performance benchmarks
Embed Connections | long lived | vars: httpx client
Shopify Store | short lived | vars: https protocol, no connection
