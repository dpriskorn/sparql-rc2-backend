# sparql-rc2-backend
OpenAPI specification https://sparql-rc2-backend.toolforge.org/docs

## Features
This backend provides a /revisions endpoint with the following capabilities:
* Fetches revisions for multiple entities within a specified timeframe.
* Returns the earliest and latest revision for each entity.
* Reports the total number of unique users who edited each entity.
* Details the number of edits made by each user.
* Includes page IDs, user IDs, entity IDs, and usernames in the response.

This endpoint offers consumers a fast and comprehensive overview of edits 
across many entities. 
It supports contributors and data consumers in tracking 
changes to entities of interest, playing a crucial role 
in maintaining data quality and consistency.

## Deployment
First stop, build and then start
* `$ toolforge webservice buildservice stop`
* `$ toolforge build start --use-latest-versions https://github.com/dpriskorn/sparql-rc2-backend.git`
* `$ toolforge webservice buildservice restart --mount=none`

Debug using
* `$ webservice logs -f` 
