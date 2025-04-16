# Package the ml-tutor directory into a zip file, ignoring all files and directories that start with a dot, as well
# as __pycache__ directories.
# Usage: ./package.sh

# Remove the previously created zip file if it exists
if [ -f "obsidian-sync.ankiaddon" ]; then
    rm obsidian-sync.ankiaddon
    echo "Removed existing obsidian-sync.ankiaddon"
fi

# Create a new zip file with the contents
# The -x patterns exclude:
# 1. All hidden files and directories (*/\.*)
# 2. All __pycache__ directories and their contents (*__pycache__* with recursive globbing)
# 3. Other specific files to exclude
cd obsidian-sync && zip -r ../obsidian-sync.ankiaddon * \
    -x "*/\.*" \
    -x "*__pycache__*" \
    -x "*.pyc" \
    -x "*.pyo" \
    -x "*/meta.json" \
    -x "*/user_files/*" \
    -x "*/addon_metadata.json"
