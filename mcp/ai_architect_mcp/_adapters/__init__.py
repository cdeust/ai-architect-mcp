"""Infrastructure adapters.

Concrete implementations of port interfaces defined in ports.py.
Each adapter wraps a specific external system (Git, Xcode, GitHub,
filesystem) and implements the corresponding port protocol.

Adapters are injected at the composition root. Stage logic never
imports adapters directly — only port interfaces.
"""
