# App + Platform Blueprint — building an internal tool the way we like it

**How to use this file.** Give Claude your idea plus a pointer to this file, e.g.:

> "Build a tool that lets ops staff upload a CSV of suppliers, validate it, and push it to our API. Follow `app-platform-blueprint.md`."

Claude then builds the idea as **two separate solutions** — a React `-app` (frontend) and a
.NET `-platform` (backend) — exactly as described here. The **app-platform-poc** skill wraps this
file in a step-by-step workflow (plan → confirm → scaffold → verify → hand over); this file stays
the source of truth for the stack, the layout, and the code.

**Conventions used below — read these first.**

- **Shell snippets are POSIX `sh`** (bash, or Git Bash on Windows). In PowerShell, assign with
  `$ROOT = "..."` / `$P = "..."` and reference as `$ROOT` / `$P`; the `NAME="value"` form is a
  parse error there. Everything else is identical.
- **`jsonc` blocks contain `//` notes written for you, the implementer.** Don't copy those comment
  lines into the generated file.
- **Placeholders:** `AppTemplate` / `app-template` inside code, and `<tool>` / `<Tool>` /
  `<Feature>` / `<Integration>` in paths and prose. Replace **all** of them (§2) — nothing you hand
  over should still contain one.

> [!IMPORTANT]
> **Never** scaffold the tool as a Python app, a Streamlit app, or a single fused
> frontend+backend project. Always the app + platform split below.

> [!NOTE]
> **A database and authentication are both optional.** This file is a **stateless, auth-agnostic**
> baseline, and it's the only one you need for a tool that neither stores data nor logs anyone in.
> The two optional pieces are separate files in this folder, read only when they apply:
>
> | File | Read it when | Size |
> |---|---|---|
> | `app-platform-blueprint.md` (this one) | always | ~970 lines |
> | `appendix-b-database.md` | the tool persists data — **or** has auth | ~150 lines |
> | `appendix-a-auth.md` | the tool needs a login and/or admin area | ~530 lines |
>
> Apply **B before A** (auth's `Users` table lives in B's database). Many internal tools need
> neither; skip whatever doesn't apply rather than reading ahead.

---

## Prerequisites

Check these before scaffolding. Install commands cover Windows (`winget`) and macOS (Homebrew);
every tool also has an installer at the linked site.

**Required — to build and run the tool:**

- **.NET 10 SDK** — check: `dotnet --list-sdks` (you need a `10.x` entry).
  Install: `winget install Microsoft.DotNet.SDK.10` · `brew install --cask dotnet-sdk` ·
  <https://dotnet.microsoft.com/download/dotnet/10.0>
- **Node.js — an active LTS, and not just any "20+"** (includes npm). Check: `node -v`, `npm -v`.
  The real requirement is whatever the Vite toolchain declares, which rises over time; at the time of
  writing `vite` and `@vitejs/plugin-react` want `^20.19.0 || >=22.12.0`, so 20.0–20.18 fails at
  install or build. **Don't trust this line — read it from the tooling after scaffolding:**
  ```bash
  node -p "require('./node_modules/vite/package.json').engines.node"
  ```
  and use the newest LTS that satisfies it. §7.1 records your choice in `.nvmrc` so CI uses the same
  one.
  Install: `winget install OpenJS.NodeJS.LTS` · `brew install node` · <https://nodejs.org>
- **Docker Desktop** — for the local `docker compose` run (and the Postgres container if the tool
  has a DB). Check: `docker --version` **and** `docker info` (confirms the daemon is running).
  Install: `winget install Docker.DockerDesktop` · `brew install --cask docker` ·
  <https://www.docker.com/products/docker-desktop>
  *(A stateless tool with no DB can instead just `dotnet run` the API + `npm run dev` — Docker
  optional then. If you do, the API must still listen on **8080** so it matches the frontend's
  default `API_BASE` — see the `launchSettings.json` step in §6.1.)*

**Conditional:**

- **dotnet-ef** (EF Core CLI) — only if the tool uses a **database** (Appendix B).
  Check: `dotnet ef --version`. Install: `dotnet tool install --global dotnet-ef`.
  If it's already installed, `dotnet tool install` fails — use `dotnet tool update --global dotnet-ef`.
  The CLI's **major must match the EF Core packages'** major (`10.x` on .NET 10); the patch level
  doesn't need to match.

Quick check of the required set in one line:
```bash
dotnet --list-sdks; node -v; npm -v; docker --version
```

---

## 1. The stack (non-negotiable)

| Layer | Choice |
|---|---|
| **Backend** (`<tool>-platform`) | .NET 10, ASP.NET Core Web API, layered folders (Presentation / Application / Domain / Infrastructure / Security) |
| **Frontend** (`<tool>-app`) | React 19 + Vite + TypeScript + Tailwind v4 + react-router + axios (`withCredentials`) |
| **Persistence** | *Optional* — PostgreSQL via EF Core (**Appendix B**). Add only if the tool persists data (or uses auth). A stateless tool has no database |
| **Auth** | *Optional* — see **Appendix A**. Custom BCrypt + JWT in an httpOnly cookie; add only if the tool needs a login/admin area. Requires the database |
| **Local run** | `Dockerfile` + `docker-compose.yml` (the API, plus Postgres if the tool has a DB) |
| **Cloud** | An infra **skeleton** (components manifest) — the receiving infra owner completes it (§10) |

Keep it **lean** — these are usually interim/internal tools. Don't add OpenTelemetry,
rate limiting, message queues, etc. unless the idea actually needs them.

### Versions — pin the majors, never the patches

This document fixes the stack at **major** level only: .NET 10, React 19, Tailwind v4, Node 20.19+/22.12+,
PostgreSQL 16+. Everything below that is resolved at scaffold time, so the blueprint doesn't rot as
packages ship:

- **Add packages without `--version`.** `dotnet add package <Name>` resolves the newest stable
  version compatible with the project's target framework; `npm install <pkg>` does the same for the
  app. A pinned patch level in a document is out of date the week after it's written.
- **The one rule that matters: majors must agree.** Every `Microsoft.EntityFrameworkCore.*`,
  `Npgsql.EntityFrameworkCore.PostgreSQL`, and `Microsoft.AspNetCore.*` package must sit on the same
  major as the SDK (`10.x` on .NET 10). Check the resolved numbers in the `.csproj` after adding, and
  fix any that drifted — mixed majors are what actually break a build. Packages on their own release
  line (`BCrypt.Net-Next`, `System.IdentityModel.Tokens.Jwt`, `xunit`) just take their latest stable.
- **Differing *patch* levels inside one major are fine, but not always silent.** The EF provider
  usually floors `Microsoft.EntityFrameworkCore.Relational` lower than EF Core itself resolves (e.g.
  Npgsql wants `10.0.4`, EF brings `10.0.11`), and the test project then logs `warning MSB3277`
  about the unification. It's benign — MSBuild unifies upward to the higher version — so leave it, or
  silence it by taking the same patch across the EF packages if a clean log matters to you.
- **Reproducibility comes from the lock, not the doc.** The generated `.csproj` and
  `package-lock.json` record exactly what was resolved, and they're committed — that's the record of
  what this build used. `dotnet list package --vulnerable` + `npm audit` (§11) is the check before
  hand-over.
