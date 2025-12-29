# 🧠 DoorDash-Driver Tool Server

A plug-and-play server for the DoorDash-Driver API using FastAPI.  

## 🚀 Quickstart

Clone the repo, set up the .env vars and start the Server

```bash
git clone https://github.com/entitycs/doordash-driver-fastapi
docker compose up
```

That's it – you're live! 🟢

Default port: 8099 - modify it in compose.yaml

[detail]
# Recent Updates
Added minimal postgreSQL database implementation

# Required Config

See config module sample.env files for environment variable settings
| <h2>Config Type</h2> | <h2>Defines</h2> |
|--------------------|--------------------|
| <h3>🔩 **Internal Config**</h3> <br/> Developer Client (aka business) information | <h3> <br/> - [x]  Developer ID <br/> - [x] Key ID<br/> - [x] Signing Secret</h3>|
| <h3>🏪**Merchant Config**</h3> <br/> Company + Store Information| <h3><br/>  - [x] Pickup External Business ID<br/>  - [x] Pickup External Store ID<br/>  - [x] Pickup Address<br/>  - [x] Pickup Phone Number </h3> |

# Constraints

Soft limits can be expanded through app updates.  

- 25 Stores (soft limit)
- todo:

```mermaid
---
config:
  kanban:
    ticketBaseUrl: 'https://mermaidchart.atlassian.net/browse/#TICKET#'
---
kanban
  Todo
    [Create Documentation]
    id7[implement local throttling]
    id12[full coverage db logging for deliveries | success + error]
    id13[todo - event looping w/ retry]
  [In progress]
    id6[Create test for all endpoints]
    id11[Design base 'Event' logging via postgre db]
  id11[Done]
    id5[test createQuote, listStores via Agent tool calling]
    id2[setup environment variable configs for merchant and delivery - required + optional]
    id3[test build, run service]
    id9[Create postgresql local + docker environments, volumes]
    id8[Tie in postgresql db - delivery_id logic first]
    id10[Test admin tooling on port 8011 - see Adminer service]
```
https://pruritic-wendi-aerobiotically.ngrok-free.dev/docs
