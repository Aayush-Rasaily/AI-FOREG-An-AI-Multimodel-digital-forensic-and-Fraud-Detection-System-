# Deployment

The root `docker-compose.yml` is a local-development composition, not a
production deployment. It provides a repeatable developer stack for the API,
worker, PostgreSQL, Redis, and RabbitMQ.

Before production deployment, provide environment-specific manifests or
infrastructure-as-code for the target platform. Those artifacts must define
secrets, identity, network isolation, TLS, autoscaling, persistent storage,
health probes, migration execution, backups, observability, and disaster
recovery.

The API and worker are intentionally built from the same image but should be
scaled and released independently. Database migrations must run as a
single-controlled deployment step.
