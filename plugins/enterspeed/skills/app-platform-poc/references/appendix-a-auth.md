## Appendix A — Authentication & admin area (optional)

> One of the three files that make up the **app + platform blueprint**. Read
> `app-platform-blueprint.md` (the core document) first — this is the drop-in auth appendix it
> refers to, and every `§n` reference below points into that file. Apply
> `appendix-b-database.md` before this one.

**Add this only if the tool needs a login and/or an admin area.** It gives username/password
login for a fixed set of seeded users, admin-gated endpoints, and an auth-guarded SPA — a custom
BCrypt + JWT-in-httpOnly-cookie setup (not ASP.NET Identity). If the tool doesn't need auth,
ignore this appendix entirely.

> Auth uses the database (a `Users` table), so **apply Appendix B (Database) first** — the
> `Users` table, connection string, and admin seeding build on the `ApplicationDbContext`,
> `ConnectionStrings`, and `InitializeDatabaseAsync` from that appendix.

**What to adjust vs. keep verbatim.** The cryptographic/cookie wiring — BCrypt, JWT signing, the
httpOnly `SameSite=Strict` cookie, and token validation — is security-sensitive; **copy it
verbatim, don't reinvent it per tool.** What legitimately varies:

- **Roles** — ships with `Admin`/`User` + the `AdminOnly` policy. Add more roles + policies, or if
  the tool has no admin/user distinction, drop the split and gate everything with plain `[Authorize]`.
- **Seeded users** — 0–2 admins from `Seeding:Admin{n}*` config (widen the loop for more), or seed
  none and add users only via the `create-user` endpoint.
- **`create-user` endpoint** — keep it (admins add users in-app) or remove it for a fixed user set.
- **Token lifetime** — `JwtSettings:ExpirationMinutes` (default 60); add a refresh endpoint if you
  need long-lived sessions.
- **Login method** — this is deliberately the *simple* seeded username/password approach. Org-wide
  SSO / Entra ID / an external IdP is a different mechanism and **out of scope** here (the SPA-guard
  and `[Authorize]` patterns still apply if you swap it in later).

### A.1 Extra backend packages

Unpinned on purpose — the SDK resolves the newest version compatible with the TFM (see core §1,
"Versions"):

```bash
dotnet add "$P" package BCrypt.Net-Next
dotnet add "$P" package Microsoft.AspNetCore.Authentication.JwtBearer
dotnet add "$P" package System.IdentityModel.Tokens.Jwt
```

`JwtBearer` must match the SDK's major (`10.x` on .NET 10). The other two run on **their own release
lines** — `BCrypt.Net-Next` and the `System.IdentityModel.*` / `Microsoft.IdentityModel.*` family
version independently of ASP.NET, so don't try to force them to the SDK's number. If the two
IdentityModel families disagree with each other, align *those* and leave ASP.NET alone.

### A.2 `Domain/Common/User.cs`
```csharp
namespace AppTemplate.Platform.Domain.Common;

public class User
{
    public string Id { get; set; } = null!;
    public string Username { get; set; } = null!;
    public string Email { get; set; } = null!;
    public string PasswordHash { get; set; } = null!;
    public string Role { get; set; } = "User";          // "Admin" or "User"
    public bool IsActive { get; set; } = true;
    public DateTimeOffset CreatedAt { get; set; }
    public DateTimeOffset? LastLoginAt { get; set; }
}
```

### A.3 `Security/JwtTokenProvider.cs`

> **Key constraint (both here and in the JWT bearer setup in A.7):** the key is read with
> `Encoding.ASCII`, and HS256 needs at least a 256-bit key — so `JwtSettings:Key` must be
> **ASCII-only and ≥ 32 characters**. Non-ASCII characters are silently mangled by `ASCII.GetBytes`,
> and a short key throws at signing time. §10 asks the infra owner for a 64-char random string;
> generate the dev key the same way, just don't reuse it.

