"""
Mermaid语法修复工具
自动检测和修复常见的Mermaid语法问题
"""
import re


def fix_mermaid_syntax(mermaid_code):
    """
    修复常见的Mermaid语法问题
    
    Args:
        mermaid_code: 原始Mermaid代码
        
    Returns:
        修复后的代码
    """
    # 去除首尾空白
    code = mermaid_code.strip()
    
    # 修复1: 饼图格式（确保缩进正确）
    if code.startswith('pie'):
        lines = code.split('\n')
        fixed_lines = []
        for i, line in enumerate(lines):
            line = line.strip()
            if i == 0:
                # 第一行（pie title xxx）
                fixed_lines.append(line)
            elif line and ':' in line:
                # 数据行，确保格式正确
                parts = line.split(':')
                if len(parts) == 2:
                    label = parts[0].strip().strip('"')
                    value = parts[1].strip()
                    fixed_lines.append(f'    "{label}" : {value}')
            elif line:
                fixed_lines.append(line)
        code = '\n'.join(fixed_lines)
    
    # 修复2: 流程图节点格式
    if code.startswith('graph'):
        # 确保箭头前后有空格
        code = re.sub(r'([A-Za-z0-9\]])\s*-->\s*([A-Za-z0-9\[])', r'\1 --> \2', code)
        code = re.sub(r'([A-Za-z0-9\]])\s*--\s*([A-Za-z0-9\[])', r'\1 -- \2', code)
    
    # 修复3: 删除多余的空行
    lines = code.split('\n')
    fixed_lines = []
    prev_empty = False
    for line in lines:
        if line.strip():
            fixed_lines.append(line)
            prev_empty = False
        elif not prev_empty:
            fixed_lines.append(line)
            prev_empty = True
    
    return '\n'.join(fixed_lines)


def validate_mermaid_syntax(mermaid_code):
    """
    验证Mermaid语法
    
    Returns:
        (is_valid, error_message)
    """
    code = mermaid_code.strip()
    
    # 检查是否为空
    if not code:
        return False, "代码为空"
    
    # 检查是否有图表类型
    first_line = code.split('\n')[0].strip().lower()
    valid_types = ['graph', 'flowchart', 'sequencediagram', 'pie', 'gantt', 
                   'classDiagram', 'stateDiagram', 'mindmap', 'quadrantChart']
    
    if not any(first_line.startswith(t.lower()) for t in valid_types):
        return False, f"未识别的图表类型: {first_line}"
    
    # 饼图特殊检查
    if first_line.startswith('pie'):
        if ':' not in code:
            return False, "饼图缺少数据（格式: \"标签\" : 数值）"
        
        # 检查数据行格式
        data_lines = [l for l in code.split('\n')[1:] if ':' in l]
        if not data_lines:
            return False, "饼图没有有效的数据行"
        
        for line in data_lines:
            parts = line.split(':')
            if len(parts) != 2:
                return False, f"数据行格式错误: {line}"
            try:
                value = float(parts[1].strip())
            except ValueError:
                return False, f"数值无效: {parts[1]}"
    
    # 流程图检查
    if first_line.startswith(('graph', 'flowchart')):
        if '-->' not in code and '--' not in code:
            return False, "流程图缺少连接关系"
    
    return True, "语法正确"


if __name__ == "__main__":
    # 测试
    test_codes = [
        # 测试1: 饼图
        '''pie title 测试饼图
    "项目A" : 35
    "项目B" : 25
    "项目C" : 40''',
        
        # 测试2: 流程图
        '''graph TD
    A[开始] --> B[处理]
    B --> C{判断}'''
    ]
    
    for i, code in enumerate(test_codes, 1):
        print(f"\n测试 {i}:")
        print("原始代码:")
        print(code)
        
        is_valid, msg = validate_mermaid_syntax(code)
        print(f"\n验证结果: {msg}")
        
        if is_valid:
            fixed = fix_mermaid_syntax(code)
            print("\n修复后:")
            print(fixed)

