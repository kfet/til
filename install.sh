#!/bin/bash
# TIL Tool Installer Script

set -e  # Exit on error

# Default installation directory
REPO_DIR="${TIL_INSTALL_DIR:-$HOME/.til-repo}"

# Banner
echo "============================================="
echo "  Installing TIL CLI Tool"
echo "============================================="

# Check for pipx
if ! command -v pipx &> /dev/null; then
    echo "Installing pipx..."
    pip install --user pipx
    
    # Add pipx to PATH for this session
    export PATH="$PATH:$HOME/.local/bin"
    
    # Verify pipx is now available
    if ! command -v pipx &> /dev/null; then
        echo "Error: pipx installation succeeded but command not found in PATH"
        echo "Please run the following commands manually and try again:"
        echo "  export PATH=\"\$PATH:\$HOME/.local/bin\""
        echo "  pipx ensurepath"
        exit 1
    fi
    
    # Now that pipx is in PATH, ensure paths are set up
    pipx ensurepath
fi

# Clone the repository if not already done
if [[ ! -d "$REPO_DIR" ]]; then
    echo "Cloning TIL repository to $REPO_DIR..."
    git clone https://github.com/kfet/til.git "$REPO_DIR"
else
    echo "TIL repository already exists at $REPO_DIR, updating..."
    (cd "$REPO_DIR" && git pull)
fi

# Install the package
echo "Installing TIL CLI tool..."
(cd "$REPO_DIR/til_cli" && pipx install --force .)

# Configure the repository location
echo "Configuring repository location..."
til config "$REPO_DIR"

echo ""
echo "Installation complete! You can now use 'til' from anywhere."
echo ""
echo "Examples:"
echo "  til list              # List all entries"
echo "  til search git        # Search for entries related to git"
echo "  til update            # Update the repository with latest entries"
echo "  til help              # Show all available commands"
echo ""
echo "Your TIL repository is located at: $REPO_DIR"
