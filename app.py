#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻量级任务看板 - Flask 后端
"""
import os
import re
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# 配置
TASKS_DIR = os.environ.get('TASKS_DIR', '/home/jetson/.openclaw/workspace/memory/tasks/checklists')

# 智能体颜色映射
AGENT_COLORS = {
    '老丑': 'blue',
    '钮码': 'red',
    '丑牛': 'green',
    '子鼠': 'yellow',
    '舆探': 'purple'
}

def parse_markdown_file(filepath):
    """解析 Markdown 任务文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取任务名称（第一行 # 后的内容）
        title_match = re.search(r'^# 任务清单[:：]\s*(.+)$', content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else os.path.basename(filepath)
        
        # 提取任务框架信息
        status_match = re.search(r'[-状态:]+[:：]\s*(🔄|✅|❌)\s*(进行中|已完成|已暂停)', content)
        status = status_match.group(1) if status_match else '🔄'
        status_text = status_match.group(2) if status_match else '进行中'
        
        # 提取创建时间
        created_match = re.search(r'创建时间[:：]\s*(\d{4}-\d{2}-\d{2}\s*\d{2}:\d{2})', content)
        created_at = created_match.group(1) if created_match else datetime.now().strftime('%Y-%m-%d %H:%M')
        
        # 提取负责人
        owner_match = re.search(r'负责人[:：]\s*(\S+)', content)
        owner = owner_match.group(1) if owner_match else '未分配'
        
        # 提取智能体标识
        agent_match = re.search(r'\[(🔵|🔴|🟢|🟡|🟣)\s*(\w+)\]', content)
        agent_icon = agent_match.group(1) if agent_match else '🔵'
        agent_name = agent_match.group(2) if agent_match else '老丑'
        
        # 计算进度
        total_checkboxes = len(re.findall(r'^\s*-\s*\[[x ]\]', content, re.MULTILINE))
        completed_checkboxes = len(re.findall(r'^\s*-\s*\[x\]', content, re.MULTILINE))
        progress = int(completed_checkboxes / total_checkboxes * 100) if total_checkboxes > 0 else 0
        
        # 提取当前 Phase
        phase_match = re.search(r'(Phase \d+[:：].*?(?=Phase \d+:|##|$))', content, re.DOTALL)
        current_phase = phase_match.group(1).strip().split('\n')[0] if phase_match else '未开始'
        
        return {
            'id': os.path.basename(filepath).replace('.md', ''),
            'title': title,
            'status': status,
            'status_text': status_text,
            'agent_icon': agent_icon,
            'agent_name': agent_name,
            'agent_color': AGENT_COLORS.get(agent_name, 'blue'),
            'progress': f"{completed_checkboxes}/{total_checkboxes}",
            'progress_percent': progress,
            'current_phase': current_phase,
            'created_at': created_at,
            'owner': owner,
            'filepath': filepath,
            'content': content[:500] + '...' if len(content) > 500 else content
        }
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return None

def get_tasks_by_status(tasks):
    """按状态分组任务"""
    planned = []
    in_progress = []
    completed = []
    
    for task in tasks:
        if task['status'] in ['🔄', '❌']:
            if task['status'] == '✅':
                completed.append(task)
            else:
                in_progress.append(task)
        else:
            planned.append(task)
    
    return planned, in_progress, completed

@app.route('/')
def index():
    """渲染主页面"""
    return render_template('index.html')

@app.route('/api/tasks')
def get_tasks():
    """获取所有任务"""
    tasks = []
    
    if os.path.exists(TASKS_DIR):
        for filename in os.listdir(TASKS_DIR):
            if filename.endswith('.md') and not filename.startswith('TEMPLATE'):
                filepath = os.path.join(TASKS_DIR, filename)
                task = parse_markdown_file(filepath)
                if task:
                    tasks.append(task)
    
    # 按状态分组
    planned, in_progress, completed = get_tasks_by_status(tasks)
    
    return jsonify({
        'planned': planned,
        'in_progress': in_progress,
        'completed': completed,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/tasks/<task_id>')
def get_task_detail(task_id):
    """获取任务详情"""
    filepath = os.path.join(TASKS_DIR, f"{task_id}.md")
    if os.path.exists(filepath):
        task = parse_markdown_file(filepath)
        if task:
            # 读取完整内容
            with open(filepath, 'r', encoding='utf-8') as f:
                task['full_content'] = f.read()
            return jsonify(task)
    
    return jsonify({'error': 'Task not found'}), 404

@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除任务"""
    filepath = os.path.join(TASKS_DIR, f"{task_id}.md")
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({'success': True})
    return jsonify({'error': 'Task not found'}), 404

@app.route('/api/sessions', methods=['POST'])
def create_session():
    """创建 OpenClaw 会话"""
    data = request.json
    # TODO: 实现 OpenClaw Sessions API 调用
    return jsonify({
        'session_id': 'demo-session-123',
        'message': '对话功能待集成 OpenClaw Sessions API'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
