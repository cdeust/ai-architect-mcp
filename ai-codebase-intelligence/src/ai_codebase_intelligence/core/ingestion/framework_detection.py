from __future__ import annotations

from typing import Any


def detect_framework_from_path(file_path: str) -> dict[str, Any] | None:
    p = file_path.lower().replace("\\", "/")
    if not p.startswith("/"):
        p = "/" + p
    # Next.js Pages Router
    if "/pages/" in p and "/_" not in p and "/api/" not in p:
        if p.endswith((".tsx", ".ts", ".jsx", ".js")):
            return {"framework": "nextjs-pages", "entryPointMultiplier": 3.0, "reason": "nextjs-page"}
    if "/app/" in p and (p.endswith("page.tsx") or p.endswith("page.ts") or p.endswith("page.jsx") or p.endswith("page.js")):
        return {"framework": "nextjs-app", "entryPointMultiplier": 3.0, "reason": "nextjs-app-page"}
    if "/pages/api/" in p or ("/app/" in p and "/api/" in p and p.endswith("route.ts")):
        return {"framework": "nextjs-api", "entryPointMultiplier": 3.0, "reason": "nextjs-api-route"}
    if "/app/" in p and (p.endswith("layout.tsx") or p.endswith("layout.ts")):
        return {"framework": "nextjs-app", "entryPointMultiplier": 2.0, "reason": "nextjs-layout"}
    if "/routes/" in p and p.endswith((".ts", ".js")):
        return {"framework": "express", "entryPointMultiplier": 2.5, "reason": "routes-folder"}
    if "/controllers/" in p and p.endswith((".ts", ".js")):
        return {"framework": "mvc", "entryPointMultiplier": 2.5, "reason": "controllers-folder"}
    if "/handlers/" in p and p.endswith((".ts", ".js")):
        return {"framework": "handlers", "entryPointMultiplier": 2.5, "reason": "handlers-folder"}
    if ("/components/" in p or "/views/" in p) and p.endswith((".tsx", ".jsx")):
        fn = p.rsplit("/", 1)[-1]
        if fn and fn[0].isupper():
            return {"framework": "react", "entryPointMultiplier": 1.5, "reason": "react-component"}
    # Python
    if p.endswith("views.py"):
        return {"framework": "django", "entryPointMultiplier": 3.0, "reason": "django-views"}
    if p.endswith("urls.py"):
        return {"framework": "django", "entryPointMultiplier": 2.0, "reason": "django-urls"}
    if ("/routers/" in p or "/endpoints/" in p or "/routes/" in p) and p.endswith(".py"):
        return {"framework": "fastapi", "entryPointMultiplier": 2.5, "reason": "api-routers"}
    if "/api/" in p and p.endswith(".py") and not p.endswith("__init__.py"):
        return {"framework": "python-api", "entryPointMultiplier": 2.0, "reason": "api-folder"}
    # Java
    if ("/controller/" in p or "/controllers/" in p) and p.endswith(".java"):
        return {"framework": "spring", "entryPointMultiplier": 3.0, "reason": "spring-controller"}
    if p.endswith("controller.java"):
        return {"framework": "spring", "entryPointMultiplier": 3.0, "reason": "spring-controller-file"}
    if ("/service/" in p or "/services/" in p) and p.endswith(".java"):
        return {"framework": "java-service", "entryPointMultiplier": 1.8, "reason": "java-service"}
    # Kotlin
    if ("/controller/" in p or "/controllers/" in p) and p.endswith(".kt"):
        return {"framework": "spring-kotlin", "entryPointMultiplier": 3.0, "reason": "spring-kotlin-controller"}
    if p.endswith("controller.kt"):
        return {"framework": "spring-kotlin", "entryPointMultiplier": 3.0, "reason": "spring-kotlin-controller-file"}
    if "/routes/" in p and p.endswith(".kt"):
        return {"framework": "ktor", "entryPointMultiplier": 2.5, "reason": "ktor-routes"}
    if "/plugins/" in p and p.endswith(".kt"):
        return {"framework": "ktor", "entryPointMultiplier": 2.0, "reason": "ktor-plugin"}
    if p.endswith("routing.kt") or p.endswith("routes.kt"):
        return {"framework": "ktor", "entryPointMultiplier": 2.5, "reason": "ktor-routing-file"}
    if ("/activity/" in p or "/ui/" in p) and p.endswith(".kt"):
        return {"framework": "android-kotlin", "entryPointMultiplier": 2.5, "reason": "android-ui"}
    if p.endswith("activity.kt") or p.endswith("fragment.kt"):
        return {"framework": "android-kotlin", "entryPointMultiplier": 2.5, "reason": "android-component"}
    if p.endswith("/main.kt"):
        return {"framework": "kotlin", "entryPointMultiplier": 3.0, "reason": "kotlin-main"}
    if p.endswith("/application.kt"):
        return {"framework": "kotlin", "entryPointMultiplier": 2.5, "reason": "kotlin-application"}
    # C#
    if "/controllers/" in p and p.endswith(".cs"):
        return {"framework": "aspnet", "entryPointMultiplier": 3.0, "reason": "aspnet-controller"}
    if p.endswith("controller.cs"):
        return {"framework": "aspnet", "entryPointMultiplier": 3.0, "reason": "aspnet-controller-file"}
    if "/pages/" in p and p.endswith(".razor"):
        return {"framework": "blazor", "entryPointMultiplier": 2.5, "reason": "blazor-page"}
    # Go
    if ("/handlers/" in p or "/handler/" in p) and p.endswith(".go"):
        return {"framework": "go-http", "entryPointMultiplier": 2.5, "reason": "go-handlers"}
    if "/routes/" in p and p.endswith(".go"):
        return {"framework": "go-http", "entryPointMultiplier": 2.5, "reason": "go-routes"}
    if "/controllers/" in p and p.endswith(".go"):
        return {"framework": "go-mvc", "entryPointMultiplier": 2.5, "reason": "go-controller"}
    if p.endswith("/main.go"):
        return {"framework": "go", "entryPointMultiplier": 3.0, "reason": "go-main"}
    # Rust
    if ("/handlers/" in p or "/routes/" in p) and p.endswith(".rs"):
        return {"framework": "rust-web", "entryPointMultiplier": 2.5, "reason": "rust-handlers"}
    if p.endswith("/main.rs"):
        return {"framework": "rust", "entryPointMultiplier": 3.0, "reason": "rust-main"}
    if "/bin/" in p and p.endswith(".rs"):
        return {"framework": "rust", "entryPointMultiplier": 2.5, "reason": "rust-bin"}
    # C/C++
    if p.endswith(("/main.c", "/main.cpp", "/main.cc")):
        return {"framework": "c-cpp", "entryPointMultiplier": 3.0, "reason": "c-main"}
    if "/src/" in p and (p.endswith("/app.c") or p.endswith("/app.cpp")):
        return {"framework": "c-cpp", "entryPointMultiplier": 2.5, "reason": "c-app"}
    # PHP/Laravel
    if "/routes/" in p and p.endswith(".php"):
        return {"framework": "laravel", "entryPointMultiplier": 3.0, "reason": "laravel-routes"}
    if ("/http/controllers/" in p or "/controllers/" in p) and p.endswith(".php"):
        return {"framework": "laravel", "entryPointMultiplier": 3.0, "reason": "laravel-controller"}
    if p.endswith("controller.php"):
        return {"framework": "laravel", "entryPointMultiplier": 3.0, "reason": "laravel-controller-file"}
    if ("/console/commands/" in p or "/commands/" in p) and p.endswith(".php"):
        return {"framework": "laravel", "entryPointMultiplier": 2.5, "reason": "laravel-command"}
    if "/jobs/" in p and p.endswith(".php"):
        return {"framework": "laravel", "entryPointMultiplier": 2.5, "reason": "laravel-job"}
    if "/listeners/" in p and p.endswith(".php"):
        return {"framework": "laravel", "entryPointMultiplier": 2.5, "reason": "laravel-listener"}
    if "/http/middleware/" in p and p.endswith(".php"):
        return {"framework": "laravel", "entryPointMultiplier": 2.5, "reason": "laravel-middleware"}
    if "/providers/" in p and p.endswith(".php"):
        return {"framework": "laravel", "entryPointMultiplier": 1.8, "reason": "laravel-provider"}
    if "/policies/" in p and p.endswith(".php"):
        return {"framework": "laravel", "entryPointMultiplier": 2.0, "reason": "laravel-policy"}
    if "/models/" in p and p.endswith(".php"):
        return {"framework": "laravel", "entryPointMultiplier": 1.5, "reason": "laravel-model"}
    if "/services/" in p and p.endswith(".php"):
        return {"framework": "laravel", "entryPointMultiplier": 1.8, "reason": "laravel-service"}
    if "/repositories/" in p and p.endswith(".php"):
        return {"framework": "laravel", "entryPointMultiplier": 1.5, "reason": "laravel-repository"}
    # Swift/iOS
    if p.endswith(("/appdelegate.swift", "/scenedelegate.swift", "/app.swift")):
        return {"framework": "ios", "entryPointMultiplier": 3.0, "reason": "ios-app-entry"}
    if p.endswith("app.swift") and "/sources/" in p:
        return {"framework": "swiftui", "entryPointMultiplier": 3.0, "reason": "swiftui-app"}
    if ("/viewcontrollers/" in p or "/controllers/" in p or "/screens/" in p) and p.endswith(".swift"):
        return {"framework": "uikit", "entryPointMultiplier": 2.5, "reason": "uikit-viewcontroller"}
    if p.endswith("viewcontroller.swift") or p.endswith("vc.swift"):
        return {"framework": "uikit", "entryPointMultiplier": 2.5, "reason": "uikit-viewcontroller-file"}
    if "/coordinators/" in p and p.endswith(".swift"):
        return {"framework": "ios-coordinator", "entryPointMultiplier": 2.5, "reason": "ios-coordinator"}
    if p.endswith("coordinator.swift"):
        return {"framework": "ios-coordinator", "entryPointMultiplier": 2.5, "reason": "ios-coordinator-file"}
    if ("/views/" in p or "/scenes/" in p) and p.endswith(".swift"):
        return {"framework": "swiftui", "entryPointMultiplier": 1.8, "reason": "swiftui-view"}
    if "/services/" in p and p.endswith(".swift"):
        return {"framework": "ios-service", "entryPointMultiplier": 1.8, "reason": "ios-service"}
    if "/router/" in p and p.endswith(".swift"):
        return {"framework": "ios-router", "entryPointMultiplier": 2.0, "reason": "ios-router"}
    # Generic
    if "/api/" in p and (p.endswith("/index.ts") or p.endswith("/index.js") or p.endswith("/__init__.py")):
        return {"framework": "api", "entryPointMultiplier": 1.8, "reason": "api-index"}
    return None


