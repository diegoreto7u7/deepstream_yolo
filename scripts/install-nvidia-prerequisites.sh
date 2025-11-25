#!/bin/bash
#
# install-nvidia-prerequisites.sh
#
# Automatically installs NVIDIA drivers and nvidia-container-toolkit
# on a fresh system (Ubuntu/Debian or RedHat/Rocky/CentOS)
#
# This script is needed for machines WITHOUT any NVIDIA/CUDA libraries installed
# The Docker container has CUDA inside, but the HOST needs:
#   1. NVIDIA GPU drivers
#   2. nvidia-container-toolkit (nvidia-docker)
#
# Usage:
#   sudo ./scripts/install-nvidia-prerequisites.sh
#   sudo ./scripts/install-nvidia-prerequisites.sh --skip-driver  # If driver already installed
#   sudo ./scripts/install-nvidia-prerequisites.sh --help
#

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Flags
SKIP_DRIVER=false
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-driver)
            SKIP_DRIVER=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            echo "Usage: sudo $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skip-driver    Skip NVIDIA driver installation (use if already installed)"
            echo "  --dry-run        Show what would be installed without actually installing"
            echo "  --help, -h       Show this help message"
            echo ""
            echo "This script installs:"
            echo "  1. NVIDIA GPU drivers (latest or specified version)"
            echo "  2. nvidia-container-toolkit (required for Docker GPU access)"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if running as root
if [ "$EUID" -ne 0 ] && [ "$DRY_RUN" = false ]; then
    echo -e "${RED}Error: This script must be run as root (use sudo)${NC}"
    exit 1
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  NVIDIA Prerequisites Installer for DeepStream Docker         ║${NC}"
echo -e "${BLUE}║  Installing: NVIDIA Drivers + nvidia-container-toolkit        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VER=$VERSION_ID
else
    echo -e "${RED}Cannot detect OS. /etc/os-release not found.${NC}"
    exit 1
fi

echo -e "${GREEN}Detected OS:${NC} $PRETTY_NAME"
echo ""

# Function to check if NVIDIA GPU exists
check_nvidia_gpu() {
    echo -e "${YELLOW}[1/6] Checking for NVIDIA GPU...${NC}"
    if lspci | grep -i nvidia > /dev/null 2>&1; then
        GPU_INFO=$(lspci | grep -i nvidia | head -n 1)
        echo -e "${GREEN}✓ NVIDIA GPU detected:${NC} $GPU_INFO"
        return 0
    else
        echo -e "${RED}✗ No NVIDIA GPU detected!${NC}"
        echo -e "${YELLOW}This system may not have an NVIDIA GPU or lspci is not installed.${NC}"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
        return 1
    fi
}

# Function to check existing NVIDIA driver
check_existing_driver() {
    echo ""
    echo -e "${YELLOW}[2/6] Checking for existing NVIDIA driver...${NC}"

    if command -v nvidia-smi &> /dev/null; then
        DRIVER_VERSION=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null | head -n 1)
        if [ -n "$DRIVER_VERSION" ]; then
            echo -e "${GREEN}✓ NVIDIA driver already installed:${NC} version $DRIVER_VERSION"

            # Check if driver is compatible with CUDA 12.8
            REQUIRED_MIN_VERSION="525.60.13"  # Minimum for CUDA 12.8
            if [ "$(printf '%s\n' "$REQUIRED_MIN_VERSION" "$DRIVER_VERSION" | sort -V | head -n1)" = "$REQUIRED_MIN_VERSION" ]; then
                echo -e "${GREEN}✓ Driver version is compatible with CUDA 12.8${NC}"
                SKIP_DRIVER=true
            else
                echo -e "${YELLOW}⚠ Driver version may be too old for CUDA 12.8 (minimum: $REQUIRED_MIN_VERSION)${NC}"
                read -p "Update driver? (y/N): " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    SKIP_DRIVER=false
                else
                    SKIP_DRIVER=true
                fi
            fi
        fi
    else
        echo -e "${YELLOW}✗ No NVIDIA driver detected (nvidia-smi not found)${NC}"
        SKIP_DRIVER=false
    fi
}

# Function to install NVIDIA driver on Ubuntu/Debian
install_driver_ubuntu() {
    echo ""
    echo -e "${YELLOW}[3/6] Installing NVIDIA driver (Ubuntu/Debian)...${NC}"

    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would run: apt-get update && apt-get install -y ubuntu-drivers-common"
        echo "[DRY RUN] Would run: ubuntu-drivers autoinstall"
        return 0
    fi

    # Update package list
    apt-get update

    # Install ubuntu-drivers tool
    apt-get install -y ubuntu-drivers-common

    # Show available drivers
    echo -e "${BLUE}Available NVIDIA drivers:${NC}"
    ubuntu-drivers devices | grep -i nvidia || true

    # Auto-install recommended driver
    echo -e "${GREEN}Installing recommended NVIDIA driver...${NC}"
    ubuntu-drivers autoinstall

    echo -e "${GREEN}✓ NVIDIA driver installed${NC}"
    echo -e "${YELLOW}⚠ System reboot required to load the driver${NC}"
}

