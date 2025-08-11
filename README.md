# sparql-rc2-backend
OpenAPI specification https://sparql-rc2-backend.toolforge.org/docs
## Deployment
First stop, build and then start
* `$ toolforge webservice buildservice stop`
* `$ toolforge build start --use-latest-versions https://github.com/dpriskorn/sparql-rc2-backend.git`
* `$ toolforge webservice buildservice start --mount=none`

Debug using
* `$ webservice logs` 
