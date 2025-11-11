"""
纯Python实现的Mermaid渲染器
支持多种渲染方式，无需Node.js
"""
import os
import re
import hashlib
import base64
import urllib.parse
import urllib.request
import json
from pathlib import Path

try:
    from fix_mermaid_syntax import fix_mermaid_syntax, validate_mermaid_syntax
    HAS_SYNTAX_FIXER = True
except ImportError:
    HAS_SYNTAX_FIXER = False


class MermaidRenderer:
    """Mermaid图表渲染器"""
    
    def __init__(self, output_dir="mermaid_images"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.method = self._detect_method()
    
    def _detect_method(self):
        """检测可用的渲染方法"""
        # 方法1: 尝试纯Python渲染（推荐）
        try:
            import matplotlib
            import networkx
            print("  → 检测到matplotlib+networkx，将使用纯Python渲染（离线）")
            return 'pure_python'
        except ImportError:
            pass
        
        # 方法2: 尝试playwright
        try:
            from playwright.sync_api import sync_playwright
            print("  → 检测到Playwright，将使用浏览器渲染（高质量）")
            return 'playwright'
        except ImportError:
            pass
        
        # 方法3: 尝试pyppeteer
        try:
            import pyppeteer
            print("  → 检测到Pyppeteer，将使用浏览器渲染")
            return 'pyppeteer'
        except ImportError:
            pass
        
        # 方法4: 使用在线API（无需额外安装）
        print("  → 使用在线API渲染（需要网络连接）")
        return 'online_api'
    
    def render(self, mermaid_code, output_filename):
        """
        渲染Mermaid代码为PNG图片
        
        Args:
            mermaid_code: Mermaid代码
            output_filename: 输出文件名
            
        Returns:
            成功返回图片路径，失败返回None
        """
        output_path = os.path.join(self.output_dir, output_filename)
        
        # 如果文件已存在，直接返回
        if os.path.exists(output_path):
            return output_path
        
        # 验证和修复语法
        if HAS_SYNTAX_FIXER:
            is_valid, msg = validate_mermaid_syntax(mermaid_code)
            if not is_valid:
                print(f"  ⚠ 语法问题: {msg}")
                mermaid_code = fix_mermaid_syntax(mermaid_code)
                print(f"  → 已自动修复语法")
        
        try:
            if self.method == 'pure_python':
                # 尝试纯Python渲染
                result = self._render_pure_python(mermaid_code, output_path)
                if result:
                    return result
                # 如果失败，不降级，直接返回None
                print(f"  → 纯Python渲染失败，将保留为代码块")
                return None
            elif self.method == 'playwright':
                return self._render_playwright(mermaid_code, output_path)
            elif self.method == 'pyppeteer':
                return self._render_pyppeteer(mermaid_code, output_path)
            else:
                return self._render_online_api(mermaid_code, output_path)
        except Exception as e:
            print(f"  ✗ 渲染失败: {e}")
            return None
    
    def _render_pure_python(self, mermaid_code, output_path):
        """
        使用纯Python渲染（matplotlib + networkx）
        优点：完全离线，无需浏览器
        缺点：只支持常见图表类型
        """
        try:
            from mermaid_python_renderer import PurePythonMermaidRenderer
            renderer = PurePythonMermaidRenderer()
            if renderer.render(mermaid_code, output_path):
                return output_path
            return None
        except ImportError:
            print(f"  ⚠ 纯Python渲染器未安装")
            return None
        except Exception as e:
            print(f"  ⚠ 纯Python渲染失败: {e}")
            return None
    
    def _render_online_api(self, mermaid_code, output_path):
        """
        使用在线API渲染（mermaid.ink）
        优点：无需安装额外依赖
        缺点：需要网络连接
        """
        # 尝试多个API服务
        apis = [
            {
                'name': 'mermaid.ink',
                'url_format': lambda code: f"https://mermaid.ink/img/{base64.urlsafe_b64encode(code.encode('utf-8')).decode('ascii')}"
            },
            {
                'name': 'kroki.io',
                'url_format': lambda code: f"https://kroki.io/mermaid/png/{base64.urlsafe_b64encode(code.encode('utf-8')).decode('ascii')}"
            }
        ]
        
        for api in apis:
            try:
                # 构建URL
                url = api['url_format'](mermaid_code)
                
                # 设置请求头
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                request = urllib.request.Request(url, headers=headers)
                
                # 下载图片
                with urllib.request.urlopen(request, timeout=30) as response:
                    if response.status == 200:
                        image_data = response.read()
                        # 检查是否是有效的PNG图片
                        if len(image_data) > 100 and image_data[:8] == b'\x89PNG\r\n\x1a\n':
                            with open(output_path, 'wb') as f:
                                f.write(image_data)
                            print(f"  → 使用 {api['name']} 渲染成功")
                            return output_path
                        else:
                            print(f"  ⚠ {api['name']} 返回的不是有效图片")
                            continue
                    else:
                        print(f"  ⚠ {api['name']} 返回错误: {response.status}")
                        continue
                        
            except urllib.error.URLError as e:
                print(f"  ⚠ {api['name']} 请求失败: {e.reason if hasattr(e, 'reason') else str(e)}")
                continue
            except Exception as e:
                print(f"  ⚠ {api['name']} 错误: {e}")
                continue
        
        # 所有API都失败
        print(f"  ✗ 所有在线API都失败")
        print(f"  💡 建议安装本地渲染: pip install playwright && playwright install chromium")
        return None
    
    def _render_playwright(self, mermaid_code, output_path):
        """
        使用Playwright渲染（推荐）
        优点：质量高，速度快
        缺点：需要安装playwright和浏览器
        """
        from playwright.sync_api import sync_playwright
        
        # HTML模板
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
    </script>
</head>
<body style="margin: 0; padding: 20px; background: white;">
    <div class="mermaid">
{mermaid_code}
    </div>
</body>
</html>
"""
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html_content)
            
            # 等待Mermaid渲染完成
            page.wait_for_selector('svg', timeout=10000)
            
            # 获取SVG元素
            svg_element = page.query_selector('svg')
            if svg_element:
                # 截图
                svg_element.screenshot(path=output_path)
                browser.close()
                return output_path
            else:
                browser.close()
                return None
    
    def _render_pyppeteer(self, mermaid_code, output_path):
        """
        使用Pyppeteer渲染
        优点：异步高效
        缺点：需要安装pyppeteer
        """
        import asyncio
        import pyppeteer
        
        async def _render():
            browser = await pyppeteer.launch()
            page = await browser.newPage()
            
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
</head>
<body style="margin: 0; padding: 20px; background: white;">
    <div class="mermaid">
{mermaid_code}
    </div>
    <script>
        mermaid.initialize({{ startOnLoad: true }});
    </script>
</body>
</html>
"""
            
            await page.setContent(html_content)
            await page.waitForSelector('svg', {'timeout': 10000})
            
            element = await page.querySelector('svg')
            if element:
                await element.screenshot({'path': output_path})
            
            await browser.close()
            return output_path if element else None
        
        return asyncio.get_event_loop().run_until_complete(_render())


def convert_mermaid_to_images(markdown_text, output_dir="mermaid_images"):
    """
    将Markdown中的Mermaid代码块转换为图片（纯Python实现）
    
    Args:
        markdown_text: 原始Markdown文本
        output_dir: 图片输出目录
        
    Returns:
        (处理后的Markdown文本, 成功数量, 失败数量)
    """
    renderer = MermaidRenderer(output_dir)
    
    success_count = 0
    fail_count = 0
    counter = [0]
    failed_codes = []  # 记录失败的代码
    
    # 匹配 ```mermaid ... ``` 代码块
    pattern = r'```\s*mermaid\s*\n(.*?)\n```'
    
    def replace_mermaid(match):
        nonlocal success_count, fail_count
        mermaid_code = match.group(1).strip()
        counter[0] += 1
        
        # 生成唯一的文件名（基于内容哈希）
        content_hash = hashlib.md5(mermaid_code.encode()).hexdigest()[:8]
        image_filename = f"mermaid_{counter[0]}_{content_hash}.png"
        
        print(f"  → 渲染Mermaid #{counter[0]}... ({len(mermaid_code)} 字符)")
        
        # 显示图表类型
        first_line = mermaid_code.split('\n')[0].strip().lower()
        if first_line.startswith('graph'):
            chart_type = "流程图"
        elif first_line.startswith('pie'):
            chart_type = "饼图"
        elif first_line.startswith('gantt'):
            chart_type = "甘特图"
        elif first_line.startswith('sequencediagram'):
            chart_type = "时序图"
        else:
            chart_type = "图表"
        print(f"     类型: {chart_type}")
        
        # 渲染图片（添加重试机制）
        result = None
        for attempt in range(2):  # 尝试2次
            result = renderer.render(mermaid_code, image_filename)
            if result:
                break
            if attempt == 0:
                print(f"     重试中...")
        
        if result:
            size = os.path.getsize(result)
            print(f"  ✓ 成功: {image_filename} ({size} 字节)")
            success_count += 1
            # 返回markdown图片语法
            return f'\n![Mermaid{chart_type} {counter[0]}]({result})\n'
        else:
            print(f"  ✗ 失败: 保留为代码块")
            fail_count += 1
            failed_codes.append((counter[0], chart_type, mermaid_code[:100]))
            
            # 返回格式化的代码块（更易读）
            return f'\n\n**📊 Mermaid{chart_type} {counter[0]}** _(渲染失败，显示为代码)_\n\n```mermaid\n{mermaid_code}\n```\n\n'
    
    # 替换所有Mermaid块
    processed_text = re.sub(pattern, replace_mermaid, markdown_text, flags=re.DOTALL)
    
    # 如果有失败的，显示提示
    if failed_codes:
        print(f"\n  ⚠ 失败的图表:")
        for idx, chart_type, preview in failed_codes:
            print(f"     #{idx} ({chart_type}): {preview}...")
        print(f"\n  💡 解决方案:")
        print(f"     1. 检查网络连接")
        print(f"     2. 验证Mermaid语法: https://mermaid.live")
        print(f"     3. 安装本地渲染: pip install playwright && playwright install chromium")
    
    return processed_text, success_count, fail_count


if __name__ == "__main__":
    # 测试
    test_markdown = """
# 测试文档

```mermaid
graph TD
    A[开始] --> B[处理]
    B --> C{判断}
    C -->|是| D[结束]
    C -->|否| B
```

正常文本。
"""
    
    print("="*60)
    print("纯Python Mermaid渲染测试")
    print("="*60)
    
    result, success, fail = convert_mermaid_to_images(test_markdown)
    
    print(f"\n成功: {success}, 失败: {fail}")
    print("\n转换后的Markdown:")
    print(result)