_AST_FRAMEWORK_PATTERNS_BY_LANGUAGE: dict[str, list[dict[str, Any]]] = {
    "javascript": [{"framework": "nestjs", "entryPointMultiplier": 3.2, "reason": "nestjs-decorator", "patterns": ["@controller", "@get", "@post", "@put", "@delete", "@patch"]}],
    "typescript": [{"framework": "nestjs", "entryPointMultiplier": 3.2, "reason": "nestjs-decorator", "patterns": ["@controller", "@get", "@post", "@put", "@delete", "@patch"]}],
    "python": [
        {"framework": "fastapi", "entryPointMultiplier": 3.0, "reason": "fastapi-decorator", "patterns": ["@app.get", "@app.post", "@app.put", "@app.delete", "@router.get"]},
        {"framework": "flask", "entryPointMultiplier": 2.8, "reason": "flask-decorator", "patterns": ["@app.route", "@blueprint.route"]},
    ],
    "java": [
        {"framework": "spring", "entryPointMultiplier": 3.2, "reason": "spring-annotation", "patterns": ["@restcontroller", "@controller", "@getmapping", "@postmapping", "@requestmapping"]},
        {"framework": "jaxrs", "entryPointMultiplier": 3.0, "reason": "jaxrs-annotation", "patterns": ["@path", "@get", "@post", "@put", "@delete"]},
    ],
    "kotlin": [
        {"framework": "spring-kotlin", "entryPointMultiplier": 3.2, "reason": "spring-kotlin-annotation", "patterns": ["@restcontroller", "@controller", "@getmapping", "@postmapping", "@requestmapping"]},
        {"framework": "ktor", "entryPointMultiplier": 2.8, "reason": "ktor-routing", "patterns": ["routing", "embeddedserver", "application.module"]},
        {"framework": "android-kotlin", "entryPointMultiplier": 2.5, "reason": "android-annotation", "patterns": ["@androidentrypoint", "appcompatactivity", "fragment("]},
    ],
    "csharp": [{"framework": "aspnet", "entryPointMultiplier": 3.2, "reason": "aspnet-attribute", "patterns": ["[apicontroller]", "[httpget]", "[httppost]", "[route]"]}],
    "php": [{"framework": "laravel", "entryPointMultiplier": 3.0, "reason": "php-route-attribute", "patterns": ["route::get", "route::post", "route::put", "route::delete", "route::resource", "route::apiresource", "#[route("]}],
}


def detect_framework_from_ast(language: str, definition_text: str) -> dict[str, Any] | None:
    if not language or not definition_text:
        return None
    configs = _AST_FRAMEWORK_PATTERNS_BY_LANGUAGE.get(language.lower())
    if not configs:
        return None
    normalized = definition_text.lower()
    for cfg in configs:
        for pattern in cfg["patterns"]:
            if pattern in normalized:
                return {
                    "framework": cfg["framework"],
                    "entryPointMultiplier": cfg["entryPointMultiplier"],
                    "reason": cfg["reason"],
                }
    return None
