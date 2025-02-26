# Making the TIL Tool Installable

This technical specification outlines approaches for making the TIL CLI tool globally installable, allowing it to be used from any directory while maintaining its functionality.

## Current Limitations

The TIL tool has the following dependency on its location:

1. It assumes the TIL collection is located in the current working directory (see line 345-346):
   ```python
   root_dir = Path.cwd()
   collection = TILCollection(root_dir)
   ```

2. This means the tool only works when run from the root of the TIL repository.

## Solution Approaches

### 1. Package Installation with Configuration

#### Implementation

1. Create a Python package structure:
   ```
   til/
   ├── setup.py
   ├── til/
   │   ├── __init__.py
   │   ├── __main__.py  # Current til script
   │   └── ...
   ```

2. Modify the tool to accept a configurable repository location:
   ```python
   def get_til_repo_path():
       # Priority order:
       # 1. Command line argument
       # 2. Environment variable
       # 3. Config file
       # 4. Current directory (fallback)
       
       # Check environment variable
       env_path = os.environ.get('TIL_REPO_PATH')
       if env_path and Path(env_path).is_dir():
           return Path(env_path)
           
       # Check config file in user's home directory
       config_path = Path.home() / '.tilconfig'
       if config_path.exists():
           try:
               config = config_path.read_text().strip()
               if Path(config).is_dir():
                   return Path(config)
           except:
               pass
               
       # Fallback to current directory
       return Path.cwd()
   ```

3. Update line 345-346 to use this function:
   ```python
   root_dir = get_til_repo_path()
   collection = TILCollection(root_dir)
   ```

4. Create setup.py file:
   ```python
   from setuptools import setup, find_packages

   setup(
       name="til-cli",
       version="1.0.0",
       packages=find_packages(),
       entry_points={
           "console_scripts": [
               "til=til.__main__:main",
           ],
       },
       python_requires=">=3.12",
   )
   ```

5. Add a configuration command:
   ```python
   # Add to subparsers in main()
   config_parser = subparsers.add_parser('config', help='Configure TIL repository location')
   config_parser.add_argument('path', help='Path to TIL repository')
   
   # Handle in the command section
   elif args.command == 'config':
       config_path = Path.home() / '.tilconfig'
       config_path.write_text(str(Path(args.path).resolve()))
       print(f"TIL repository path set to: {args.path}")
   ```

#### Installation Instructions

```bash
# Clone the repo (one time)
git clone https://github.com/yourusername/til.git
cd til

# Install the package
pip install -e .  # For development
# or
pip install .     # For regular installation
# or
pipx install .    # Recommended for CLI tools

# Configure the repo location
til config /path/to/til/repo
```

### 2. Shell Wrapper with Repository Detection

Create a shell script wrapper that detects the repository location and sets the working directory.

1. Create a shell wrapper:
   ```bash
   #!/bin/bash
   
   # Find the TIL repository path
   if [ -n "$TIL_REPO_PATH" ] && [ -d "$TIL_REPO_PATH" ]; then
       REPO_PATH="$TIL_REPO_PATH"
   elif [ -f "$HOME/.tilconfig" ]; then
       REPO_PATH=$(cat "$HOME/.tilconfig")
   else
       echo "Error: TIL repository not found. Please set TIL_REPO_PATH environment variable or create ~/.tilconfig"
       exit 1
   fi
   
   # Save current directory
   ORIG_DIR="$(pwd)"
   
   # Change to repository directory
   cd "$REPO_PATH" || { echo "Error: Could not change to repository directory"; exit 1; }
   
   # Run the actual TIL script with all arguments
   ./til "$@"
   
   # Return to original directory
   cd "$ORIG_DIR" || true
   ```

2. Make it executable and add to your PATH:
   ```bash
   chmod +x /path/to/til-wrapper.sh
   # Add to .bashrc or .zshrc
   export PATH="$PATH:/path/to/directory/containing/wrapper"
   ```

3. Create a configuration utility:
   ```bash
   #!/bin/bash
   
   if [ $# -ne 1 ]; then
       echo "Usage: til-config /path/to/til/repository"
       exit 1
   fi
   
   if [ ! -d "$1" ]; then
       echo "Error: Directory does not exist: $1"
       exit 1
   fi
   
   echo "$1" > "$HOME/.tilconfig"
   echo "TIL repository configured to: $1"
   ```

### 3. Using pipx with Custom Environment Variables