# Function to install NVIDIA driver on RedHat/Rocky/CentOS
install_driver_rhel() {
    echo ""
    echo -e "${YELLOW}[3/6] Installing NVIDIA driver (RedHat/Rocky/CentOS)...${NC}"

    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would install NVIDIA driver from CUDA repository"
        return 0
    fi

    # Install EPEL and development tools
    if [[ "$VER" == "8"* ]]; then
        dnf install -y epel-release
        dnf groupinstall -y "Development Tools"
        dnf install -y kernel-devel kernel-headers gcc make dkms acpid libglvnd-glx libglvnd-opengl libglvnd-devel pkgconfig
    elif [[ "$VER" == "9"* ]]; then
        dnf install -y epel-release
        dnf groupinstall -y "Development Tools"
        dnf install -y kernel-devel kernel-headers gcc make dkms acpid libglvnd-glx libglvnd-opengl libglvnd-devel pkgconfig
    else
        yum install -y epel-release
        yum groupinstall -y "Development Tools"
        yum install -y kernel-devel kernel-headers gcc make dkms acpid libglvnd-glx libglvnd-opengl libglvnd-devel pkgconfig
    fi

    # Add NVIDIA CUDA repository
    echo -e "${GREEN}Adding NVIDIA CUDA repository...${NC}"
    if [[ "$VER" == "8"* ]]; then
        dnf config-manager --add-repo https://developer.download.nvidia.com/compute/cuda/repos/rhel8/x86_64/cuda-rhel8.repo
        dnf clean all
        dnf -y module install nvidia-driver:latest-dkms
    elif [[ "$VER" == "9"* ]]; then
        dnf config-manager --add-repo https://developer.download.nvidia.com/compute/cuda/repos/rhel9/x86_64/cuda-rhel9.repo
        dnf clean all
        dnf -y module install nvidia-driver:latest-dkms
    else
        # RHEL 7 or CentOS 7
        yum-config-manager --add-repo https://developer.download.nvidia.com/compute/cuda/repos/rhel7/x86_64/cuda-rhel7.repo
        yum clean all
        yum install -y nvidia-driver-latest-dkms
    fi

    echo -e "${GREEN}✓ NVIDIA driver installed${NC}"
    echo -e "${YELLOW}⚠ System reboot required to load the driver${NC}"
}

# Function to install nvidia-container-toolkit on Ubuntu/Debian
install_nvidia_docker_ubuntu() {
    echo ""
    echo -e "${YELLOW}[4/6] Installing nvidia-container-toolkit (Ubuntu/Debian)...${NC}"

    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would install nvidia-container-toolkit"
        return 0
    fi

    # Add NVIDIA Container Toolkit repository
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

    curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

    # Update and install
    apt-get update
    apt-get install -y nvidia-container-toolkit

    # Configure Docker to use NVIDIA runtime
    if command -v docker &> /dev/null; then
        nvidia-ctk runtime configure --runtime=docker
        systemctl restart docker 2>/dev/null || true
        echo -e "${GREEN}✓ Docker configured to use NVIDIA runtime${NC}"
    else
        echo -e "${YELLOW}⚠ Docker not installed yet. Run this script again after installing Docker.${NC}"
    fi

    echo -e "${GREEN}✓ nvidia-container-toolkit installed${NC}"
}

# Function to install nvidia-container-toolkit on RedHat/Rocky/CentOS
install_nvidia_docker_rhel() {
    echo ""
    echo -e "${YELLOW}[4/6] Installing nvidia-container-toolkit (RedHat/Rocky/CentOS)...${NC}"

    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would install nvidia-container-toolkit"
        return 0
    fi

    # Add NVIDIA Container Toolkit repository
    curl -s -L https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo | \
        tee /etc/yum.repos.d/nvidia-container-toolkit.repo

    # Install
    if [[ "$VER" == "8"* ]] || [[ "$VER" == "9"* ]]; then
        dnf clean expire-cache
        dnf install -y nvidia-container-toolkit
    else
        yum clean expire-cache
        yum install -y nvidia-container-toolkit
    fi

    # Configure Docker to use NVIDIA runtime
    if command -v docker &> /dev/null; then
        nvidia-ctk runtime configure --runtime=docker
        systemctl restart docker 2>/dev/null || true
        echo -e "${GREEN}✓ Docker configured to use NVIDIA runtime${NC}"
    else
        echo -e "${YELLOW}⚠ Docker not installed yet. Run this script again after installing Docker.${NC}"
    fi

    echo -e "${GREEN}✓ nvidia-container-toolkit installed${NC}"
}