```csharp
using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using Microsoft.IdentityModel.Tokens;

namespace AppTemplate.Platform.Security;

public interface IJwtTokenProvider
{
    string GenerateToken(string userId, string username, string email, bool isAdmin);
    int GetTokenExpirationSeconds();

    // Nothing in this appendix calls this — it's the one piece a refresh endpoint needs (verify the
    // signature, issuer and audience, but accept an expired token so you can mint a new one). Keep it
    // if you're adding refresh (see "Token lifetime" above); delete it if you're not, rather than
    // leaving an unused path into token validation.
    ClaimsPrincipal? ValidateTokenIgnoringExpiry(string token);
}

public class JwtTokenProvider : IJwtTokenProvider
{
    private readonly IConfiguration _configuration;
    public JwtTokenProvider(IConfiguration configuration) => _configuration = configuration;

    public string GenerateToken(string userId, string username, string email, bool isAdmin)
    {
        var s = _configuration.GetSection("JwtSettings");
        var key = Encoding.ASCII.GetBytes(s["Key"] ?? throw new InvalidOperationException("JWT Key missing"));
        var claims = new List<Claim>
        {
            new(ClaimTypes.NameIdentifier, userId),
            new("sub", userId),
            new("preferred_username", username),
            new("email", email),
            new(ClaimTypes.Name, username),
        };
        if (isAdmin) claims.Add(new Claim("role", "Admin"));

        var descriptor = new SecurityTokenDescriptor
        {
            Subject = new ClaimsIdentity(claims),
            Expires = DateTime.UtcNow.AddMinutes(int.Parse(s["ExpirationMinutes"] ?? "60")),
            Issuer = s["Issuer"],
            Audience = s["Audience"],
            SigningCredentials = new SigningCredentials(new SymmetricSecurityKey(key), SecurityAlgorithms.HmacSha256Signature),
        };
        var handler = new JwtSecurityTokenHandler();
        return handler.WriteToken(handler.CreateToken(descriptor));
    }

    public int GetTokenExpirationSeconds()
        => int.Parse(_configuration.GetSection("JwtSettings")["ExpirationMinutes"] ?? "60") * 60;

    public ClaimsPrincipal? ValidateTokenIgnoringExpiry(string token)
    {
        var s = _configuration.GetSection("JwtSettings");
        var key = Encoding.ASCII.GetBytes(s["Key"] ?? throw new InvalidOperationException("JWT Key missing"));
        var handler = new JwtSecurityTokenHandler { MapInboundClaims = false };
        try
        {
            return handler.ValidateToken(token, new TokenValidationParameters
            {
                ValidateIssuerSigningKey = true,
                IssuerSigningKey = new SymmetricSecurityKey(key),
                ValidateIssuer = true, ValidIssuer = s["Issuer"],
                ValidateAudience = true, ValidAudience = s["Audience"],
                ValidateLifetime = false, RoleClaimType = "role",
            }, out _);
        }
        catch (Exception ex) when (ex is SecurityTokenException or ArgumentException) { return null; }
    }
}
```

### A.4 `Security/AuthenticationService.cs`
```csharp
using AppTemplate.Platform.Domain.Common;
using AppTemplate.Platform.Infrastructure.Persistence;
using Microsoft.EntityFrameworkCore;

namespace AppTemplate.Platform.Security;

public interface IAuthenticationService
{
    Task<User?> AuthenticateAsync(string username, string password);
    Task<User?> CreateUserAsync(string username, string email, string password, string role = "User");
}

public class AuthenticationService : IAuthenticationService
{
    private readonly ApplicationDbContext _db;
    public AuthenticationService(ApplicationDbContext db) => _db = db;

    public async Task<User?> AuthenticateAsync(string username, string password)
    {
        if (string.IsNullOrWhiteSpace(username) || string.IsNullOrWhiteSpace(password)) return null;
        var user = await _db.Users.FirstOrDefaultAsync(u => u.Username == username);
        if (user is null || !user.IsActive) return null;
        if (!BCrypt.Net.BCrypt.Verify(password, user.PasswordHash)) return null;
        user.LastLoginAt = DateTimeOffset.UtcNow;
        await _db.SaveChangesAsync();
        return user;
    }

    public async Task<User?> CreateUserAsync(string username, string email, string password, string role = "User")
    {
        if (string.IsNullOrWhiteSpace(username) || string.IsNullOrWhiteSpace(email) || string.IsNullOrWhiteSpace(password)) return null;
        if (await _db.Users.AnyAsync(u => u.Username == username || u.Email == email)) return null;
        var user = new User
        {
            Id = Guid.NewGuid().ToString(), Username = username, Email = email,
            PasswordHash = BCrypt.Net.BCrypt.HashPassword(password),
            Role = role, IsActive = true, CreatedAt = DateTimeOffset.UtcNow,
        };
        _db.Users.Add(user);
        await _db.SaveChangesAsync();
        return user;
    }
}
```