1. Update the TIL script to use environment variable:
   ```python
   root_dir = Path(os.environ.get('TIL_REPO_PATH', Path.cwd()))
   ```

2. Install with pipx and set the environment variable:
   ```bash
   pipx install .
   pipx runpip til-cli inject-environment TIL_REPO_PATH=/path/to/til/repo
   ```

## Recommended Approach

The package installation with configuration (option 1) is the most robust approach because:

1. It's cross-platform
2. It allows for multiple configuration methods (env vars, config file, CLI args)
3. It follows Python packaging best practices
4. It doesn't require shell-specific scripts

## Additional Considerations

1. **Repository Updates**: Add an `update` command to automatically update the TIL repository:
   ```python
   # Add to subparsers in main()
   update_parser = subparsers.add_parser('update', help='Update TIL repository with latest changes')
   
   # Handle in the command section
   elif args.command == 'update':
       repo_path = get_til_repo_path()
       print(f"Updating TIL repository at: {repo_path}")
       try:
           # Check if it's a git repository
           git_dir = repo_path / '.git'
           if not git_dir.is_dir():
               logger.error(f"Error: Not a git repository: {repo_path}")
               return 1
               
           # Run git pull
           result = subprocess.run(
               ['git', 'pull'],
               cwd=repo_path,
               capture_output=True,
               text=True
           )
           
           if result.returncode == 0:
               print(f"Successfully updated:\n{result.stdout}")
               return 0
           else:
               logger.error(f"Error updating repository:\n{result.stderr}")
               return 1
       except Exception as e:
           logger.error(f"Error updating repository: {e}")
           return 1
   ```

2. **Easy Installation**: Create a simple one-line installer script:
   ```bash
   #!/bin/bash
   # til-installer.sh
   
   set -e  # Exit on error
   
   # Check for pipx
   if ! command -v pipx &> /dev/null; then
       echo "Installing pipx..."
       pip install pipx
       pipx ensurepath
       # Source the updated PATH
       if [[ -f ~/.bashrc ]]; then
           source ~/.bashrc
       elif [[ -f ~/.zshrc ]]; then
           source ~/.zshrc
       fi
   fi
   
   # Clone the repository if not already done
   REPO_DIR="$HOME/.til-repo"
   if [[ ! -d "$REPO_DIR" ]]; then
       echo "Cloning TIL repository..."
       git clone https://github.com/yourusername/til.git "$REPO_DIR"
   else
       echo "TIL repository already exists, updating..."
       (cd "$REPO_DIR" && git pull)
   fi
   
   # Install the package
   echo "Installing TIL CLI tool..."
   (cd "$REPO_DIR" && pipx install .)
   
   # Configure the repository location
   echo "Configuring repository location..."
   til config "$REPO_DIR"
   
   echo "Installation complete! You can now use 'til' from anywhere."
   echo "Try 'til list' to see all entries or 'til help' for more options."
   ```

   Installation would be as simple as:
   ```bash
   curl -sSL https://raw.githubusercontent.com/yourusername/til/main/install.sh | bash
   ```

3. **Multiple TIL Repositories**: The configuration could be extended to support multiple repositories by storing a list in the config file.

4. **Command Completion**: Add shell completion scripts for bash/zsh to make the tool more user-friendly.

## Implementation Steps

1. Restructure the code as a proper Python package
2. Add repository location configuration
3. Update the CLI to support the new configuration options
4. Add the `update` command for repository updates
5. Create setup.py and packaging files
6. Create the installer script for one-line installation
7. Test installation and functionality
8. Create documentation for installation and usage

## Sample Code for Installer

Create a file named `install.sh` in the repository root:

```bash
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
    pipx ensurepath
    
    # Add pipx to PATH for this session
    export PATH="$PATH:$HOME/.local/bin"
fi

# Clone the repository if not already done
if [[ ! -d "$REPO_DIR" ]]; then
    echo "Cloning TIL repository to $REPO_DIR..."
    git clone https://github.com/yourusername/til.git "$REPO_DIR"
else
    echo "TIL repository already exists at $REPO_DIR, updating..."
    (cd "$REPO_DIR" && git pull)
fi

# Install the package
echo "Installing TIL CLI tool..."
(cd "$REPO_DIR" && pipx install --force .)

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
```

Make it executable:
```bash
chmod +x install.sh
```

The user can then install with:
```bash
# From a local clone
./install.sh

# Or directly from GitHub
curl -sSL https://raw.githubusercontent.com/yourusername/til/main/install.sh | bash
```