- **Every version lives in the generated repo, never twice.** This document states *rules*; the repo
  states *numbers*. Node's version goes in `<tool>-app/.nvmrc` and CI reads it with
  `node-version-file` rather than repeating a literal (§7.1 + the CI workflow). Package versions live
  in the `.csproj` and `package-lock.json`. The .NET version is the one deliberate exception — it's a
  stack decision (§1), so it appears in the TFM, the two Docker tags, and CI's `dotnet-version`; the
  note below lists all four. If you ever find yourself typing the same version number into two files,
  one of them should be reading it from the other.

> **Moving to a newer .NET later** means changing four things, and nothing else: the TFM
> (`-f net10.0` in §6.1 and the Testing section), the two Docker image tags (§6.7), the version in
> the §1 table, and the SDK version in the CI workflow. The "majors must agree" rule then pulls the
> packages along on the next restore.

---

## 2. Naming

Pick the tool name once, then use it consistently. For a tool called **Widget Sync**:

| Token | Value | Used for |
|---|---|---|
| kebab `<tool>` | `widget-sync` | folder names, DB, JWT issuer |
| Pascal `<Tool>` | `WidgetSync` | .NET project + namespace |

- Folders: `widget-sync/widget-sync-platform` and `widget-sync/widget-sync-app`
- .NET project/namespace: `WidgetSync.Platform` (`WidgetSync.Platform.*`)
- DB name: `WidgetSync`; (if auth) JWT issuer `widget-sync`, audience `widget-sync-users`

**All embedded code below uses the placeholder `AppTemplate` (Pascal) / `app-template`
(kebab). Find-and-replace those with the real tool name.**

---

## 3. Turn the idea into a plan (do this first)

From the idea, decide:

1. **Does it need to persist data?** If the tool just transforms / proxies / validates with no
   stored state, it needs **no database** — skip EF Core/Postgres entirely (a leaner API). Add a
   database — **Appendix B** (`appendix-b-database.md`) — only if it stores domain data **or** uses
   auth (which needs a `Users` table).
2. **Does it need auth?** A login and/or admin area — yes or no? Many internal tools don't
   (they sit behind VPN/SSO, or are single-purpose). If **yes**, apply **Appendix A**
   (`appendix-a-auth.md`; this also pulls in the database). If **no**, skip all auth: no login page,
   controllers left unauthenticated, no `JwtSettings`/`Seeding` config.
