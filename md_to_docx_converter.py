"""
Markdown 到 DOCX 转换器 - 使用Pandoc引擎
支持Mermaid图表自动渲染为图片（纯Python实现）
"""
import pypandoc
import os
import sys


def convert_markdown_to_docx(markdown_text, output_path, template_path=None):
    """
    将Markdown文本转换为DOCX文档（使用Pandoc）
    自动检测并处理Mermaid图表
    
    Args:
        markdown_text: Markdown格式的文本
        output_path: 输出的DOCX文件路径
        template_path: 可选的DOTX模板文件路径
    """
    # 准备pandoc参数
    extra_args = []
    
    # 如果提供了模板，使用reference-doc参数
    if template_path and os.path.exists(template_path):
        # 确保使用绝对路径，避免中文路径问题
        template_path = os.path.abspath(template_path)
        print(f"  → 使用模板: {template_path}")
        print(f"  → 模板文件大小: {os.path.getsize(template_path)} 字节")
        extra_args.extend(['--reference-doc', template_path])
    
    # 检查是否有Mermaid图表
    has_mermaid = '```mermaid' in markdown_text or '~~~mermaid' in markdown_text
    
    if has_mermaid:
        print(f"  → 检测到Mermaid图表")
        
        # 使用纯Python渲染器
        try:
            from mermaid_renderer import convert_mermaid_to_images
            
            print(f"  → 使用纯Python渲染器")
            markdown_text, success, fail = convert_mermaid_to_images(markdown_text)
            
            if success > 0:
                print(f"  ✓ 成功渲染 {success} 个Mermaid图表")
            if fail > 0:
                print(f"  ⚠ {fail} 个Mermaid图表渲染失败")
                
        except Exception as e:
            print(f"  ✗ Mermaid渲染失败: {e}")
            print(f"  💡 提示: 默认使用在线API，需要网络连接")
    
    # 添加其他有用的参数
    extra_args.extend([
        '--standalone',  # 创建独立文档
        '--from=markdown+pipe_tables+grid_tables',  # 支持表格
    ])
    
    print(f"  → Pandoc参数: {extra_args}")
    
    try:
        # 检查pypandoc是否可用
        try:
            import pypandoc as pd
            print(f"  → pypandoc版本: {pd.__version__}")
        except ImportError as ie:
            raise Exception(f"pypandoc未安装: {str(ie)}")
        
        # 检查Pandoc是否安装
        try:
            pandoc_version = pd.get_pandoc_version()
            print(f"  → Pandoc版本: {pandoc_version}")
        except Exception as pve:
            raise Exception(f"Pandoc未安装或无法访问: {str(pve)}\n"
                          f"请安装Pandoc: https://pandoc.org/installing.html")
        
        # 使用pypandoc进行转换
        print(f"  → 开始转换...")
        result = pd.convert_text(
            markdown_text,
            'docx',
            format='md',
            outputfile=output_path,
            extra_args=extra_args
        )
        
        # 检查输出文件
        if os.path.exists(output_path):
            size = os.path.getsize(output_path)
            print(f"  → 转换完成，文件大小: {size} 字节")
            return True
        else:
            raise Exception("转换完成但输出文件不存在")
            
    except Exception as e:
        error_msg = str(e)
        
        # 提供更友好的错误提示
        if "No such file or directory" in error_msg or "not found" in error_msg.lower():
            raise Exception(
                "Pandoc未找到！\n"
                "请先安装Pandoc:\n"
                "  Windows: winget install pandoc 或 choco install pandoc\n"
                "  Linux: sudo apt-get install pandoc\n"
                "  Mac: brew install pandoc\n"
                f"原始错误: {error_msg}"
            )
        elif "pypandoc" in error_msg.lower():
            raise Exception(
                "pypandoc未正确安装！\n"
                f"请运行: pip install pypandoc\n"
                f"原始错误: {error_msg}"
            )
        else:
            raise Exception(f"Pandoc转换失败: {error_msg}")


def check_pandoc_installation():
    """
    检查Pandoc是否已安装
    """
    try:
        # 检查pandoc版本
        version = pypandoc.get_pandoc_version()
        print(f"✓ Pandoc已安装，版本: {version}")
        
        # 检查Mermaid渲染器
        try:
            from mermaid_renderer import MermaidRenderer
            renderer = MermaidRenderer()
            print(f"✓ Mermaid渲染器已就绪")
            
            if renderer.method == 'playwright':
                print(f"  → 渲染方式: Playwright（高质量）")
            elif renderer.method == 'pyppeteer':
                print(f"  → 渲染方式: Pyppeteer（异步）")
            else:
                print(f"  → 渲染方式: 在线API（需要网络）")
                print(f"  💡 安装Playwright获得更好效果: pip install playwright && playwright install chromium")
        except Exception as e:
            print(f"⚠ Mermaid渲染器初始化失败: {e}")
        
        return True
    except Exception:
        print("× Pandoc未安装")
        print("\n请手动安装Pandoc:")
        print("  Windows: winget install pandoc")
        print("  Linux:   sudo apt-get install pandoc")
        print("  Mac:     brew install pandoc")
        return False


if __name__ == "__main__":
    # 测试Pandoc和Mermaid安装
    print("="*60)
    print("检查转换工具安装状态")
    print("="*60)
    check_pandoc_installation()
