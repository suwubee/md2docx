from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
import os
import tempfile
from datetime import datetime
from md_to_docx_converter import convert_markdown_to_docx, check_pandoc_installation

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件大小为16MB
app.config['TEMPLATES_FOLDER'] = 'templates_docx'

# 确保模板文件夹存在
os.makedirs(app.config['TEMPLATES_FOLDER'], exist_ok=True)

# 启动时检查Pandoc安装
print("正在检查Pandoc安装状态...")
if not check_pandoc_installation():
    print("\n警告: Pandoc未正确安装，转换功能可能无法使用！")

def get_available_templates():
    """获取所有可用的.dotx模板文件"""
    templates = []
    if os.path.exists(app.config['TEMPLATES_FOLDER']):
        for file in os.listdir(app.config['TEMPLATES_FOLDER']):
            if file.endswith('.dotx'):
                templates.append(file)
    
    # 同时检查项目根目录的.dotx文件
    for file in os.listdir('.'):
        if file.endswith('.dotx'):
            templates.append(file)
    
    return sorted(list(set(templates)))

@app.route('/')
def index():
    """主页面"""
    templates = get_available_templates()
    return render_template('index.html', templates=templates)

@app.route('/api/templates', methods=['GET'])
def list_templates():
    """API接口：获取模板列表"""
    templates = get_available_templates()
    return jsonify({
        'success': True,
        'templates': templates
    })

@app.route('/convert', methods=['POST'])
def convert():
    """转换Markdown到DOCX"""
    temp_output_path = None
    try:
        # 获取表单数据
        markdown_text = request.form.get('markdown_text', '')
        template_name = request.form.get('template', '')
        output_filename = request.form.get('output_filename', 'output.docx')
        
        print(f"\n{'='*60}")
        print(f"开始转换...")
        print(f"Markdown长度: {len(markdown_text)} 字符")
        print(f"模板: {template_name if template_name else '无（使用默认）'}")
        print(f"输出文件名: {output_filename}")
        
        if not markdown_text:
            return jsonify({
                'success': False,
                'error': '请输入Markdown内容'
            }), 400
        
        # 确保文件名以.docx结尾
        if not output_filename.endswith('.docx'):
            output_filename += '.docx'
        
        output_filename = secure_filename(output_filename)
        
        # 查找模板文件
        template_path = None
        if template_name:
            if os.path.exists(os.path.join(app.config['TEMPLATES_FOLDER'], template_name)):
                template_path = os.path.join(app.config['TEMPLATES_FOLDER'], template_name)
                print(f"✓ 找到模板: {template_path}")
            elif os.path.exists(template_name):
                template_path = template_name
                print(f"✓ 找到模板: {template_path}")
            else:
                print(f"⚠ 模板文件未找到: {template_name}，将使用默认样式")
        
        # 创建临时文件用于输出
        temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
        temp_output_path = temp_output.name
        temp_output.close()
        print(f"临时文件: {temp_output_path}")
        
        # 执行转换
        print("正在调用Pandoc转换...")
        convert_markdown_to_docx(
            markdown_text=markdown_text,
            output_path=temp_output_path,
            template_path=template_path
        )
        
        # 检查文件是否生成
        if not os.path.exists(temp_output_path):
            raise Exception("转换失败：输出文件未生成")
        
        file_size = os.path.getsize(temp_output_path)
        print(f"✓ 转换成功！文件大小: {file_size} 字节")
        print(f"{'='*60}\n")
        
        # 发送文件给用户
        return send_file(
            temp_output_path,
            as_attachment=True,
            download_name=output_filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ 转换失败！")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        
        # 导入traceback以获取详细错误
        import traceback
        print(f"详细错误:\n{traceback.format_exc()}")
        print(f"{'='*60}\n")
        
        # 清理临时文件
        if temp_output_path and os.path.exists(temp_output_path):
            try:
                os.remove(temp_output_path)
            except:
                pass
        
        return jsonify({
            'success': False,
            'error': f'转换失败: {str(e)}'
        }), 500

@app.route('/preview', methods=['POST'])
def preview():
    """预览Markdown渲染效果"""
    try:
        markdown_text = request.form.get('markdown_text', '')
        if not markdown_text:
            return jsonify({
                'success': False,
                'error': '没有内容可预览'
            }), 400
        
        # 使用markdown库渲染为HTML
        import markdown
        html = markdown.markdown(
            markdown_text,
            extensions=['tables', 'fenced_code', 'nl2br']
        )
        
        return jsonify({
            'success': True,
            'html': html
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'预览失败: {str(e)}'
        }), 500

if __name__ == '__main__':
    print("=" * 60)
    print("Markdown转DOCX Web应用")
    print("=" * 60)
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"可用模板: {len(get_available_templates())} 个")
    print("=" * 60)
    print("请在浏览器中访问: http://127.0.0.1:5000")
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)


