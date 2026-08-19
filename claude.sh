#!/bin/bash
# relocate the Claude Code install to local disk
LOCAL=/tmp/$USER/claude-install
mkdir -p "$LOCAL"

# copy the versions + launcher off NFS (cp forces full read, no NFS mmap at runtime)
rsync -a ~/.local/share/claude/ "$LOCAL/claude/"

# point PATH at a local shim
mkdir -p "$LOCAL/bin"
ln -sf "$LOCAL/claude/versions/2.1.173" "$LOCAL/bin/claude"

export PATH="$LOCAL/bin:$PATH"
claude --version
