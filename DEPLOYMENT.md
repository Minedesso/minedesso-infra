# Automatic Minecraft deployment

## Flow

Each of the four plugin repositories runs Maven verification on pushes and pull
requests. Only a successful push to `main` sends `plugin-updated` to this
repository (a merged pull request also produces that push).

The infrastructure workflow checks out all four plugins from their current
`main`, verifies them, builds all three Minecraft images, and publishes unique
`run-<run-id>-<attempt>` tags. The `plugin-revisions` artifact records the four
source SHAs in ban, lobby, essential, islewars order. The deploy job only starts
after all images have been published successfully. PR and development builds
never deploy. Manual runs on `main` can retry a deployment.

All three Minecraft servers restart on a plugin update, including shared ban
plugin updates. Rebuilding the complete set means a pending run superseded by
another update still includes all current plugin changes. Running workflows
are not cancelled. Images use unique run tags because the infrastructure commit
SHA does not change when a plugin changes.

The VPS pulls images only; it does not build application source. Existing worlds,
plugin settings and other volume data persist. Only matching Minedesso plugin
JARs in the top-level plugin directory are removed before synchronization.

## GitHub configuration

1. Merge the infrastructure workflow into the default branch, which must be
   `main`, before enabling the plugin senders. GitHub dispatch events use the
   workflow on the default branch.
2. In each plugin repository set the Actions secret `INFRA_DISPATCH_TOKEN`.
   Use a fine-grained PAT scoped only to `Minedesso/minedesso-infra`, with
   **Contents: Read and write** (required by the dispatch endpoint). The normal
   repository `GITHUB_TOKEN` does not have cross-repository access.
3. In this repository create the `production` environment and add secrets:
   - `DEPLOY_HOST`: VPS hostname, SSH port 22.
   - `DEPLOY_USER`: `mc-deploy`.
   - `DEPLOY_SSH_KEY`: private key for that account's forced command.
   - `DEPLOY_KNOWN_HOSTS`: verified SSH host key entry; obtain and verify it
     through a trusted administrator connection, not blindly during CI.
4. Permit production deployments from `main`. Configure reviewers only if
   manual approval is desired for every deployment.

The existing plugin clone URLs assume public repositories. Private plugins need
an additional read-only credential for cloning in the infrastructure workflow.
Do not enable deployment until those builds succeed.

## VPS preparation (administrator, once)

Use Docker Compose >= 2.20 and a working stack at `/opt/minecraft-dev`.
Install the reviewed infrastructure files there before the first automated run.
The deploy key must not be able to edit this directory, its Compose files,
`.env`, scripts or configuration. Those files and the deployment scripts must
be root-owned and not group/world-writable.

Create `mc-deploy` with a locked password, a Bash login shell and no Docker group
membership. Install the scripts as administrator from the reviewed checkout:

```bash
sudo install -o root -g root -m 0755 scripts/deploy-minecraft /usr/local/bin/deploy-minecraft
sudo install -o root -g root -m 0755 scripts/minecraft-ssh /usr/local/bin/minecraft-ssh
```

Install this rule using `visudo -f /etc/sudoers.d/minecraft-deploy`:

```text
mc-deploy ALL=(root) NOPASSWD: /usr/local/bin/deploy-minecraft
```

Add the CI public key to `mc-deploy`'s `authorized_keys` with this prefix:

```text
restrict,command="/usr/local/bin/minecraft-ssh" ssh-ed25519 <CI-public-key>
```

Protect the account's `.ssh` directory (0700) and `authorized_keys` (0600).
The forced command validates the complete request without evaluating shell text;
the privileged script independently accepts only a numeric workflow run tag.
The account has neither an unrestricted shell via this key nor general sudo.

For private GHCR images, log Docker in as root using a read-only package token.
CI only needs the deployment SSH key; it does not transmit registry credentials.

## Versions, failure and rollback

The script serializes remote deployments with `flock`, pulls all three images
before restarting any server, allows two minutes for graceful shutdown, then
waits up to five minutes for healthy Minecraft containers.

After success it stores the selected tags in `.minecraft-images.env` (ignored by
Git). Use `sudo bash scripts/deploy.sh` for later whole-stack deployments so this
override is preserved. A plain `docker compose up` reads only `.env` and can
revert the selected Minecraft versions.

A pull failure leaves the running servers untouched. A startup/health failure
fails the workflow and does not save the new tags; some containers may already
have changed. There is no automatic world rollback. Inspect logs, then redeploy
a known good retained run tag as administrator:

```bash
sudo /usr/local/bin/deploy-minecraft run-123456789-1
```

Keep prior GHCR run tags available for rollback. Back up worlds before activating
this rollout, and smoke-test a plugin change through `main` on the target VPS.

## Existing stack considerations

- PostgreSQL currently uses the single `postgres` login for the APIs and
  Keycloak, so all three use `POSTGRES_PASSWORD`. Separate passwords require
  creating separate database roles first. Initialization scripts only run on an
  empty database volume; verify `minedesso`, `islewars` and `keycloak` exist on
  existing installations. Do not delete existing volumes to rerun initialization.
- Copy the generated Velocity forwarding secret into the matching `.env` value.
- IsleWars API currently contains only the application scaffold. Its business
  endpoints, authentication and database migrations need implementation before
  the IsleWars plugin can use them; CI/CD alone does not provide those endpoints.
- Deployment healthchecks establish container readiness, not that every plugin
  enabled successfully. Check Minecraft logs and perform an in-game smoke test.

## References

- [GitHub workflow events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
- [Docker Actions cache](https://docs.docker.com/build/cache/backends/gha/)
- [Minecraft plugin synchronization](https://docker-minecraft-server.readthedocs.io/en/latest/mods-and-plugins/)
- [Keycloak container health](https://www.keycloak.org/server/containers)