### A.5 `Presentation/Controllers/AuthController.cs` — the cookie logic is the important bit
```csharp
using System.ComponentModel.DataAnnotations;
using AppTemplate.Platform.Security;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace AppTemplate.Platform.Presentation.Controllers;

[ApiController]
[Route("api/auth")]              // spelled out, not [controller] — keeps the URL lowercase (§6.5)
public class AuthController : ControllerBase
{
    private readonly IAuthenticationService _auth;
    private readonly IJwtTokenProvider _jwt;
    private readonly IWebHostEnvironment _env;

    public AuthController(IAuthenticationService auth, IJwtTokenProvider jwt, IWebHostEnvironment env)
    { _auth = auth; _jwt = jwt; _env = env; }

    private void AppendCookie(string token, DateTimeOffset expires) =>
        Response.Cookies.Append("authToken", token, new CookieOptions
        {
            HttpOnly = true,
            Secure = !_env.IsDevelopment(),   // HTTPS-only in prod; off locally so http works
            SameSite = SameSiteMode.Strict,
            Expires = expires,
        });

    [HttpPost("login")]
    public async Task<IActionResult> Login([FromBody] LoginRequest r)
    {
        var user = await _auth.AuthenticateAsync(r.Username, r.Password);
        if (user is null) return Unauthorized(new { error = "Invalid credentials" });
        var token = _jwt.GenerateToken(user.Id, user.Username, user.Email, user.Role == "Admin");
        var expiresAt = DateTimeOffset.UtcNow.AddSeconds(_jwt.GetTokenExpirationSeconds());
        AppendCookie(token, expiresAt);
        return Ok(new { tokenExpiresAt = expiresAt.ToUnixTimeMilliseconds(),
            user = new { id = user.Id, username = user.Username, email = user.Email, role = user.Role } });
    }

    // AllowAnonymous on purpose: with [Authorize], an expired or invalid token gets a 401 here and
    // the stale cookie is never cleared. Clearing a cookie needs no identity.
    [HttpPost("logout")]
    [AllowAnonymous]
    public IActionResult Logout() { AppendCookie("", DateTimeOffset.UnixEpoch); return Ok(); }

    [HttpGet("me")]
    [Authorize]
    public IActionResult Me() => Ok(new
    {
        id = User.FindFirst("sub")?.Value,
        username = User.FindFirst("preferred_username")?.Value,
        email = User.FindFirst("email")?.Value,
        role = User.IsInRole("Admin") ? "Admin" : "User",
    });

    [HttpPost("create-user")]
    [Authorize(Policy = "AdminOnly")]
    public async Task<IActionResult> CreateUser([FromBody] CreateUserRequest r)
    {
        if ((r.Password?.Length ?? 0) < 8) return BadRequest(new { error = "Password must be ≥ 8 chars" });
        var u = await _auth.CreateUserAsync(r.Username, r.Email, r.Password!, r.Role ?? "User");
        return u is null ? BadRequest(new { error = "Username or email already exists" })
            : Ok(new { id = u.Id, username = u.Username, role = u.Role });
    }
}

public class LoginRequest { [Required] public string Username { get; set; } = null!; [Required] public string Password { get; set; } = null!; }
public class CreateUserRequest { [Required] public string Username { get; set; } = null!; [Required][EmailAddress] public string Email { get; set; } = null!; [Required] public string Password { get; set; } = null!; public string? Role { get; set; } }
```

