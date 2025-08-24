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

## Caching
This endpoint is using an in-memory cached with a 
timeout of 60s because the underlying data is not changing very often.
