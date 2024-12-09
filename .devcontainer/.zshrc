# Path to your oh-my-zsh installation.
export ZSH="$HOME/.oh-my-zsh"

# Set name of the theme to load
ZSH_THEME="robbyrussell"

# Plugins
plugins=(
    git
    docker
    python
    pip
    virtualenv
    history
    colored-man-pages
    zsh-autosuggestions
    zsh-syntax-highlighting
)

source $ZSH/oh-my-zsh.sh

# User configuration
export LANG=en_US.UTF-8
export EDITOR='code'

# Aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias python=python3
alias pip=pip3

# CUDA and Python paths
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
export PYTHONPATH=/workspace:$PYTHONPATH

# Custom functions
function nvidia-smi-watch() {
    watch -n0.5 nvidia-smi
}

# Welcome message
echo "🚀 NVIDIA ML Development Environment"
nvidia-smi 