### A.6 `Infrastructure/Persistence/UserSeeder.cs` — idempotent; seeds up to 2 admins from config
```csharp
using AppTemplate.Platform.Domain.Common;
using Microsoft.EntityFrameworkCore;

namespace AppTemplate.Platform.Infrastructure.Persistence;

public static class UserSeeder
{
    public record AdminSeed(string Username, string? Email, string Password);

    public static async Task SeedAsync(ApplicationDbContext db, ILogger logger, IReadOnlyList<AdminSeed> admins)
    {
        if (await db.Users.AnyAsync()) { logger.LogInformation("Users exist — skip seeding."); return; }
        if (admins.Count == 0) { logger.LogWarning("No Seeding:Admin{n}* config — nobody can log in yet."); return; }
        var i = 1;
        foreach (var a in admins)
        {
            db.Users.Add(new User
            {
                Id = $"user-admin-{i:000}", Username = a.Username,
                Email = string.IsNullOrWhiteSpace(a.Email) ? $"{a.Username}@app-template.local" : a.Email,
                PasswordHash = BCrypt.Net.BCrypt.HashPassword(a.Password),
                Role = "Admin", IsActive = true, CreatedAt = DateTimeOffset.UtcNow,
            });
            i++;
        }
        await db.SaveChangesAsync();
        // Say who was created — silence here means a hand-over reader has no idea which accounts exist.
        logger.LogInformation("Seeded {Count} admin account(s): {Usernames}", admins.Count, string.Join(", ", admins.Select(a => a.Username)));
    }
}
```

### A.7 Wire it into the shared files

**`ApplicationDbContext.cs`** — add the Users table:
```csharp
public DbSet<User> Users => Set<User>();   // + `using AppTemplate.Platform.Domain.Common;`
// inside OnModelCreating:
var user = b.Entity<User>();
user.HasKey(u => u.Id);
user.HasIndex(u => u.Username).IsUnique();
user.HasIndex(u => u.Email).IsUnique();
user.Property(u => u.Username).HasMaxLength(256).IsRequired();
user.Property(u => u.Email).HasMaxLength(256).IsRequired();
user.Property(u => u.PasswordHash).HasMaxLength(512).IsRequired();
user.Property(u => u.Role).HasMaxLength(50).IsRequired().HasDefaultValue("User");
```

