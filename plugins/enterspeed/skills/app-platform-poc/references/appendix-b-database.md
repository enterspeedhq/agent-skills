## Appendix B — Database / persistence (optional)

> One of the three files that make up the **app + platform blueprint**. Read
> `app-platform-blueprint.md` (the core document) first — this is the drop-in persistence appendix
> it refers to, and every `§n` reference below points into that file. If the tool also needs auth,
> apply this appendix first, then `appendix-a-auth.md`.

**Add this only if the tool persists data.** Auth (Appendix A) builds on it — the `Users` table
lives in this database — so if you're adding auth, apply this appendix first. A stateless tool
skips it entirely.

### B.1 Extra backend packages

Unpinned on purpose — the SDK resolves the newest version compatible with the TFM (see core §1,
"Versions"):

```bash
dotnet add "$P" package Microsoft.EntityFrameworkCore
dotnet add "$P" package Microsoft.EntityFrameworkCore.Design
dotnet add "$P" package Microsoft.EntityFrameworkCore.Tools
dotnet add "$P" package Npgsql.EntityFrameworkCore.PostgreSQL
```

Then check the `.csproj`: all four must have landed on the **same major as the SDK** (`10.x` on
.NET 10). If Npgsql lags a major behind EF Core, take Npgsql's newest `10.x` explicitly rather than
downgrading EF — the provider is usually the one that trails.

### B.2 `Infrastructure/Persistence/ApplicationDbContext.cs` + design-time factory
```csharp
using Microsoft.EntityFrameworkCore;

namespace AppTemplate.Platform.Infrastructure.Persistence;

public class ApplicationDbContext : DbContext
{
    public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options) : base(options) { }

    // public DbSet<YourEntity> YourEntities => Set<YourEntity>();

    protected override void OnModelCreating(ModelBuilder b)
    {
        base.OnModelCreating(b);
        // configure your entities here
    }
}
```
```csharp
// ApplicationDbContextFactory.cs — lets `dotnet ef` run without a live DB
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Design;

namespace AppTemplate.Platform.Infrastructure.Persistence;

public class ApplicationDbContextFactory : IDesignTimeDbContextFactory<ApplicationDbContext>
{
    public ApplicationDbContext CreateDbContext(string[] args) =>
        new(new DbContextOptionsBuilder<ApplicationDbContext>()
            .UseNpgsql("Host=localhost;Port=5432;Database=AppTemplate;Username=postgres;Password=postgres").Options);
}
```

### B.3 Wire it into `ServiceCollectionExtensions.cs`
Add the usings `AppTemplate.Platform.Infrastructure.Persistence` and `Microsoft.EntityFrameworkCore`,
then register the context at the top of `AddApplicationServices`:
```csharp
var cs = config.GetConnectionString("DefaultConnection") ?? throw new InvalidOperationException("ConnectionStrings:DefaultConnection missing");
services.AddDbContext<ApplicationDbContext>(o => o.UseNpgsql(cs));
```
and add the migrate-on-boot helper **to the same `ServiceCollectionExtensions` class** — an
extension on `WebApplication`, sitting next to `UseApplicationMiddleware` (auth extends this to also
seed admins — Appendix A):
```csharp
public static async Task InitializeDatabaseAsync(this WebApplication app)
{
    using var scope = app.Services.CreateScope();
    var db = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
    await db.Database.MigrateAsync();
}
```

### B.4 `Program.cs`
Add before `app.Run();`:
```csharp
await app.InitializeDatabaseAsync();
```

### B.5 Config additions
`appsettings.json` → add `"ConnectionStrings": { "DefaultConnection": "" }` (real value from env/Key Vault in prod).
`appsettings.Development.json` → add (the port must match the **host** port you publish in B.6, not
the container's 5432):
```jsonc
"ConnectionStrings": { "DefaultConnection": "Host=localhost;Port=5433;Database=AppTemplate;Username=postgres;Password=postgres" }
```

### B.6 `docker-compose.yml` additions
Add a `db` service and point the API at it. Two things here are load-bearing:

**The healthcheck and `service_healthy` condition are required, not decoration.** Plain
`depends_on: [db]` only waits for the container to *start*, so the API boots first, `MigrateAsync()`
can't connect, and the API dies — usually looking like a bug in your code rather than a startup race.

**Publish a tool-specific host port, not 5432.** Every blueprint tool with a database would otherwise
claim the same one, and the second `docker compose up` fails with
`Bind for 0.0.0.0:5432 failed: port is already allocated` — including against a Postgres you
installed natively. Pick a free port per tool (5433, 5434, …), keep the **container** port at 5432
since that's what the API connects to over the compose network, and mirror your choice in
`appsettings.Development.json` (B.5) so the no-Docker `dotnet run` path still reaches the database.

```yaml
services:
  db:
    image: postgres:16
    environment: { POSTGRES_DB: AppTemplate, POSTGRES_USER: postgres, POSTGRES_PASSWORD: postgres }
    ports: ["5433:5432"]        # host:container — pick a free host port per tool
    volumes: ["pgdata:/var/lib/postgresql/data"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d AppTemplate"]
      interval: 5s
      timeout: 5s
      retries: 10
  api:
    depends_on:
      db: { condition: service_healthy }
    environment:
      ConnectionStrings__DefaultConnection: "Host=db;Port=5432;Database=AppTemplate;Username=postgres;Password=postgres"
volumes: { pgdata: {} }
```

### B.7 Migration

Do this **last**, after every entity is in place — including `Users` if the tool has auth (A.7). One
`InitialCreate` covering the whole model beats an `InitialCreate` + `AddUsers` pair on a greenfield
PoC.

```bash
dotnet tool install --global dotnet-ef      # if not present; `dotnet tool update --global dotnet-ef` if it is
dotnet ef migrations add InitialCreate --project "$P" --output-dir Migrations
dotnet build "$P"
```
The design-time factory (B.2) means this works with no database running.

### B.8 Adding entities
Add a `DbSet<T>` to `ApplicationDbContext` and configure it in `OnModelCreating`, then add a
migration (`dotnet ef migrations add <Name>`). Return DTOs from controllers, never the entities
themselves (§4).

> Deployed infra: this is the "PostgreSQL Flexible Server" component + the
> `ConnectionStrings__DefaultConnection` secret in §10.