3. **Domain entities** (only if persisting) → EF Core tables.
4. **Features** → each becomes one backend controller (+ service if there's logic) **and** one
   frontend page/tab. Common shape for "upload → process → send" tools: a `preview` endpoint
   (parse + return, no side effects) and an `ingest`/`action` endpoint (do it, often with a
   `dryRun` flag).
5. **Admin-managed config?** If the tool holds credentials/settings users edit in-app, add a
   single-row settings entity + a settings screen (needs the database + auth).
6. **External integrations** → a typed `HttpClient` in `Application/<Integration>/`.

State this plan back and **wait for confirmation** before scaffolding anything — the database and
auth answers change the file set, and reversing them later is more work than asking.

Settle decisions 1 and 2 **now**, not mid-build — they decide which of the three blueprint files you
read at all. If the tool has both a database and auth, apply `appendix-b-database.md` and
`appendix-a-auth.md` *before* creating the first EF migration, so you get a single `InitialCreate`
that already contains `Users` (see B.7) rather than `InitialCreate` + `AddUsers`.

7. **Branching model.** State it rather than letting it fall out of a CI trigger: the default is
   **trunk-based** — a single `main`, short-lived branches, CI on push and pull request — because git
   flow is ceremony for a single-developer PoC. Say so in the plan and in the README, so a receiving
   team on a different model inherits a stated decision instead of an accident. (Being settled
   org-wide; if the standard lands as trunk plus release tags, this becomes the standard rather than
   a default.)

Then build in this order: platform baseline (§6.1–6.4) → Appendix B if persisting → Appendix A if
auth → features (§6.5) → Docker (§6.7) → frontend (§7) → tests → README (§8) → terraform skeleton
(§10) → CI. Verify with §6.6 and the §11 checklist.

---

## 4. Models — the contract between app and platform

The pair of type definitions — **C# on the platform, TypeScript on the app** — *is* the API
contract. Define the models on **both** sides and keep them in lockstep: when one changes,
change the other in the same change set. This makes the boundary explicit and stops the app and
platform from silently drifting apart.

- **Platform = source of truth for the shape.** Define request/response **DTOs** as C#
  records/classes. **Default: at the bottom of the controller file** that uses them — one file to
  read per endpoint. Move a DTO to `Application/<Feature>/` only once a second controller or a
  service signature needs it. Controllers accept and return these DTOs — **never expose EF
  entities directly** on the API (don't leak `Domain` types or lazy-load surprises to the wire).
- **App = a faithful mirror.** Define matching TypeScript `interface`s in the feature's
  `src/api/<feature>Api.ts`, and type every `apiGet`/`apiPost` call with them so the compiler
  enforces the contract on the frontend.
- **Casing must match the serializer.** By default ASP.NET serializes **camelCase**, so TS
  interfaces use camelCase (`createdAt`). If a payload must be snake_case (e.g. an external
  API's contract), serialize *that* payload with `JsonNamingPolicy.SnakeCaseLower` (or
  `[JsonPropertyName]`) and mirror snake_case in the TS interface. One casing per payload, and
  the two sides must agree.
- **Log with message templates, not interpolation.** `logger.LogInformation("Parsed {Rows} rows for {Supplier}", rows, supplier)`, never `$"Parsed {rows} rows"`. Named properties are what make logs searchable the moment anything structured is put in front of them, and converting a codebase later is a full sweep. Costs nothing now.
- **Type mapping:** `DateTimeOffset`→`string` (ISO), `int`/`decimal`→`number`, `bool`→`boolean`,
  arrays→`T[]`, nullable→`T | null` (or optional `?`). One request DTO + one response DTO per
  endpoint, mirrored 1:1.
- **Ids are `string`** (a GUID as string, as in `Guid.NewGuid().ToString()`) unless the idea needs
  otherwise — so entity keys, DTO ids, and the TS mirror are all `string`, with no `number`/`string`
  mismatch across the wire.
- **Correlation travels in a header, not the body.** Every response carries `X-Correlation-ID` (§6.3),
  so a user-reported failure can be found in the logs. Deliberately *not* a body field: a body field
  would have to be added by every hand-written `BadRequest(new { error = ... })` in every controller,
  and the first one anybody forgets is the one they needed. The header is set by middleware and is
  therefore always right, whoever wrote the body.
- **Errors have a contract too.** Every non-2xx body is `{ "error": "<human-readable message>" }`.
  That's what the app's `errorMessage()` reads (§7.2), so it applies to *everything*: hand-written
  `BadRequest(new { error = ... })`, `[ApiController]`'s automatic model-validation 400s, and
  unhandled 500s — the latter two only if you wire them up, which §6.3 does. Without that wiring
  a validation failure reaches the user as "Request failed with status code 400" and the real
  reason is lost.

**Worked example — an `Item` feature.** Platform DTOs (bottom of `ItemController.cs`):
```csharp
public record ItemResponse(string Id, string Title, DateTimeOffset CreatedAt);
public class CreateItemRequest { [Required] public string Title { get; set; } = ""; }
```
App mirror (`src/api/itemsApi.ts`):
```ts
export interface Item { id: string; title: string; createdAt: string; }   // mirrors ItemResponse
export interface CreateItem { title: string; }                            // mirrors CreateItemRequest
export const listItems  = ()               => apiGet<Item[]>("/api/items").then(r => r.data);
export const createItem = (body: CreateItem) => apiPost<Item>("/api/items", body).then(r => r.data);
```

> **Optional:** for larger or fast-moving APIs, generate the TS types from the platform's OpenAPI
> doc (`/openapi/v1.json`) instead of hand-mirroring. For lean interim tools, hand-maintained
> mirrored types are simpler and fine — as long as they stay in sync.

---

## 5. Repository layout

```
<tool>/                                  # a git repo — `git init` + .gitignore before the first build (§11)
├── README.md                            # how to run + env vars (required — §8)
├── .gitignore                           # see §11 for the entry list
├── .github/workflows/ci.yml             # CI build+test (+ optional deploy stub) — see CI/CD section
├── <tool>-platform/                     # .NET backend solution
│   ├── AppTemplate.Platform.slnx        # or .sln — whichever the SDK wrote (§6.1)
│   ├── AppTemplate.Platform/
│   │   ├── Program.cs
│   │   ├── Properties/launchSettings.json  # applicationUrl → http://localhost:8080 (§6.1)
│   │   ├── Presentation/Controllers/    # one controller per feature (+ AuthController if auth)
│   │   ├── Application/                  # services, integrations, parsers
│   │   ├── Domain/                       # entities, if persisting (+ Common/User.cs if auth)
│   │   ├── Infrastructure/
│   │   │   ├── Persistence/              # DB only, Appendix B: DbContext, factory (+ UserSeeder if auth)
│   │   │   └── ServiceConfiguration/     # ServiceCollectionExtensions
│   │   ├── Security/                     # (only if auth: AuthenticationService, JwtTokenProvider)
│   │   ├── Migrations/                   # DB only (Appendix B)
│   │   └── appsettings.json / appsettings.Development.json
│   ├── tests/AppTemplate.Platform.Tests/   # xUnit, wired into the solution (Testing section)
│   ├── Dockerfile
│   ├── .dockerignore                     # required, not optional (§6.7)
│   ├── docker-compose.yml
│   └── terraform/                        # infra skeleton — components manifest (§10)
└── <tool>-app/                          # React frontend
    ├── .nvmrc                            # the Node version; CI reads it (§7.1)
    └── src/
        ├── lib/{config.ts, api/client.ts}   # (+ auth/ if auth)
        ├── api/                          # one module per feature (+ authApi if auth)
        ├── components/{ui.tsx, Layout.tsx}  # (+ ProtectedRoute.tsx if auth)
        ├── pages/                        # one per feature (+ LoginPage if auth)
        ├── test/setup.ts                 # Vitest setup (Testing section)
        ├── router.tsx, App.tsx, main.tsx, index.css
```

> The tree shows the **full** shape. A **stateless** tool omits `Persistence/`, `Migrations/`, and
> the connection string (Appendix B); a **no-auth** tool omits `Security/`, `Common/User.cs`, and
> the frontend `auth/` + `LoginPage` / `ProtectedRoute` (Appendix A).

---

## 6. Build the backend (`<tool>-platform`)

The baseline below is a **stateless** API — controllers + OpenAPI + health + CORS, **no database,
no auth**. Add persistence via **Appendix B** (`appendix-b-database.md`) and login via
**Appendix A** (`appendix-a-auth.md`) only if the idea needs them — open those files at the point
you apply them, not before.

### 6.1 Scaffold

```bash
ROOT="<tool>/<tool>-platform"
dotnet new sln -n AppTemplate.Platform -o "$ROOT"
dotnet new webapi --use-controllers -n AppTemplate.Platform -o "$ROOT/AppTemplate.Platform" -f net10.0

# The SDK writes EITHER AppTemplate.Platform.slnx OR .sln depending on version — look, don't assume:
ls "$ROOT"                                      # PowerShell: Get-ChildItem $ROOT
SLN="$ROOT/AppTemplate.Platform.slnx"           # ...or .sln, whichever is actually there
P="$ROOT/AppTemplate.Platform/AppTemplate.Platform.csproj"

dotnet sln "$SLN" add "$P"

# Delete the template's sample endpoint and scratch files — in current SDKs exactly these three:
rm -f "$ROOT/AppTemplate.Platform/WeatherForecast.cs" \
      "$ROOT/AppTemplate.Platform/Controllers/WeatherForecastController.cs" \
      "$ROOT/AppTemplate.Platform/AppTemplate.Platform.http"
rmdir "$ROOT/AppTemplate.Platform/Controllers" 2>/dev/null   # controllers live in Presentation/Controllers/ (§5)
# If your SDK scaffolded something else, delete whatever sample model + controller it created.

# No extra packages in the baseline. Appendix B adds EF/Npgsql; Appendix A adds BCrypt + JwtBearer.
```

Then set the local port in `AppTemplate.Platform/Properties/launchSettings.json`: the `http`
profile's `"applicationUrl"` must be `"http://localhost:8080"`, and drop (or ignore) the `https`
profile. **This matters** — the container listens on 8080 (§6.7) and the frontend defaults to
`http://localhost:8080` (§7.2), so a `dotnet run` on the template's default 5xxx port gives you a
frontend calling a dead address.

> .NET 10 notes: the SDK normally writes a **`.slnx`** (XML) solution rather than `.sln` — use
> whichever the `ls` above showed, here and in the Testing section. `--use-controllers` gives
> controllers (not minimal APIs). Use the **built-in OpenAPI** (`AddOpenApi()` / `MapOpenApi()`)
> that the template references — don't add Swashbuckle. `$SLN` and `$P` are reused by the later
> sections and both appendices.

### 6.2 `Program.cs`

```csharp
using AppTemplate.Platform.Infrastructure.ServiceConfiguration;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddApplicationServices(builder.Configuration, builder.Environment);
var app = builder.Build();
app.UseApplicationMiddleware();
// If using a database (Appendix B): await app.InitializeDatabaseAsync();   // before Run()
app.Run();

public partial class Program { }        // so integration tests can host it
```

### 6.3 `ServiceCollectionExtensions.cs` — DI + middleware

```csharp
using System.Reflection;
using Microsoft.AspNetCore.Mvc;

namespace AppTemplate.Platform.Infrastructure.ServiceConfiguration;

public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddApplicationServices(this IServiceCollection services, IConfiguration config, IWebHostEnvironment env)
    {
        // `??` is not enough: appsettings.json ships this key as "" (present but empty), and
        // WithOrigins("") matches no origin at all — every browser call would fail CORS.
        var origin = config["Cors:AllowedOrigin"];
        if (string.IsNullOrWhiteSpace(origin))
        {
            // Fall back only in development. In production a missing origin is a misconfiguration:
            // without this throw the API comes up healthy while serving a credentialed policy for
            // localhost, which is both useless and wrong. §8 lists the var as required — mean it.
            if (!env.IsDevelopment()) throw new InvalidOperationException("Cors:AllowedOrigin missing");
            origin = "http://localhost:5173";
        }
        // WithExposedHeaders is what lets the SPA *read* the correlation id: cross-origin JavaScript
        // cannot see a custom response header unless it is named here. Omit it and the header arrives
        // while the browser silently hides it.
        services.AddCors(o => o.AddPolicy("AllowFrontend", p => p
            .WithOrigins(origin).AllowAnyMethod().AllowAnyHeader().AllowCredentials()
            .WithExposedHeaders(CorrelationId.HeaderName)));

        // >>> register your tool's services + typed HttpClients here <<<
        // Database? add the registrations from Appendix B.   Auth? add the registrations from Appendix A.

        services.AddControllers()
            // Keep [ApiController]'s automatic validation 400s in the { error } shape the app reads
            // (§4). The default is ProblemDetails, which errorMessage() can't unwrap — the user
            // would see "Request failed with status code 400" instead of what was wrong.
            .ConfigureApiBehaviorOptions(o => o.InvalidModelStateResponseFactory = ctx =>
            {
                var errors = ctx.ModelState.Values.SelectMany(v => v.Errors).ToArray();
                // A binding/parse failure carries an Exception, and its message leaks JSON paths and
                // byte offsets ("The JSON value could not be converted... LineNumber: 0 |
                // BytePositionInLine: 15") — not something to show a user. Only DataAnnotation
                // messages are written to be read.
                if (errors.Any(e => e.Exception is not null))
                    return new BadRequestObjectResult(new { error = "Malformed request body." });

                var msg = string.Join("; ", errors.Select(e => e.ErrorMessage).Where(m => !string.IsNullOrWhiteSpace(m)));
                return new BadRequestObjectResult(new { error = string.IsNullOrWhiteSpace(msg) ? "Invalid request" : msg });
            });
        services.AddOpenApi();
        services.AddHealthChecks();
        return services;
    }

    public static WebApplication UseApplicationMiddleware(this WebApplication app)
    {
        // FIRST — everything after this, including the exception handler, needs the id to exist.
        app.UseCorrelationId();
        // Unhandled exceptions → the same { error } shape. The middleware logs the exception itself,
        // so the detail lands in the logs without leaking a stack trace to the browser.
        app.UseExceptionHandler(b => b.Run(async ctx =>
        {
            ctx.Response.StatusCode = StatusCodes.Status500InternalServerError;
            // UseExceptionHandler clears the response before running this, wiping the header the
            // correlation middleware set — so put it back, or 500s become the one case with no id.
            // HttpContext.Items survives the clear, which is why the id is stashed there too.
            var id = CorrelationId.For(ctx);
            if (!string.IsNullOrWhiteSpace(id)) ctx.Response.Headers[CorrelationId.HeaderName] = id;
            await ctx.Response.WriteAsJsonAsync(new { error = "Unexpected server error" });
        }));
        if (app.Environment.IsDevelopment()) app.MapOpenApi();
        // Deliberately no UseHttpsRedirection: the API serves http on 8080 in every local run mode,
        // and in Azure the Container App ingress terminates TLS. In a container it would only log
        // "failed to determine the https port for redirect" on every boot.
        app.UseCors("AllowFrontend");
        // If using auth (Appendix A): app.UseAuthentication(); app.UseAuthorization();  (here, before MapControllers)
        app.MapHealthChecks("/health");
        // "Is the deployed thing actually my change?" — one curl instead of a portal dig. Anonymous
        // like /health, and it returns nothing but the version: no build paths, no machine names.
        app.MapGet("/version", (IConfiguration config) =>
        {
            var version = config["APP_VERSION"];      // set by the deploy step to the image tag (§10)
            if (string.IsNullOrWhiteSpace(version))
                version = Assembly.GetEntryAssembly()?.GetCustomAttribute<AssemblyInformationalVersionAttribute>()?.InformationalVersion;
            return Results.Ok(new { version = string.IsNullOrWhiteSpace(version) ? "unknown" : version });
        }).AllowAnonymous();
        app.MapControllers();
        return app;
    }
}
```

> `BadRequestObjectResult` needs `using Microsoft.AspNetCore.Mvc;` and the version lookup needs
> `using System.Reflection;` (both shown); `StatusCodes` and `WriteAsJsonAsync` come from the Web
> SDK's implicit usings.

**`Infrastructure/ServiceConfiguration/CorrelationId.cs`** — the id that ties a user's failed click to
a log line. Copy as written; the ordering and the explicit log line are both load-bearing:

```csharp
namespace AppTemplate.Platform.Infrastructure.ServiceConfiguration;

public static class CorrelationId
{
    public const string HeaderName = "X-Correlation-ID";

    public static IApplicationBuilder UseCorrelationId(this IApplicationBuilder app) =>
        app.Use(async (ctx, next) =>
        {
            // The inbound value is caller-controlled and ends up in a log line and a response header,
            // so trust it only if it can't do damage: newlines would let a caller forge log entries,
            // and an oversized value gets reflected into every response.
            var id = ctx.Request.Headers[HeaderName].FirstOrDefault();
            if (!IsUsable(id))
                id = Guid.NewGuid().ToString("n")[..12];      // short enough to read down a phone

            ctx.Items[HeaderName] = id;                      // survives UseExceptionHandler's clear
            ctx.Response.Headers[HeaderName] = id;

            var logger = ctx.RequestServices.GetRequiredService<ILoggerFactory>().CreateLogger("Request");
            // BeginScope is for structured sinks (App Insights, Seq) that record scope properties.
            // Do NOT rely on it for the console — rendering scopes needs IncludeScopes, which is easy
            // to configure in the wrong place and silent when you do. The explicit line below is what
            // makes the id greppable in `docker compose logs`, and it doubles as an access log.
            using (logger.BeginScope(new Dictionary<string, object> { ["CorrelationId"] = id }))
            {
                await next();
                logger.LogInformation("{Method} {Path} -> {StatusCode} [{CorrelationId}]",
                    ctx.Request.Method, ctx.Request.Path, ctx.Response.StatusCode, id);
            }
        });

    public static string? For(HttpContext ctx) => ctx.Items[HeaderName] as string;

    private static bool IsUsable(string? id) =>
        !string.IsNullOrWhiteSpace(id)
        && id.Length <= 64
        && id.All(c => char.IsAsciiLetterOrDigit(c) || c == '-');
}
```

> **Why an explicit log line rather than scopes alone.** Verified on a real run: with
> `Logging:Console:IncludeScopes` *or* `Logging:Console:FormatterOptions:IncludeScopes` set, the
> console emitted no scopes at all, so the id was nowhere in `docker compose logs` while looking
> perfectly correct in code. Log it explicitly and the id is there regardless of formatter.
>
> **Error tracking later.** If a Sentry or App Insights hook is ever wanted, the exception handler
> above is the single funnel every unhandled failure already passes through — one registration, not
> an audit. Leave the seam; don't wire a key at scaffold time to infrastructure nobody has chosen.

### 6.4 `appsettings.json` + `appsettings.Development.json`

Remember the `//` lines are notes to you — the committed JSON files contain no comments.

```jsonc
// appsettings.json — no secrets committed; prod supplies config via env/Key Vault
{
  "Logging": { "LogLevel": { "Default": "Information", "Microsoft.AspNetCore": "Warning" } },
  "AllowedHosts": "*",
  "Cors": { "AllowedOrigin": "" }   // intentionally empty — Development + compose + prod env supply it
  // Database? add "ConnectionStrings" (Appendix B).  Auth? add "JwtSettings" + "Seeding" (Appendix A).
}
```
```jsonc
// appsettings.Development.json — local only
{
  "Cors": { "AllowedOrigin": "http://localhost:5173" }
}
```

### 6.5 Features (the idea)

For each feature, add a controller under `Presentation/Controllers/`, **a service in
`Application/<Feature>/`**, and (if persisting) entities in `Domain/`.

**The service is not optional, even when the feature looks too small for one.** "Add a service if
there's logic" is the judgement call that gets made wrong most often, and moving data access out of
controllers *after* hand-over touches every endpoint and every test at once. One extra file per
feature at scaffold time buys a controller that only binds, calls and maps — and a service that unit
tests can drive without spinning up the web host. The controller gets `ITodoService`, never
`ApplicationDbContext`.

A shape that keeps controllers thin without inventing machinery: the service returns a small record
carrying either the result or the reason it failed, and the controller maps that onto status codes.

```csharp
public sealed record TodoOutcome(Todo? Todo, string? Error = null, bool NotFound = false);

// in the controller:
private ActionResult<TodoResponse> Respond(TodoOutcome outcome)
{
    if (outcome.NotFound) return NotFound(new { error = outcome.Error });
    if (outcome.Error is not null) return BadRequest(new { error = outcome.Error });
    return Ok(ToResponse(outcome.Todo!));
}
``` **Write the route out in
lowercase — `[Route("api/todos")]`, not `[Route("api/[controller]")]`.** The token form renders the
class name's casing into the URL (`/api/Todos`), and since ASP.NET routing is case-insensitive the
mismatch stays invisible on the server while the app's URLs, interceptor string matches, and logs
disagree with each other. Define its request/response
DTOs and mirror them in the app per **§4** (controllers return DTOs, never EF entities). Reuse the
**preview / action(+dryRun)** shape for upload-and-process tools. When response JSON casing must
match an external contract exactly, serialize with an explicit `JsonSerializerOptions`
(snake_case via `JsonNamingPolicy.SnakeCaseLower`, or `[JsonPropertyName]`) and return
`Content(json, "application/json")` rather than relying on the default serializer.

> Inject `ApplicationDbContext` (Appendix B) into the **service** if the feature persists data — not
> into the controller; protect endpoints with `[Authorize]` / `[Authorize(Policy="AdminOnly")]`
> (Appendix A) if the tool has auth.

> **File uploads — set the limit deliberately.** Kestrel caps a request body at ~30 MB by default,
> so a larger upload fails with a bare 413 that says nothing useful. Decide the real ceiling per
> endpoint: raise it with `[RequestSizeLimit(bytes)]` on the action (plus
> `MultipartBodyLengthLimit` if you're reading the multipart sections yourself), or keep it low and
> validate `file.Length` in the action so you can return the `{ error }` shape (§4) with a message
> the user can act on. Also reject the wrong content type early rather than letting the parser fail
> deep in a 40 000-row CSV.

### 6.6 Verify

```bash
dotnet build "$P"
```
(With a database, also add the initial migration — see Appendix B.)

### 6.7 `Dockerfile` + `.dockerignore` + `docker-compose.yml`

```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
COPY AppTemplate.Platform/AppTemplate.Platform.csproj AppTemplate.Platform/
RUN dotnet restore AppTemplate.Platform/AppTemplate.Platform.csproj
COPY AppTemplate.Platform/ AppTemplate.Platform/
RUN dotnet publish AppTemplate.Platform/AppTemplate.Platform.csproj -c Release -o /app --no-restore

FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS runtime
WORKDIR /app
COPY --from=build /app .
# Run as the non-root user the .NET images already provide (UID 1654). Portable across the
# Debian/Ubuntu/Azure-Linux bases — don't `adduser`/`useradd` (not present on all of them).
USER $APP_UID
ENV ASPNETCORE_URLS=http://+:8080
EXPOSE 8080
ENTRYPOINT ["dotnet", "AppTemplate.Platform.dll"]
```

A **`.dockerignore`** next to the Dockerfile is **required** — without it your host `bin/`/`obj/`
get copied into the image and break `dotnet publish --no-restore` (the host-restored `obj` has
paths that don't exist in the Linux build stage):
```
**/bin/
**/obj/
tests/
terraform/
*.tfstate*
.vs/
```
```yaml
# docker-compose.yml — baseline (stateless): just the API.
# Database? add a `db` service + ConnectionStrings__DefaultConnection (Appendix B).
# Auth? add JwtSettings__Key + Seeding__* (Appendix A). ASPNETCORE_ENVIRONMENT=Development keeps
# any auth cookie non-Secure so it works over http locally.
services:
  api:
    build: { context: ., dockerfile: Dockerfile }
    environment:
      ASPNETCORE_ENVIRONMENT: Development
      Cors__AllowedOrigin: "http://localhost:5173"
    ports: ["8080:8080"]
```

---

## 7. Build the frontend (`<tool>-app`)

### 7.1 Scaffold

Run these from `<tool>/` (the repo root) so the app lands as a sibling of `<tool>-platform`:

```bash
npm create -y vite@latest <tool>-app -- --template react-ts
cd <tool>-app
npm install
npm install axios react-router-dom
npm install -D tailwindcss @tailwindcss/vite
```

> **Both prompts here will hang a non-interactive shell.** `npm create` asks "Ok to proceed?" the
> first time it fetches `create-vite` — hence `-y` — and `create-vite` itself asks what to do if the
> target folder already exists, so make sure `<tool>-app/` does not exist beforehand. If a run does
> stall waiting on input, kill it, remove any half-created folder, and re-run.

**`vite.config.ts`** — write it once in its final shape, tests included:
```ts
import { defineConfig } from "vitest/config";       // not "vite" — the test block below needs this
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath } from "node:url";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    // The template sets "type": "module", so __dirname does NOT exist here — resolving the alias
    // with path.resolve(__dirname, "./src") fails at config load. Use import.meta.url.
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  server: { port: 5173 },
  test: { environment: "jsdom", globals: true, setupFiles: "./src/test/setup.ts" },
});
```
**`.nvmrc`** — write the Node major you're building with (just `22`, or whatever the newest LTS
satisfying the `engines` check in Prerequisites is). This is the single place the version lives: CI
reads it via `node-version-file`, and `nvm use` picks it up for anyone cloning the repo. Don't also
hardcode it in the workflow.

`src/index.css`: replace the template's contents with `@import "tailwindcss";`, and delete the
template's `src/App.css` and `src/assets/` — the shell below doesn't use them.
`tsconfig.app.json`: add `"paths": { "@/*": ["./src/*"] }` — **do not set `baseUrl`** (TS 6
deprecates it, and current templates ship TS 6). With `verbatimModuleSyntax` on, import types with
`import type`.

**Lint — the template ships one, so use it.** `create-vite` emits `.oxlintrc.json` and a
`"lint": "oxlint"` script; keep them rather than swapping in ESLint. Add
`typescript/consistent-type-imports` as an `error`, which turns §11's `import type` convention into a
failure instead of a habit, and keep the template's own `react/*` rules:

```jsonc
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": ["react", "typescript", "oxc", "import"],
  "categories": { "correctness": "error" },
  "rules": {
    "react/rules-of-hooks": "error",
    "react/only-export-components": ["warn", { "allowConstantExport": true }],
    "typescript/consistent-type-imports": "error"
  }
}
```

> `no-floating-promises` is worth wanting and **won't work as configured**: it needs type information,
> so it requires the extra `oxlint-tsgolint` package and `oxlint --type-aware`. Verified — without
> those, adding the rule silently does nothing, which is worse than not having it. Add the package if
> you want the rule; otherwise leave it out rather than pretending.

**`package.json`** — add `"engines": { "node": ">=22" }` (matching `.nvmrc`), and an `.npmrc`
containing `engine-strict=true`. Without engine-strict a wrong local Node only warns. Note the SPA is
never containerised — the Dockerfile covers the API only — so local Node is whatever is on `PATH`
until something enforces it.

### 7.2 API client + app shell (no-auth baseline)

**`src/lib/config.ts`**
```ts
// 8080 is the container port (§6.7) AND the launchSettings port (§6.1) — keep all three aligned,
// so `docker compose up` and `dotnet run` both work without touching VITE_API_BASE.
export const API_BASE: string = (import.meta.env.VITE_API_BASE as string | undefined) ?? "http://localhost:8080";
```
**`src/lib/api/client.ts`**
```ts
import axios from "axios";
import type { AxiosRequestConfig } from "axios";
import { API_BASE } from "@/lib/config";

export const CORRELATION_HEADER = "X-Correlation-ID";

export const http = axios.create({ baseURL: API_BASE, withCredentials: true });

/**
 * crypto.randomUUID exists only in a secure context — it is undefined over plain http on anything
 * that isn't localhost, which is exactly how a PoC gets demoed from a phone on the LAN. Calling it
 * blind throws inside the interceptor and fails EVERY request, not just the id. The id has no
 * security requirement; it only needs to be unique enough to grep for.
 */
function newCorrelationId(): string {
  const uuid = globalThis.crypto?.randomUUID?.();
  if (uuid) return uuid.replace(/-/g, "").slice(0, 12);
  return Math.random().toString(36).slice(2, 10) + Date.now().toString(36).slice(-4);
}

// One id per request so a user-reported failure can be found in the API logs.
http.interceptors.request.use((cfg) => {
  cfg.headers[CORRELATION_HEADER] = newCorrelationId();
  return cfg;
});

export const apiGet = <T>(u: string, c?: AxiosRequestConfig) => http.get<T>(u, c);
export const apiPost = <T>(u: string, d?: unknown, c?: AxiosRequestConfig) => http.post<T>(u, d, c);
export const apiPut = <T>(u: string, d?: unknown) => http.put<T>(u, d);
export const apiDelete = <T>(u: string) => http.delete<T>(u);
export const apiPostForm = <T>(u: string, f: FormData) => http.post<T>(u, f);

export function errorMessage(e: unknown): string {
  if (axios.isAxiosError(e)) {
    const d = e.response?.data as { error?: string; message?: string } | undefined;
    return d?.error ?? d?.message ?? e.message;
  }
  return e instanceof Error ? e.message : "Request failed";
}

/**
 * A quotable reference for failures the user can't act on — server errors and network failures.
 * Returns null for 4xx, where the message already says what to fix and an id is just noise.
 */
export function errorReference(e: unknown): string | null {
  if (!axios.isAxiosError(e)) return null;
  const status = e.response?.status;
  if (status !== undefined && status < 500) return null;
  const fromResponse = e.response?.headers?.[CORRELATION_HEADER.toLowerCase()] as string | undefined;
  // A network failure has no response at all — fall back to the id we sent, which is the case where
  // the user has least to go on and most needs something to quote.
  const fromRequest = e.config?.headers?.[CORRELATION_HEADER] as string | undefined;
  return fromResponse ?? fromRequest ?? null;
}
```
- **`App.tsx`** renders `<RouterProvider router={router} />`.
- **`router.tsx`** maps `/` → a `Layout` with one child route per feature.
- **`Layout.tsx`** is a top-nav shell with one `NavLink` per feature + an `<Outlet/>` (a single-feature tool can skip the nav).
- **`components/ui.tsx`** holds small shared bits (Button/Card/etc.). Give the error banner an
  optional `reference` prop and render it as small monospace text when set — pages pass
  `errorReference(e)`, so "something broke" always comes with something the user can quote and you
  can grep. Optionally show `/version`'s value in the layout footer, so anyone can say which build
  they're looking at without a curl.

> If the tool needs a login/admin area, use the **auth shell in Appendix A** instead — it adds a
> `UserProvider`, a `ProtectedRoute`, a `LoginPage`, an `authApi`, and a 401→logout interceptor
> on the client, and wraps the router in `<UserProvider>`.

### 7.3 Feature pages
The pages are entirely solution-dependent — this is just the pattern. For **each feature the idea
needs**, add one page under `src/pages/` and one typed API module under `src/api/` (its
request/response types follow **§4**; use `FormData` only if that feature uploads files), then wire
the page into `router.tsx` and a `NavLink` in `Layout.tsx`. A tool might have several tabs, a
single screen, or — with just one feature — no nav at all.

---

## Testing (set up as part of scaffolding)

Wire up both test projects during scaffolding so engineering has them **out of the box**. Run
with `dotnet test` (backend) and `npm test` (frontend).

### Backend — xUnit

```bash
T="$ROOT/tests/AppTemplate.Platform.Tests/AppTemplate.Platform.Tests.csproj"
dotnet new xunit -n AppTemplate.Platform.Tests -o "$ROOT/tests/AppTemplate.Platform.Tests" -f net10.0
dotnet sln "$SLN" add "$T"        # $SLN from §6.1 — .slnx or .sln, whichever the SDK wrote
dotnet add "$T" reference "$P"
```
(The `xunit` template brings xUnit + `Microsoft.NET.Test.Sdk` + the VS runner. Depending on SDK
version you'll get xUnit v2 or v3 — either is fine, and the `[Fact]` / `Assert` code below is
identical in both. Don't add xUnit packages by hand on top of the template's.) A sanity test:
```csharp
using Xunit;
namespace AppTemplate.Platform.Tests;

public class SanityTests
{
    [Fact]
    public void Adds() => Assert.Equal(2, 1 + 1);
}
```
- **Unit-test the domain logic directly** — parsers, transforms, validators, services. That's
  where the value is.
- For output that must match an **external contract**, use **golden-file tests**: run the logic
  on a checked-in sample input and assert the serialized output equals a checked-in expected file.
- For **endpoint/integration tests**, host the real app with `WebApplicationFactory<Program>`
  (`Program` is already exposed via `public partial class Program { }`) — add the package with
  `dotnet add "$T" package Microsoft.AspNetCore.Mvc.Testing` (same major as the SDK — see §1). Note the hosted app
  reads real config: a test that boots it needs a connection string if the tool has a database
  (point it at a throwaway DB, or keep those tests out of the default `dotnet test` run).

> Keep test fixtures with personal/customer data **out of the repo** (gitignore them) — see §11.

### Frontend — Vitest + React Testing Library

```bash
npm install -D vitest jsdom @testing-library/react @testing-library/jest-dom
```
`package.json` scripts → add `"test": "vitest run"` and `"test:watch": "vitest"`.
`vite.config.ts` → already carries the `vitest/config` import and the `test` block if you wrote it in
its final shape (§7.1); if not, add them now.
`src/test/setup.ts`:
```ts
import "@testing-library/jest-dom";
```
Example (a pure util from the baseline client):
```ts
import { describe, it, expect } from "vitest";
import { errorMessage } from "@/lib/api/client";

describe("errorMessage", () => {
  it("falls back for non-error values", () => expect(errorMessage("nope")).toBe("Request failed"));
});
```
Component tests use `render`/`screen` from `@testing-library/react` (jsdom is configured above).

---

## 8. README (required in every generated solution)

Always create a top-level `<tool>/README.md`. A new developer must be able to run the tool from
it alone. Include:

1. **Overview** — a clear, descriptive summary of the solution: **what it is**, **what it does**,
   and **the end goal / problem it solves**. Err toward detail at hand-over so the full picture
   comes across — it can always be trimmed later. A new reader should understand the purpose and
   intended outcome before the how.
2. **Prerequisites** — Docker, .NET 10 SDK, Node 20.19+/22.12+ (say which version you developed against).
3. **Run locally** — the two-terminal commands (§9).
4. **Environment variables** — a table of every var the platform reads and the frontend build
   uses, which are secrets, and their local-dev defaults. Baseline set:

   | Variable | Where | Required | Secret | Notes |
   |---|---|---|---|---|
   | `ConnectionStrings__DefaultConnection` | platform | if DB | yes | Postgres conn string (Appendix B); prod uses `SSL Mode=VerifyFull` |
   | `Cors__AllowedOrigin` | platform | yes | no | the frontend URL |
   | `ASPNETCORE_ENVIRONMENT` | platform | yes | no | `Development` locally, `Production` deployed |
   | `APP_VERSION` | platform | no | no | Image tag or commit SHA, surfaced by `GET /version`. Set by the deploy step; falls back to the assembly version, then `"unknown"` |
   | `VITE_API_BASE` | app (build) | no | no | API base URL; empty = same-origin |

   If the tool uses auth (Appendix A), also document `JwtSettings__Key` (secret),
   `JwtSettings__Issuer`/`__Audience`, and `Seeding__Admin1Username`/`__Admin1Password`
   (+ `Admin2`, secrets) — plus the seeded login credentials.
5. **Tests** — `dotnet test`, `npm test`, `npm run lint`, `npm run build`.
6. **Branching** — one line naming the model the repo uses (trunk-based by default, §3) so the next
   team doesn't have to infer it from the CI triggers.
7. **Deploy** — point to `<tool>-platform/terraform/README.md` (§10).

Keep it copy-pasteable. The `terraform/README.md` from §10 is a separate, infra-focused doc.

---

## 9. Local run

```bash
# terminal 1 (backend)
cd <tool>-platform && docker compose up --build      # API → http://localhost:8080
# terminal 2 (frontend)
cd <tool>-app && npm run dev                          # UI → http://localhost:5173
```
Without Docker (stateless tools only): `cd <tool>-platform/AppTemplate.Platform && dotnet run` —
also on <http://localhost:8080>, given the `launchSettings.json` port from §6.1.

If the tool has auth, log in with the seeded admin (dev default `admin` / `admin-password`).

---

## 10. Infrastructure skeleton (components manifest)

**Don't author full, apply-ready Terraform.** These tools are typically handed over, and
whoever owns infrastructure completes and applies it. Instead, ship a
`<tool>-platform/terraform/` **skeleton** that *declares which Azure components the tool needs*
and the *runtime configuration contract* the platform expects — enough for the infra owner to
wire it up without reverse-engineering the app. Meanwhile the tool already runs locally via the
`docker-compose.yml` from §6.7, so the cloud build can be deferred entirely.

Produce these three files:

### 10.1 `terraform/README.md` — the manifest (the real deliverable)

**Components in use** (what the infra owner must provision):

| Component | Why it's needed | Notes |
|---|---|---|
| Resource Group | Holds everything | one per environment |
| Azure Container Registry (ACR) | Stores the API image | image is pushed at deploy time, not by IaC |
| Container App (+ Environment) | Runs the .NET API | external ingress, `target_port = 8080`, HTTPS; pulls the image via a managed identity |
| PostgreSQL Flexible Server *(only if the tool has a DB)* | App database | `B_Standard_B1ms` is ample; TLS (`SSL Mode=VerifyFull`); reachable via "allow Azure services" or a private endpoint |
| Key Vault | Secrets store | connection string (if DB); JWT key & admin seed creds (if auth) |
| User-assigned managed identity | API → Key Vault + ACR access | roles: **Key Vault Secrets User**, **AcrPull** |
| Log Analytics workspace | Container App logs | |
| Static Web App | Hosts the React frontend | |

**Runtime configuration contract** — the Container App must be given these (secrets from Key
Vault; `.NET` maps `__` → `:`). The API migrates the DB on boot, so no separate migration step
is needed once these are set:

| Env var | Value | Source |
|---|---|---|
| `ASPNETCORE_ENVIRONMENT` | `Production` | plain |
| `APP_VERSION` | the image tag being deployed | plain (set by the deploy step, not IaC) |
| `ConnectionStrings__DefaultConnection` *(if DB)* | Postgres conn string incl. `SSL Mode=VerifyFull` | secret |
| `Cors__AllowedOrigin` | the frontend URL | plain |
| *(if auth)* `JwtSettings__Key` | 64-char random string | secret |
| *(if auth)* `JwtSettings__Issuer` / `__Audience` | `<tool>` / `<tool>-users` | plain |
| *(if auth)* `Seeding__Admin1Username` / `__Admin1Password` (+ `Admin2`) | the login accounts | secret |

**Decisions to state explicitly in the README** — these get made once, early, by whoever deploys, and
are painful to revisit afterwards. Don't guess at them; write down that they need deciding, and record
the answer once it exists:

- **Environment separation.** One environment, or a dev/prod pair? It changes naming, what can be
  shared, and whether the Static Web App and Container App come in pairs.
- **Postgres network posture.** "Allow Azure services" or a private endpoint. Awkward to tighten once
  things are connecting to it, so it shouldn't fall to whoever is in a hurry.
- **Backup and retention.** The flexible server's retention window, and whether geo-redundancy is on.
  Skippable for a throwaway; a decision if this is going to production — and the first person to want
  a restore is the wrong person to be finding out.

Naming conventions are deliberately *not* in scope here: the manifest names components, not instances,
and the receiving team owns their own naming.

**Deploy notes to record in the README:**
- *(if auth)* **Same-site cookie:** the SWA (`*.azurestaticapps.net`) and the Container App
  (`*.azurecontainerapps.io`) are *different sites*, so a `SameSite=Strict` auth cookie won't
  flow cross-site. Either **link the Container App as the SWA backend** (same-origin `/api`;
  build the frontend with `VITE_API_BASE=` empty) or use **same-parent custom domains**.
- **Secrets** live in Key Vault — nothing secret in Terraform state or the repo.
- **Image roll-out** (`az acr build` + `az containerapp update --image`) is a deploy step, not IaC.
- **The Static Web App picks its own Node version** for the frontend build, which makes it a fourth
  place the Node version effectively lives — and the one nobody looks at until a build that is green
  in CI fails in SWA. Record the version there to match `<tool>-app/.nvmrc`.

### 10.2 `terraform/main.tf` (stub)

Just the provider block plus a **commented `# TODO:` placeholder per component** from the table
above (showing the intended wiring: identity → KV/ACR roles, Container App → KV secrets +
`ingress target_port = 8080` + `ignore_changes` on the image). **No full resource bodies** — the
infra owner fills those in to their standards.

### 10.3 `terraform/variables.tf` (stub)

The inputs the infra owner will supply: `subscription_id`, `location`, `resource_group_name`,
`api_image`, `frontend_origin`.

---

## GitHub Actions (CI/CD) — CI recommended, CD optional

**CI (build + test) — ship it by default.** A workflow that builds and tests both projects on
every push/PR gives engineering an immediate safety net (and exercises the test setup above).
`.github/workflows/ci.yml`:

```yaml
name: CI
on:
  push: { branches: [main] }
  pull_request:
jobs:
  platform:
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: <tool>-platform } }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with: { dotnet-version: '10.0.x' }
      - run: dotnet build -c Release
      - run: dotnet test --no-build -c Release
  app:
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: <tool>-app } }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        # Reads <tool>-app/.nvmrc — the version lives in the repo, not in this file (§1, "Versions")
        with: { node-version-file: <tool>-app/.nvmrc, cache: npm, cache-dependency-path: <tool>-app/package-lock.json }
      - run: npm ci
      - run: npm run lint
      - run: npm run build
      - run: npm test
```
Unit tests must not need a live Postgres; an integration test that does can add a `postgres`
service container to the job.

**Deploy (CD) is the infra owner's job — not this step (§10).** Don't wire a deploy pipeline at
scaffold time: the Azure resources, names, and access (OIDC/credentials, ACR, Container App, SWA
token) aren't known yet, and §10 already records the deploy steps. If you want a placeholder,
leave an empty `.github/workflows/deploy.yml` stub for the infra owner to complete — otherwise
omit it. A local-only tool skips CD entirely (CI stays a recommended default).

---

## 11. Conventions & gotchas (checklist)

- [ ] Two projects: `<tool>-app` (React) + `<tool>-platform` (.NET). Never Python, never fused.
- [ ] Every endpoint has a request/response **DTO on the platform mirrored 1:1 by a TS interface** in the app; casing matches the serializer. Controllers return DTOs, not EF entities (§4).
- [ ] Every non-2xx body is `{ error: string }` — hand-written failures, `[ApiController]` validation 400s, and unhandled 500s all included (§4 + the wiring in §6.3).
- [ ] The API listens on **8080** in all three run modes — `docker compose`, `dotnet run` (launchSettings, §6.1), and the deployed container — and the app's `API_BASE` points there (§7.2).
- [ ] **Database is optional (Appendix B)** — PostgreSQL/EF Core only if the tool persists data or uses auth. A stateless tool drops the EF packages, `DbContext`/factory, migrations, connection string, and the Postgres service.
- [ ] **Auth is optional** — added only if the tool needs a login/admin area (Appendix A). Otherwise no login page, unauthenticated controllers, no `JwtSettings`/`Seeding`.
- [ ] Config via env vars in prod (`__` maps to `:`); secrets from Key Vault. Nothing secret committed.
- [ ] *(if DB)* EF: an `IDesignTimeDbContextFactory` so `dotnet ef` works without a DB. `InitializeDatabaseAsync` migrates on boot (and seeds admins if auth).
- [ ] .NET 10: `.slnx` solution — or `.sln`, whichever the SDK actually wrote (§6.1); `dotnet new webapi --use-controllers`; built-in OpenAPI (`AddOpenApi`/`MapOpenApi`).
- [ ] Packages added **unpinned**, and every EF / Npgsql / `Microsoft.AspNetCore.*` package resolved to the SDK's major (§1, "Versions"). The `.csproj` and `package-lock.json` are the record — both committed.
- [ ] No version number written in two places: Node's lives in `<tool>-app/.nvmrc` and CI reads it with `node-version-file`; the Node floor was checked against the toolchain's `engines`, not copied from this document.
- [ ] `GET /version` responds anonymously and reports something real (`APP_VERSION` locally, the image tag once deployed); the deploy step is documented as setting it (§10).
- [ ] Correlation: `X-Correlation-ID` on every response **including 500s**, named in `WithExposedHeaders` so the SPA can read it, logged explicitly on one line per request, and surfaced to the user by the error banner for 5xx and network failures. Verify the 500 case specifically — it's the one that breaks.
- [ ] Frontend: axios `withCredentials`; TS `import type`; `paths` alias without `baseUrl`.
- [ ] Local compose runs `ASPNETCORE_ENVIRONMENT=Development` (so any auth cookie isn't `Secure` and works over http).
- [ ] A top-level `README.md` documents run steps + every env var (§8).
- [ ] CI workflow builds + tests both projects on PRs (recommended default); CD is optional and completed by the infra owner. A local-only tool can skip both.
- [ ] `<tool>/` is a git repo: `git init` and write `.gitignore` **before** the first `dotnet build` / `npm install`, so `bin/`, `obj/`, and `node_modules/` are never staged. Leave committing and pushing to the user — don't commit unasked.
- [ ] `.gitignore` — start from `dotnet new gitignore` and append the frontend and terraform entries rather than hand-maintaining a list. It must cover `bin/ obj/ TestResults/ *.user .vs/ node_modules/ dist/ coverage/ .terraform/ *.tfstate* **/terraform.tfvars` and **all three env forms**: `**/.env`, `**/.env.local`, `**/.env.*.local`. `**/.env` alone does **not** match `.env.local`, which is Vite's documented place for local secrets and so the likeliest accidental commit in the whole layout — verify with `git check-ignore -q <tool>-app/.env.local`. Do **not** ignore `.terraform.lock.hcl`; that one is meant to be committed so provider versions are pinned for everyone. Never commit sample data with personal info (names, IBANs, etc.).
- [ ] `npm run lint` passes and runs in CI (§7.1). A linter the generated repo ships but nobody runs is a linter that will be red the first time someone tries.
- [ ] Verify before handing off: `dotnet build`, `dotnet test`, `npm run build`, `npm test`, and a local smoke test (login too, if auth).
- [ ] Dependency check before handover: `dotnet list package --vulnerable --include-transitive` + `npm audit`; bump/pin anything flagged — **except** the one below.
- [ ] `Microsoft.OpenApi` will be flagged (transitively, via the template's `Microsoft.AspNetCore.OpenApi`). **Defer it, and don't try to pin your way out:** an explicit `Microsoft.OpenApi` reference resolves to a 3.x that breaks the build outright — `error CS0200: Property or indexer 'IOpenApiMediaType.Example' cannot be assigned to` from ASP.NET's OpenAPI source generator. It has to wait for `Microsoft.AspNetCore.OpenApi` to take a patched 2.x. Deferring is safe because the doc is **dev-only**: `MapOpenApi` sits inside the `IsDevelopment()` guard, so it isn't exposed in production.