**`ServiceCollectionExtensions.cs`** — in `AddApplicationServices`, after the DbContext/CORS:
```csharp
var jwt = config.GetSection("JwtSettings");
var key = Encoding.ASCII.GetBytes(jwt["Key"] ?? throw new InvalidOperationException("JwtSettings:Key missing"));
services.AddAuthentication(x => { x.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme; x.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme; })
    .AddJwtBearer(x =>
    {
        x.RequireHttpsMetadata = !env.IsDevelopment();
        x.MapInboundClaims = false;
        x.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuerSigningKey = true, IssuerSigningKey = new SymmetricSecurityKey(key),
            ValidateIssuer = true, ValidIssuer = jwt["Issuer"],
            ValidateAudience = true, ValidAudience = jwt["Audience"],
            ValidateLifetime = true, ClockSkew = TimeSpan.FromSeconds(30), RoleClaimType = "role",
        };
        // Read the JWT from the httpOnly cookie, not the Authorization header:
        x.Events = new JwtBearerEvents { OnMessageReceived = ctx => { ctx.Token = ctx.Request.Cookies["authToken"]; return Task.CompletedTask; } };
    });
services.AddAuthorizationBuilder()
    .AddPolicy("AdminOnly", p => { p.RequireAuthenticatedUser(); p.RequireRole("Admin"); })
    .AddPolicy("AnyAuthenticated", p => p.RequireAuthenticatedUser());
services.AddScoped<IAuthenticationService, AuthenticationService>();
services.AddScoped<IJwtTokenProvider, JwtTokenProvider>();
```
(+ `using` for `System.Text`, `AppTemplate.Platform.Security`, `Microsoft.AspNetCore.Authentication.JwtBearer`, `Microsoft.IdentityModel.Tokens`.)
In `UseApplicationMiddleware`, add `app.UseAuthentication(); app.UseAuthorization();` before `MapControllers()`.
In `InitializeDatabaseAsync`, after `MigrateAsync()`, seed the admins:
```csharp
var config = scope.ServiceProvider.GetRequiredService<IConfiguration>();
var logger = scope.ServiceProvider.GetRequiredService<ILogger<ApplicationDbContext>>();
var seeding = config.GetSection("Seeding");
var admins = new List<UserSeeder.AdminSeed>();
for (var i = 1; i <= 2; i++)
{
    var u = seeding[$"Admin{i}Username"]; var p = seeding[$"Admin{i}Password"];
    if (!string.IsNullOrWhiteSpace(u) && !string.IsNullOrWhiteSpace(p))
        admins.Add(new(u, seeding[$"Admin{i}Email"], p));
}
await UserSeeder.SeedAsync(db, logger, admins);
```

**`appsettings.json`** — add:
```jsonc
"JwtSettings": { "Issuer": "app-template", "Audience": "app-template-users", "ExpirationMinutes": 60, "Key": "" },
"Seeding": { "Admin1Username": "", "Admin1Password": "", "Admin1Email": "", "Admin2Username": "", "Admin2Password": "" }
```
**`appsettings.Development.json`** — add a dev `JwtSettings:Key` and a seeded admin:
```jsonc
"JwtSettings": { "Key": "dev-only-insecure-signing-key-change-me-0123456789" },
"Seeding": { "Admin1Username": "admin", "Admin1Email": "admin@app-template.local", "Admin1Password": "admin-password" }
```
**`docker-compose.yml`** — add to the `api` service `environment:`
```yaml
JwtSettings__Key: "local-dev-only-change-me-0123456789abcdef0123456789"
Seeding__Admin1Username: "admin"
Seeding__Admin1Password: "admin-password"
Seeding__Admin1Email: "admin@app-template.local"
```
Then create the migration for the `Users` table and build:

- **Greenfield, auth decided up front (the normal case):** you haven't created any migration yet, so
  just do B.7 now — a single `dotnet ef migrations add InitialCreate` that already includes `Users`.
- **Adding auth to a tool that already has migrations:** `dotnet ef migrations add AddUsers`.

Either way, finish with `dotnet build "$P"`.

### A.8 Protect endpoints
Add `[Authorize]` to feature controllers (or `[Authorize(Policy = "AdminOnly")]` for admin-only
ones like a settings/keys screen).

### A.9 Frontend auth shell
**Replace `src/lib/api/client.ts`** with the version that redirects to login on 401/403:
```ts
import axios from "axios";
import type { AxiosRequestConfig } from "axios";
import { API_BASE } from "@/lib/config";

export const http = axios.create({ baseURL: API_BASE, withCredentials: true });

http.interceptors.response.use((r) => r, (error) => {
  const status = error?.response?.status;
  const url: string = error?.config?.url ?? "";
  if ((status === 401 || status === 403) && !url.includes("/auth/login") && !url.includes("/auth/me"))
    globalThis.dispatchEvent(new Event("auth:logout"));
  return Promise.reject(error);
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
```
**`src/lib/auth/types.ts`**
```ts
export interface User { id: string; username: string; email: string; role: "Admin" | "User"; }
```
The context lives in **two files on purpose**. A single `UserContext.tsx` exporting both the provider
component and the `useUser` hook trips the fast-refresh lint rule in every current template — oxlint
calls it `react(only-export-components)`, ESLint calls it
`react-refresh/only-export-components` — and suppressing it needs a different directive per linter.
Splitting the non-component parts out satisfies both with no suppression comment at all.

