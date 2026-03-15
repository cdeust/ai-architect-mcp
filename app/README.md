# AI Architect App

macOS app and CLI that composes the Apple Intelligence packages:

- **SwiftData + CloudKit** persistence via `SwiftDataStack`
- **NaturalLanguage** text analysis via `NLTextAnalyzer`
- **Vision** mockup analysis via `FoundationModelsAnalyzer`

Requires macOS 26+ and Swift 6.2.

## Build

```bash
cd app && swift build
```

## Test

```bash
cd app && swift test
```

## CLI

```bash
swift run ai-architect-cli --text "Your text to analyze"
swift run ai-architect-cli --list
```
