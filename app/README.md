# App Layer (Reference Placeholder)

The Mac app lives in the `ai-architect` repository (separate). It is the display layer only.

The SwiftUI app:

- Spawns `claude` CLI as a subprocess
- Owns the SwiftData schema for local persistence
- Displays pipeline status and results
- Does not contain engine logic

No `.xcodeproj` or `.xcworkspace` belongs in this repository. The MCP server is the engine. The app is one of several clients (Mac app, Claude Code terminal, Xcode MCP bridge, GitHub Actions).