**`src/lib/auth/userContext.ts`** — context + hook, no components:
```ts
import { createContext, useContext } from "react";
import type { User } from "@/lib/auth/types";

export interface UserCtx {
  user: User | null;
  isRestoring: boolean;
  login: (u: User) => void;
  logout: () => void;
}

export const UserContext = createContext<UserCtx | undefined>(undefined);

export function useUser() {
  const c = useContext(UserContext);
  if (!c) throw new Error("useUser must be used within UserProvider");
  return c;
}
```
**`src/lib/auth/UserProvider.tsx`** — the component:
```tsx
import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { apiGet, apiPost } from "@/lib/api/client";
import type { User } from "@/lib/auth/types";
import { UserContext } from "@/lib/auth/userContext";
import type { UserCtx } from "@/lib/auth/userContext";

export function UserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isRestoring, setIsRestoring] = useState(true);

  useEffect(() => {
    apiGet<User>("/api/auth/me").then((r) => setUser(r.data)).catch(() => {}).finally(() => setIsRestoring(false));
  }, []);

  useEffect(() => {
    const onLogout = () => setUser(null);
    globalThis.addEventListener("auth:logout", onLogout);
    return () => globalThis.removeEventListener("auth:logout", onLogout);
  }, []);

  const value = useMemo<UserCtx>(() => ({
    user, isRestoring, login: (u) => setUser(u),
    logout: () => { setUser(null); apiPost("/api/auth/logout").catch(() => {}); },
  }), [user, isRestoring]);

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}
```
**`src/api/authApi.ts`**
```ts
import { apiPost } from "@/lib/api/client";
import type { User } from "@/lib/auth/types";
export const loginApi = (username: string, password: string) =>
  apiPost<{ tokenExpiresAt: number; user: User }>("/api/auth/login", { username, password }).then((r) => r.data);
```

> **Write auth URLs lowercase — `/api/auth/...` — everywhere.** ASP.NET routing is
> case-insensitive, so `/api/Auth/login` reaches the controller either way, but the interceptor
> above matches on `url.includes("/auth/login")`, which is a **case-sensitive** string compare. Get
> it wrong and a rejected login also fires `auth:logout`. Same for `/api/auth/me` and
> `/api/auth/logout`.

**`src/components/ProtectedRoute.tsx`** — the restore race is easy to get wrong (checking `user`
before `/auth/me` resolves bounces an authenticated user to the login page on every refresh), so
take this as written:
```tsx
import { Navigate } from "react-router-dom";
import type { ReactNode } from "react";
import { useUser } from "@/lib/auth/userContext";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, isRestoring } = useUser();
  if (isRestoring) return <div className="p-8 text-slate-500">Loading…</div>;  // never decide before restore finishes
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
```
**`src/pages/LoginPage.tsx`** — username/password form → `loginApi` → `login(user)` → navigate `/`.
Show failures via `errorMessage(e)` (the API returns `{ error: "Invalid credentials" }`), and if an
already-authenticated user lands here, redirect them to `/` rather than showing the form again.
**`Layout.tsx`** — add the current user + a logout button (`useUser` from `@/lib/auth/userContext`).
**`router.tsx`** — add a public `/login` route; wrap the app routes in `<ProtectedRoute>`, e.g.
`{ path: "/", element: <ProtectedRoute><Layout /></ProtectedRoute>, children: [...] }`.
**`App.tsx`** — wrap `<RouterProvider>` in `<UserProvider>` (imported from
`@/lib/auth/UserProvider`), so the provider sits outside the router.

### A.10 Deploy note
With auth, mind the **same-site cookie** gotcha in §10 (SWA and Container App are different
sites). Document the seeded login credentials and the `JwtSettings`/`Seeding` env vars in the
README (§8).
