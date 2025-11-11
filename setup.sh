#!/bin/bash

###############################################################################
# Markdown转DOCX Web应用 - 系统依赖安装脚本
# 支持系统：Debian/Ubuntu/CentOS/RHEL
# 功能：安装Pandoc和中文字体
###############################################################################

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_header() {
    echo ""
    echo "============================================================"
    echo -e "${BLUE}$1${NC}"
    echo "============================================================"
}

# 检查是否为root或有sudo权限
check_sudo() {
    if [ "$EUID" -ne 0 ]; then
        if ! command -v sudo >/dev/null 2>&1; then
            print_error "需要root权限或sudo命令"
            exit 1
        fi
        SUDO="sudo"
    else
        SUDO=""
    fi
}

# 检测系统类型
detect_system() {
    print_header "检测操作系统"
    
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS_NAME=$ID
        OS_VERSION=$VERSION_ID
        
        case "$OS_NAME" in
            debian|ubuntu)
                OS_TYPE="debian"
                PKG_MGR="apt-get"
                print_success "检测到 Debian/Ubuntu 系统: $PRETTY_NAME"
                ;;
            centos|rhel|rocky|almalinux)
                OS_TYPE="rhel"
                # CentOS 8+ 使用 dnf，CentOS 7 使用 yum
                if command -v dnf >/dev/null 2>&1; then
                    PKG_MGR="dnf"
                else
                    PKG_MGR="yum"
                fi
                print_success "检测到 CentOS/RHEL 系统: $PRETTY_NAME"
                ;;
            fedora)
                OS_TYPE="rhel"
                PKG_MGR="dnf"
                print_success "检测到 Fedora 系统: $PRETTY_NAME"
                ;;
            *)
                print_error "不支持的系统: $PRETTY_NAME"
                print_info "本脚本仅支持 Debian/Ubuntu/CentOS/RHEL 系统"
                exit 1
                ;;
        esac
    else
        print_error "无法检测操作系统"
        exit 1
    fi
}

# 安装Pandoc
install_pandoc() {
    print_header "步骤 1/3: 安装 Pandoc"
    
    if command -v pandoc >/dev/null 2>&1; then
        PANDOC_VERSION=$(pandoc --version | head -n 1)
        print_success "Pandoc 已安装: $PANDOC_VERSION"
        return 0
    fi
    
    print_info "正在安装 Pandoc..."
    
    case "$OS_TYPE" in
        debian)
            $SUDO apt-get update -qq
            $SUDO apt-get install -y pandoc
            ;;
        rhel)
            # CentOS/RHEL 需要 EPEL 仓库
            if ! $PKG_MGR repolist | grep -q epel; then
                print_info "启用 EPEL 仓库..."
                if [ "$PKG_MGR" = "dnf" ]; then
                    $SUDO dnf install -y epel-release
                else
                    $SUDO yum install -y epel-release
                fi
            fi
            $SUDO $PKG_MGR install -y pandoc
            ;;
    esac
    
    if command -v pandoc >/dev/null 2>&1; then
        PANDOC_VERSION=$(pandoc --version | head -n 1)
        print_success "Pandoc 安装成功: $PANDOC_VERSION"
    else
        print_error "Pandoc 安装失败"
        exit 1
    fi
}

# 安装中文字体
install_chinese_fonts() {
    print_header "步骤 2/3: 安装中文字体"
    
    case "$OS_TYPE" in
        debian)
            if fc-list 2>/dev/null | grep -q "WenQuanYi"; then
                print_success "中文字体已安装"
            else
                print_info "正在安装文泉驿中文字体..."
                $SUDO apt-get install -y fonts-wqy-zenhei fonts-wqy-microhei
                print_success "中文字体安装完成"
            fi
            ;;
        rhel)
            if fc-list 2>/dev/null | grep -q "WenQuanYi"; then
                print_success "中文字体已安装"
            else
                print_info "正在安装文泉驿中文字体..."
                $SUDO $PKG_MGR install -y wqy-zenhei-fonts wqy-microhei-fonts
                print_success "中文字体安装完成"
            fi
            ;;
    esac
}

# 清理matplotlib缓存
clear_matplotlib_cache() {
    print_header "步骤 3/3: 清理 matplotlib 字体缓存"
    
    if [ -d "$HOME/.cache/matplotlib" ]; then
        print_info "清理旧的字体缓存..."
        rm -rf "$HOME/.cache/matplotlib"
        print_success "字体缓存已清理"
    else
        print_info "无需清理缓存（首次安装）"
    fi
}

# 显示完成信息
show_completion() {
    print_header "✅ 系统依赖安装完成！"
    
    echo ""
    echo "已安装的组件："
    echo -e "  ✓ Pandoc: $(pandoc --version | head -n 1 | cut -d' ' -f2)"
    echo "  ✓ 中文字体: 文泉驿正黑、文泉驿微米黑"
    echo "  ✓ 包管理器: $PKG_MGR"
    echo ""
    echo "下一步操作："
    echo ""
    echo "1. 安装 Python 依赖："
    echo -e "   ${GREEN}pip3 install -r requirements.txt${NC}"
    echo ""
    echo "   或使用国内镜像源（推荐）："
    echo -e "   ${GREEN}pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple${NC}"
    echo ""
    echo "2. 测试 Mermaid 渲染："
    echo -e "   ${GREEN}python3 mermaid_python_renderer.py${NC}"
    echo ""
    echo "3. 启动应用："
    echo -e "   ${GREEN}python3 app.py${NC}"
    echo ""
    echo "4. 访问："
    echo -e "   ${BLUE}http://127.0.0.1:5000${NC}"
    echo ""
    
    if [ "$OS_TYPE" = "rhel" ]; then
        echo "💡 CentOS/RHEL 提示："
        echo "   如果遇到防火墙问题，执行："
        echo -e "   ${GREEN}sudo firewall-cmd --add-port=5000/tcp --permanent${NC}"
        echo -e "   ${GREEN}sudo firewall-cmd --reload${NC}"
        echo ""
    fi
    
    echo "============================================================"
}

# 主函数
main() {
    print_header "Markdown转DOCX - 系统依赖安装脚本"
    
    echo ""
    echo "本脚本将安装以下系统组件："
    echo "  1. Pandoc (文档转换引擎)"
    echo "  2. 中文字体 (文泉驿字体)"
    echo "  3. 清理 matplotlib 字体缓存"
    echo ""
    echo "支持的系统："
    echo "  • Debian / Ubuntu"
    echo "  • CentOS / RHEL / Rocky Linux / AlmaLinux"
    echo "  • Fedora"
    echo ""
    echo -e "${YELLOW}注意：需要 sudo 权限${NC}"
    echo ""
    
    read -p "按 Enter 继续，或 Ctrl+C 取消... " -r
    echo ""
    
    check_sudo
    detect_system
    install_pandoc
    install_chinese_fonts
    clear_matplotlib_cache
    show_completion
}

# 错误处理
trap 'print_error "安装过程中发生错误"; exit 1' ERR

# 运行主函数
main