# Function to verify installation
verify_installation() {
    echo ""
    echo -e "${YELLOW}[5/6] Verifying installation...${NC}"

    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would verify nvidia-smi and docker runtime"
        return 0
    fi

    # Check nvidia-smi (may not work until reboot if driver was just installed)
    if command -v nvidia-smi &> /dev/null; then
        echo -e "${GREEN}✓ nvidia-smi found${NC}"
        if nvidia-smi &> /dev/null; then
            echo -e "${GREEN}✓ nvidia-smi working:${NC}"
            nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
        else
            echo -e "${YELLOW}⚠ nvidia-smi installed but not working (reboot required)${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ nvidia-smi not found yet (reboot required)${NC}"
    fi

    # Check nvidia-container-toolkit
    if command -v nvidia-ctk &> /dev/null; then
        echo -e "${GREEN}✓ nvidia-container-toolkit installed${NC}"
    else
        echo -e "${RED}✗ nvidia-container-toolkit not found${NC}"
    fi

    # Check Docker runtime
    if command -v docker &> /dev/null; then
        if docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi &> /dev/null 2>&1; then
            echo -e "${GREEN}✓ Docker GPU access working!${NC}"
        else
            echo -e "${YELLOW}⚠ Docker GPU access not working yet (may need reboot)${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Docker not installed. Install Docker and run this script again.${NC}"
    fi
}

# Function to show next steps
show_next_steps() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Installation Complete!                                        ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}[6/6] Next Steps:${NC}"
    echo ""

    if [ "$SKIP_DRIVER" = false ]; then
        echo -e "${RED}1. REBOOT YOUR SYSTEM${NC}"
        echo -e "   ${YELLOW}sudo reboot${NC}"
        echo ""
        echo -e "2. After reboot, verify NVIDIA driver:"
        echo -e "   ${YELLOW}nvidia-smi${NC}"
        echo ""
    else
        echo -e "${GREEN}1. NVIDIA driver already installed, no reboot needed${NC}"
        echo ""
    fi

    if ! command -v docker &> /dev/null; then
        echo -e "2. Install Docker (if not already installed):"
        if [[ "$OS" == "ubuntu" ]] || [[ "$OS" == "debian" ]]; then
            echo -e "   ${YELLOW}curl -fsSL https://get.docker.com -o get-docker.sh${NC}"
            echo -e "   ${YELLOW}sudo sh get-docker.sh${NC}"
        else
            echo -e "   ${YELLOW}sudo dnf install -y docker-ce docker-ce-cli containerd.io${NC}"
        fi
        echo ""
        echo -e "3. Add your user to docker group:"
        echo -e "   ${YELLOW}sudo usermod -aG docker \$USER${NC}"
        echo -e "   ${YELLOW}newgrp docker${NC}"
        echo ""
    fi

    echo -e "3. Test GPU access in Docker:"
    echo -e "   ${YELLOW}docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi${NC}"
    echo ""
    echo -e "4. Build your DeepStream Docker image:"
    echo -e "   ${YELLOW}cd /home/diego/Documentos/deepstream/app${NC}"
    echo -e "   ${YELLOW}./scripts/docker-build.sh${NC}"
    echo ""
    echo -e "5. Run your DeepStream application:"
    echo -e "   ${YELLOW}./scripts/docker-run.sh${NC}"
    echo ""
    echo -e "${GREEN}For more information, see: docs/DOCKER.md${NC}"
}

# Main installation flow
main() {
    check_nvidia_gpu
    check_existing_driver

    # Install NVIDIA driver
    if [ "$SKIP_DRIVER" = false ]; then
        case "$OS" in
            ubuntu|debian)
                install_driver_ubuntu
                ;;
            rhel|centos|rocky|almalinux)
                install_driver_rhel
                ;;
            *)
                echo -e "${RED}Unsupported OS: $OS${NC}"
                echo -e "${YELLOW}Supported: Ubuntu, Debian, RHEL, CentOS, Rocky Linux, AlmaLinux${NC}"
                exit 1
                ;;
        esac
    else
        echo ""
        echo -e "${GREEN}[3/6] Skipping NVIDIA driver installation (already installed)${NC}"
    fi

    # Install nvidia-container-toolkit
    case "$OS" in
        ubuntu|debian)
            install_nvidia_docker_ubuntu
            ;;
        rhel|centos|rocky|almalinux)
            install_nvidia_docker_rhel
            ;;
        *)
            echo -e "${RED}Unsupported OS: $OS${NC}"
            exit 1
            ;;
    esac

    # Verify installation
    verify_installation

    # Show next steps
    show_next_steps
}

# Run main installation
main
