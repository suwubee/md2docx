"""
纯Python实现的Mermaid渲染器 - 使用matplotlib等库直接绘制
完全不依赖浏览器或Node.js
"""
import re
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import networkx as nx


class PurePythonMermaidRenderer:
    """纯Python Mermaid渲染器"""
    
    def __init__(self):
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'sans-serif']
        plt.rcParams['axes.unicode_minus'] = False
    
    def render(self, mermaid_code, output_path):
        """
        渲染Mermaid代码为PNG图片
        
        Args:
            mermaid_code: Mermaid代码
            output_path: 输出文件路径
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            # 识别图表类型
            first_line = mermaid_code.strip().split('\n')[0].lower()
            
            if first_line.startswith('pie'):
                return self._render_pie(mermaid_code, output_path)
            elif first_line.startswith(('graph', 'flowchart')):
                return self._render_graph(mermaid_code, output_path)
            elif first_line.startswith('gantt'):
                return self._render_gantt(mermaid_code, output_path)
            else:
                print(f"  ⚠ 不支持的图表类型: {first_line}")
                return False
                
        except Exception as e:
            print(f"  ✗ 渲染错误: {e}")
            return False
    
    def _render_pie(self, mermaid_code, output_path):
        """渲染饼图"""
        try:
            lines = mermaid_code.strip().split('\n')
            
            # 提取标题
            title = "饼图"
            if 'title' in lines[0]:
                title = lines[0].split('title', 1)[1].strip()
            
            # 提取数据
            labels = []
            sizes = []
            for line in lines[1:]:
                line = line.strip()
                if ':' in line:
                    parts = line.split(':')
                    if len(parts) == 2:
                        label = parts[0].strip().strip('"\'')
                        try:
                            value = float(parts[1].strip())
                            labels.append(label)
                            sizes.append(value)
                        except ValueError:
                            continue
            
            if not labels or not sizes:
                print(f"  ✗ 饼图数据为空")
                return False
            
            # 绘制饼图
            fig, ax = plt.subplots(figsize=(10, 7))
            
            # 颜色方案
            colors = plt.cm.Set3(range(len(labels)))
            
            # 绘制
            wedges, texts, autotexts = ax.pie(
                sizes, 
                labels=labels,
                autopct='%1.1f%%',
                startangle=90,
                colors=colors,
                textprops={'fontsize': 11}
            )
            
            # 美化百分比文字
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_weight('bold')
                autotext.set_fontsize(10)
            
            # 设置标题
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            
            # 图例
            ax.legend(wedges, labels, 
                     title="类别",
                     loc="center left",
                     bbox_to_anchor=(1, 0, 0.5, 1))
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            
            print(f"  → 使用matplotlib绘制成功")
            return True
            
        except Exception as e:
            print(f"  ✗ 饼图渲染失败: {e}")
            return False
    
    def _render_graph(self, mermaid_code, output_path):
        """渲染流程图/图结构"""
        try:
            lines = mermaid_code.strip().split('\n')
            
            # 解析图的方向
            first_line = lines[0].lower()
            if 'td' in first_line or 'tb' in first_line:
                layout = 'vertical'
            else:
                layout = 'horizontal'
            
            # 解析节点和边
            nodes = {}  # {id: label}
            edges = []  # [(from, to, label)]
            
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue
                
                # 解析边 A --> B 或 A -- label --> B
                if '-->' in line or '--' in line:
                    self._parse_edge(line, nodes, edges)
            
            if not nodes:
                print(f"  ⚠ 流程图没有节点")
                return False
            
            # 使用networkx创建图
            G = nx.DiGraph()
            
            # 添加节点
            for node_id, label in nodes.items():
                G.add_node(node_id, label=label)
            
            # 添加边
            for from_node, to_node, edge_label in edges:
                if from_node in nodes and to_node in nodes:
                    G.add_edge(from_node, to_node, label=edge_label)
            
            # 绘制
            fig, ax = plt.subplots(figsize=(12, 8))

            # 选择布局算法
            try:
                # 使用分层布局（适合有向图）
                if layout == 'vertical':
                    # 从上到下：使用graphviz的分层布局
                    pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
                else:
                    # 从左到右
                    pos = nx.nx_agraph.graphviz_layout(G, prog='dot', args='-Grankdir=LR')
            except:
                # 如果graphviz不可用，使用备用方案：多部图布局
                try:
                    # 使用shell_layout或kamada_kawai_layout
                    if layout == 'vertical':
                        # 分层手动布局
                        pos = self._hierarchical_layout(G, vertical=True)
                    else:
                        pos = self._hierarchical_layout(G, vertical=False)
                except:
                    # 最后备用：spring布局
                    print("  ⚠ 使用简单布局，复杂图表可能效果不佳")
                    if layout == 'vertical':
                        pos = nx.spring_layout(G, k=2, iterations=50)
                    else:
                        pos = nx.spring_layout(G, k=3, iterations=50)
            
            # 绘制节点
            for node, (x, y) in pos.items():
                label = nodes[node]
                
                # 判断节点形状
                if '{' in label:
                    # 菱形（判断节点）
                    shape = patches.FancyBboxPatch(
                        (x-0.15, y-0.08), 0.3, 0.16,
                        boxstyle="round,pad=0.02",
                        edgecolor='#4A90E2', facecolor='#E3F2FD',
                        linewidth=2
                    )
                elif '[' in label:
                    # 方形（普通节点）
                    shape = patches.Rectangle(
                        (x-0.15, y-0.08), 0.3, 0.16,
                        edgecolor='#4A90E2', facecolor='#E8F4F8',
                        linewidth=2
                    )
                else:
                    # 圆角矩形
                    shape = patches.FancyBboxPatch(
                        (x-0.15, y-0.08), 0.3, 0.16,
                        boxstyle="round,pad=0.02",
                        edgecolor='#4A90E2', facecolor='#F0F8FF',
                        linewidth=2
                    )
                
                ax.add_patch(shape)
                
                # 清理标签
                clean_label = label.replace('[', '').replace(']', '')
                clean_label = clean_label.replace('{', '').replace('}', '')
                clean_label = clean_label.strip()
                
                # 添加文字
                ax.text(x, y, clean_label, 
                       ha='center', va='center',
                       fontsize=10, fontweight='bold',
                       color='#333333')
            
            # 绘制边
            for from_node, to_node, edge_label in edges:
                if from_node in pos and to_node in pos:
                    x1, y1 = pos[from_node]
                    x2, y2 = pos[to_node]
                    
                    # 绘制箭头
                    arrow = FancyArrowPatch(
                        (x1, y1), (x2, y2),
                        arrowstyle='-|>',
                        color='#666666',
                        linewidth=2,
                        connectionstyle="arc3,rad=0.1",
                        mutation_scale=20
                    )
                    ax.add_patch(arrow)
                    
                    # 添加边标签
                    if edge_label:
                        mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
                        ax.text(mid_x, mid_y, edge_label,
                               fontsize=8, color='#666666',
                               bbox=dict(boxstyle='round,pad=0.3',
                                       facecolor='white',
                                       edgecolor='none',
                                       alpha=0.8))
            
            # 设置图形属性
            ax.set_xlim(-0.3, 1.3)
            ax.set_ylim(-0.3, 1.3)
            ax.axis('off')
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            
            print(f"  → 使用networkx+matplotlib绘制成功")
            return True
            
        except Exception as e:
            print(f"  ✗ 流程图渲染失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _parse_edge(self, line, nodes, edges):
        """解析边的定义"""
        # 匹配箭头
        if '-->' in line:
            parts = line.split('-->')
            arrow_type = '-->'
        elif '--->' in line:
            parts = line.split('--->')
            arrow_type = '--->'
        elif '--' in line:
            parts = line.split('--')
            arrow_type = '--'
        else:
            return
        
        if len(parts) < 2:
            return
        
        # 解析源节点
        from_part = parts[0].strip()
        from_id, from_label = self._parse_node(from_part)
        if from_id:
            nodes[from_id] = from_label
        
        # 解析目标节点（可能包含边标签）
        to_part = parts[1].strip()
        
        # 检查是否有边标签 |label|
        edge_label = ""
        if '|' in from_part:
            match = re.search(r'\|([^|]+)\|', from_part)
            if match:
                edge_label = match.group(1)
        
        to_id, to_label = self._parse_node(to_part)
        if to_id:
            nodes[to_id] = to_label
        
        # 添加边
        if from_id and to_id:
            edges.append((from_id, to_id, edge_label))
    
    def _parse_node(self, text):
        """解析节点定义，返回(id, label)"""
        text = text.strip()

        # A[label] 或 A{label} 格式
        match = re.match(r'([A-Za-z0-9_]+)\s*[\[\{]([^\]\}]+)[\]\}]', text)
        if match:
            node_id = match.group(1)
            label = match.group(2)
            return node_id, label

        # 简单的节点ID
        match = re.match(r'^([A-Za-z0-9_]+)', text)
        if match:
            node_id = match.group(1)
            return node_id, node_id

        return None, None

    def _hierarchical_layout(self, G, vertical=True):
        """
        手动实现分层布局算法
        适用于有向无环图（DAG）
        """
        import networkx as nx

        # 计算每个节点的层级
        try:
            # 找出所有没有入边的节点作为根节点
            roots = [n for n in G.nodes() if G.in_degree(n) == 0]
            if not roots:
                # 如果有环，随便选一个节点作为根
                roots = [list(G.nodes())[0]]

            # 使用BFS计算层级
            levels = {}
            current_level = roots
            level_num = 0
            visited = set()

            while current_level:
                next_level = []
                for node in current_level:
                    if node not in visited:
                        levels[node] = level_num
                        visited.add(node)
                        # 添加所有子节点到下一层
                        for successor in G.successors(node):
                            if successor not in visited:
                                next_level.append(successor)
                level_num += 1
                current_level = next_level

            # 为未访问的节点分配层级（处理孤立节点）
            for node in G.nodes():
                if node not in levels:
                    levels[node] = level_num

            # 计算每一层的节点数量，用于居中布局
            level_nodes = {}
            for node, level in levels.items():
                if level not in level_nodes:
                    level_nodes[level] = []
                level_nodes[level].append(node)

            # 生成位置
            pos = {}
            max_level = max(levels.values()) if levels else 0

            for node, level in levels.items():
                nodes_in_level = level_nodes[level]
                index_in_level = nodes_in_level.index(node)
                num_in_level = len(nodes_in_level)

                if vertical:
                    # 从上到下布局
                    x = (index_in_level - (num_in_level - 1) / 2) * 0.3
                    y = 1.0 - (level / max(max_level, 1)) * 0.8
                    pos[node] = (x, y)
                else:
                    # 从左到右布局
                    x = (level / max(max_level, 1)) * 0.8
                    y = (index_in_level - (num_in_level - 1) / 2) * 0.3
                    pos[node] = (x, y)

            return pos

        except Exception as e:
            print(f"  ⚠ 分层布局失败: {e}")
            # 返回简单的circular布局作为备用
            return nx.circular_layout(G)
    
    def _render_gantt(self, mermaid_code, output_path):
        """渲染甘特图"""
        try:
            lines = mermaid_code.strip().split('\n')
            
            # 提取标题
            title = "甘特图"
            tasks = []
            current_section = ""
            
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith('title'):
                    title = line.split('title', 1)[1].strip()
                elif line.startswith('section'):
                    current_section = line.split('section', 1)[1].strip()
                elif ':' in line:
                    # 解析任务
                    parts = line.split(':')
                    task_name = parts[0].strip()
                    tasks.append({
                        'name': task_name,
                        'section': current_section
                    })
            
            if not tasks:
                print(f"  ⚠ 甘特图没有任务")
                return False
            
            # 绘制简化的甘特图
            fig, ax = plt.subplots(figsize=(12, len(tasks) * 0.5 + 2))
            
            # 绘制任务条
            for i, task in enumerate(tasks):
                y_pos = len(tasks) - i - 1
                ax.barh(y_pos, 1, left=i*0.5, height=0.6, 
                       color='#4A90E2', alpha=0.7)
                ax.text(-0.1, y_pos, task['name'], 
                       ha='right', va='center', fontsize=10)
            
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            ax.set_yticks([])
            ax.set_xlabel('时间线', fontsize=12)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_visible(False)
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            
            print(f"  → 使用matplotlib绘制成功")
            return True
            
        except Exception as e:
            print(f"  ✗ 甘特图渲染失败: {e}")
            return False


if __name__ == "__main__":
    # 测试
    renderer = PurePythonMermaidRenderer()
    
    # 测试饼图
    pie_code = """pie title 测试饼图
    "项目A" : 35
    "项目B" : 25
    "项目C" : 40"""
    
    print("测试饼图...")
    if renderer.render(pie_code, "test_pie.png"):
        print("✓ 饼图生成成功: test_pie.png")
    
    # 测试流程图
    graph_code = """graph TD
    A[开始] --> B[处理]
    B --> C{判断}
    C -->|是| D[结束]
    C -->|否| B"""
    
    print("\n测试流程图...")
    if renderer.render(graph_code, "test_graph.png"):
        print("✓ 流程图生成成功: test_graph.png")

