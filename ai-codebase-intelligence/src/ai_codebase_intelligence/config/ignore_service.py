from __future__ import annotations

DEFAULT_IGNORE_LIST: frozenset[str] = frozenset({
    # Version Control
    ".git",
    ".svn",
    ".hg",
    ".bzr",
    # IDEs & Editors
    ".idea",
    ".vscode",
    ".vs",
    ".eclipse",
    ".settings",
    ".DS_Store",
    "Thumbs.db",
    # Dependencies
    "node_modules",
    "bower_components",
    "jspm_packages",
    "vendor",  # PHP/Go
    # 'packages' removed - commonly used for monorepo source code (lerna, pnpm, yarn workspaces)
    "venv",
    ".venv",
    "env",
    ".env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "site-packages",
    ".tox",
    "eggs",
    ".eggs",
    "lib64",
    "parts",
    "sdist",
    "wheels",
    # Build Outputs
    "dist",
    "build",
    "out",
    "output",
    "bin",
    "obj",
    "target",  # Java/Rust
    ".next",
    ".nuxt",
    ".output",
    ".vercel",
    ".netlify",
    ".serverless",
    "_build",
    "public/build",
    ".parcel-cache",
    ".turbo",
    ".svelte-kit",
    # Test & Coverage
    "coverage",
    ".nyc_output",
    "htmlcov",
    ".coverage",
    "__tests__",  # Often just test files
    "__mocks__",
    ".jest",
    # Logs & Temp
    "logs",
    "log",
    "tmp",
    "temp",
    "cache",
    ".cache",
    ".tmp",
    ".temp",
    # Generated/Compiled
    ".generated",
    "generated",
    "auto-generated",
    ".terraform",
    ".serverless",
    # Documentation (optional - might want to keep)
    # "docs",
    # "documentation",
    # Misc
    ".husky",
    ".github",  # GitHub config, not code
    ".circleci",
    ".gitlab",
    "fixtures",  # Test fixtures
    "snapshots",  # Jest snapshots
    "__snapshots__",
    # Pipeline worktrees & state — never index these. Prior YOLO runs
    # created N copies of the source tree under .pipeline-worktrees/,
    # inflating impact analysis blast radius ~Nx.
    ".pipeline-worktrees",
    ".pipeline-worktree",
    ".pipeline",
    "_pipeline",
})

IGNORED_EXTENSIONS: frozenset[str] = frozenset({
    # Images
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp", ".bmp", ".tiff", ".tif",
    ".psd", ".ai", ".sketch", ".fig", ".xd",
    # Archives
    ".zip", ".tar", ".gz", ".rar", ".7z", ".bz2", ".xz", ".tgz",
    # Binary/Compiled
    ".exe", ".dll", ".so", ".dylib", ".a", ".lib", ".o", ".obj",
    ".class", ".jar", ".war", ".ear",
    ".pyc", ".pyo", ".pyd",
    ".beam",  # Erlang
    ".wasm",  # WebAssembly
    ".node",  # Native Node addons
    # Documents
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".odt", ".ods", ".odp",
    # Media
    ".mp4", ".mp3", ".wav", ".mov", ".avi", ".mkv", ".flv", ".wmv",
    ".ogg", ".webm", ".flac", ".aac", ".m4a",
    # Fonts
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    # Databases
    ".db", ".sqlite", ".sqlite3", ".mdb", ".accdb",
    # Minified/Bundled files
    ".min.js", ".min.css", ".bundle.js", ".chunk.js",
    # Source maps (debug files, not source)
    ".map",
    # Lock files (handled separately, but also here)
    ".lock",
    # Certificates & Keys (security - don't index!)
    ".pem", ".key", ".crt", ".cer", ".p12", ".pfx",
    # Data files (often large/binary)
    ".csv", ".tsv", ".parquet", ".avro", ".feather",
    ".npy", ".npz", ".pkl", ".pickle", ".h5", ".hdf5",
    # Misc binary
    ".bin", ".dat", ".data", ".raw",
    ".iso", ".img", ".dmg",
})

# Files to ignore by exact name
IGNORED_FILES: frozenset[str] = frozenset({
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "composer.lock",
    "Gemfile.lock",
    "poetry.lock",
    "Cargo.lock",
    "go.sum",
    ".gitignore",
    ".gitattributes",
    ".npmrc",
    ".yarnrc",
    ".editorconfig",
    ".prettierrc",
    ".prettierignore",
    ".eslintignore",
    ".dockerignore",
    "Thumbs.db",
    ".DS_Store",
    "LICENSE",
    "LICENSE.md",
    "LICENSE.txt",
    "CHANGELOG.md",
    "CHANGELOG",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".env.test",
    ".env.example",
})


def should_ignore_path(file_path: str) -> bool:
    normalized_path = file_path.replace("\\", "/")
    parts = normalized_path.split("/")
    file_name = parts[-1]
    file_name_lower = file_name.lower()

    # Check if any path segment is in ignore list
    for part in parts:
        if part in DEFAULT_IGNORE_LIST:
            return True

    # Check exact filename matches
    if file_name in IGNORED_FILES or file_name_lower in IGNORED_FILES:
        return True

    # Check extension
    last_dot_index = file_name_lower.rfind(".")
    if last_dot_index != -1:
        ext = file_name_lower[last_dot_index:]
        if ext in IGNORED_EXTENSIONS:
            return True
        # Handle compound extensions like .min.js, .bundle.js
        second_last_dot = file_name_lower.rfind(".", 0, last_dot_index)
        if second_last_dot != -1:
            compound_ext = file_name_lower[second_last_dot:]
            if compound_ext in IGNORED_EXTENSIONS:
                return True

    # Ignore hidden files (starting with .)
    if file_name.startswith(".") and file_name != ".":
        # But allow some important config files
        # Actually, let's NOT ignore all dot files - many are important configs
        # Just rely on the explicit lists above
        pass

    # Ignore files that look like generated/bundled code
    if (".bundle." in file_name_lower
            or ".chunk." in file_name_lower
            or ".generated." in file_name_lower
            or file_name_lower.endswith(".d.ts")):  # TypeScript declaration files
        return True

    return False
