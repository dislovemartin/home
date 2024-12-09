FROM nvcr.io/nvidia/tritonserver:23.12-py3

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8 \
    TZ=UTC

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    sudo \
    build-essential \
    python3-pip \
    python3-dev \
    zsh \
    fonts-powerline \
    locales \
    tzdata \
    openssh-client \
    gnupg \
    lsb-release \
    ca-certificates \
    htop \
    tmux \
    vim \
    && locale-gen en_US.UTF-8 \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=1000

# Create the user group
RUN groupadd -f -g ${USER_GID} ${USERNAME}

# Create the user
RUN useradd -l -m -u ${USER_UID} -g ${USER_GID} -s /usr/bin/zsh ${USERNAME} \
    && echo "${USERNAME} ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME} \
    && chmod 0440 /etc/sudoers.d/${USERNAME}

# Set up SSH directory
RUN mkdir -p /home/${USERNAME}/.ssh \
    && chown -R ${USERNAME}:${USER_GID} /home/${USERNAME}/.ssh \
    && chmod 700 /home/${USERNAME}/.ssh

# Install Oh My Zsh and plugins for better terminal experience
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended \
    && git clone https://github.com/zsh-users/zsh-autosuggestions /root/.oh-my-zsh/custom/plugins/zsh-autosuggestions \
    && git clone https://github.com/zsh-users/zsh-syntax-highlighting.git /root/.oh-my-zsh/custom/plugins/zsh-syntax-highlighting \
    && cp -r /root/.oh-my-zsh /home/${USERNAME}/ \
    && chown -R ${USERNAME}:${USER_GID} /home/${USERNAME}/.oh-my-zsh

# Set up Python development environment
RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel

# Install development tools with version pinning
RUN pip3 install --no-cache-dir \
    black==24.2.0 \
    flake8==7.0.0 \
    pylint==3.0.3 \
    pytest==8.0.2 \
    pytest-cov==4.1.0 \
    ipython==8.21.0 \
    jupyter==1.0.0 \
    pre-commit==3.6.2 \
    isort==5.13.2

# Install ML/NVIDIA tools with specific versions
RUN pip3 install --no-cache-dir \
    torch==2.1.2 \
    torchvision==0.16.2 \
    torchaudio==2.1.2 \
    transformers==4.36.2 \
    optimum==1.16.1 \
    auto-gptq==0.5.1 \
    nvidia-ml-py==12.535.133 \
    tensorboard==2.15.1 \
    scikit-learn==1.4.0 \
    pandas==2.2.0 \
    numpy==1.26.4

# Copy requirements and install project dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Configure ZSH for vscode user
COPY .devcontainer/.zshrc /home/${USERNAME}/.zshrc
RUN chown ${USERNAME}:${USER_GID} /home/${USERNAME}/.zshrc

# Set up CUDA environment
ENV CUDA_HOME=/usr/local/cuda \
    PATH=/usr/local/cuda/bin:${PATH} \
    LD_LIBRARY_PATH=/usr/local/cuda/lib64:${LD_LIBRARY_PATH}

# Create workspace directory and set permissions
RUN mkdir -p /workspace \
    && chown -R ${USERNAME}:${USER_GID} /workspace

# Switch to non-root user
USER ${USERNAME}

# Set working directory
WORKDIR /workspace

# Set default shell to zsh
ENV SHELL=/usr/bin/zsh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD nvidia-smi || exit 1