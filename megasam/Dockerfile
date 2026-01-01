# Use CUDA 11.8 as specified in the MegaSaM README
FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Miniconda
ENV CONDA_DIR=/opt/conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p $CONDA_DIR && \
    rm ~/miniconda.sh
ENV PATH=$CONDA_DIR/bin:$PATH

# Set working directory
WORKDIR /app

# Clone upstream MegaSaM repo and create conda environment
RUN git clone --depth 1 https://github.com/mega-sam/mega-sam.git /app
WORKDIR /app
RUN conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main && \
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r && \
    conda env create -f environment.yml

# Activate Conda environment in subsequent RUN commands
SHELL ["conda", "run", "-n", "mega_sam", "/bin/bash", "-c"]

# Install xformers (Pre-built binary as suggested in README for PyTorch 2.0.1 + CUDA 11.8)
RUN conda install xformers::xformers

# Ensure git submodules are available (if present)
RUN git submodule update --init --recursive

# Compile the 'base' extension for camera tracking
RUN cd base && python setup.py install

# ---------------------------------------------------------------------------
# Download Pretrained Models
# ---------------------------------------------------------------------------

# 1. Download DepthAnything Checkpoint
RUN mkdir -p Depth-Anything/checkpoints && \
    wget -O Depth-Anything/checkpoints/depth_anything_vitl14.pth \
    "https://huggingface.co/spaces/LiheYoung/Depth-Anything/resolve/main/checkpoints/depth_anything_vitl14.pth"

# 2. Download RAFT Checkpoint (using a direct mirror link since GDrive is hard to wget)
RUN mkdir -p cvd_opt && \
    wget -O cvd_opt/raft-things.pth \
    "https://github.com/sczhou/ProPainter/releases/download/v0.1.0/raft-things.pth"

# 3. Handle MegaSaM Checkpoint
# Note: 'checkpoints/megasam_final.pth' is assumed to be part of the git repo 
# or LFS. If missing, you may need to add a download step here if a URL exists.
# The following ensures the directory exists.
RUN mkdir -p checkpoints

# Set the default entrypoint to run commands inside the conda environment
ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "mega_sam"]

# Default command (can be overridden)
CMD ["python", "tools/run_demo.py"]
