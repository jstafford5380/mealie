# Aspire local development

Install Node.js 24 or later and [Aspire CLI](https://aspire.dev/get-started/install-cli/) 13.6.5 or later.
Start Docker Desktop or a Docker-compatible container runtime.
The TypeScript AppHost does not require the .NET SDK.
The containers provide Python, uv, pnpm, and the application dependencies.

From the repository root, run:

```sh
npm run dev:aspire
```

The first run builds the application images and downloads dependencies.
Later runs use the Docker build cache.
The command starts these services:

| Service | Purpose |
| --- | --- |
| frontend | Nuxt development server with hot reload |
| backend | FastAPI development server with hot reload |
| postgres | PostgreSQL 15 with automatic database setup and migrations |
| mailpit | Local SMTP server and email inbox |

Open the dashboard URL from the command output.
Select the frontend HTTP URL to open Mealie.
Aspire assigns available ports to the services.
The frontend sends API requests through its Nuxt proxy.
The dashboard shows service health and console logs.

Use the default account for a new database:

- Email: `changeme@example.com`
- Password: `MyPassword`

To check the application from another terminal, run:

```sh
npm run dev:aspire:check
```

The check waits for all services, checks the frontend API proxy, and prints the application URLs.

## Isolation and data

Each checkout has separate PostgreSQL and application data volumes.
Volume names start with `mealie-aspire-` and include a hash of the checkout path.
Data persists across restarts in that checkout.
Use one Aspire instance per checkout.
Use a separate checkout or worktree for another instance with separate data.

The containers use read-only source mounts.
The frontend image contains dependencies, and its container stores build files.
They do not use the host Python environment, frontend dependencies, `.env`, `.dev.env`, or `dev/data`.
The backend sends email to Mailpit.
Select the Mailpit HTTP URL in the dashboard to read email.

Source edits trigger hot reload.
Restart Aspire after edits to dependency files or Dockerfiles.
The next image build installs dependencies from the lockfiles.

## Stop and restart

Press Ctrl+C in the original terminal to stop the stack.
Aspire removes the session containers and keeps the data volumes.

For a background session, use:

```sh
npm run dev:aspire -- --detach
```

To stop a background session, run:

```sh
aspire stop --apphost dev/aspire/apphost.mts
```

To delete this checkout's development data, stop Aspire first.
Then remove its two named Docker volumes:

```sh
node --input-type=module -e 'import {createHash} from "node:crypto"; import {realpathSync} from "node:fs"; console.log("mealie-aspire-" + createHash("sha256").update(realpathSync(".")).digest("hex").slice(0, 12))'
docker volume rm <prefix>-postgres <prefix>-data
```

Use the prefix from the first command in the second command.
The next start creates a new database and default account.
