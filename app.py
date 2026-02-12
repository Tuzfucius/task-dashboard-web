#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻量级任务看板 - Flask 后端 V2
"""
import os
import re
import json
import shutil
from datetime import datetime
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# 配置
TASKS_DIR = os.environ.get('TASKS_DIR', '/home/jetson/.openclaw/workspace/memory/tasks/checklists')
ARCHIVED_DIR = os.environ.get('ARCHIVED_DIR', '/home/jetson/.openclaw/workspace/memory/tasks/archived')

# 确保归档目录存在
os.makedirs(ARCHIVED_DIR, exist_ok=True)

# 智能体颜色映射
AGENT_COLORS = {
    '老丑': 'blue',
    '钮码': 'red',
    '丑牛': 'green',
    '子鼠': 'yellow',
    '舆探': 'purple'
}

# 智能体图标映射
AGENT_ICONS = {
    '老丑': '🔵',
    '钮码': '🔴',
    '丑牛': '🟢',
    '子鼠': '🟡',
    '舆探': '🟣'
}

def parse_markdown_file(filepath, include_full=False):
    """解析 Markdown 任务文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return _parse_content(content, filepath, include_full)
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return None

def _parse_content(content, filepath=None, include_full=False):
    """解析 Markdown 内容"""
    
    # 🔴 Bug 4 Fix: 增强任务名称解析（支持多种格式）
    # 格式1: # 任务清单: AI Agents 汉化项目
    # 格式2: # 任务清单：AI Agents 汉化项目  
    # 格式3: # 任务清单
    #         AI Agents 汉化项目
    title_match = re.search(r'^# 任务清单[:：]?\s*(.+)$', content, re.MULTILINE)
    if title_match:
        title = title_match.group(1).strip()
        # 如果标题太长或包含换行，继续查找
        if len(title) > 100 or '\n' in title:
            title = re.split(r'[\n\r]', title)[0].strip()
    else:
        # 尝试从第一行获取
        lines = content.strip().split('\n')
        for line in lines:
            if line.startswith('#'):
                title = line.lstrip('#').strip()
                if title and len(title) < 100:
                    break
        else:
            title = '未命名任务'
    
    # 🔴 Bug 3 Fix: 增强智能体识别（支持多种格式）
    # 格式1: [🔵 老丑] - 原格式
    # 格式2: - **智能体**: 老丑
    # 格式3: - 负责人: 老丑 (默认)
    # 格式4: - Agent: 老丑
    agent_match = re.search(r'\[(🔵|🔴|🟢|🟡|🟣)\s*(\w+)\]', content)
    if agent_match:
        agent_icon = agent_match.group(1)
        agent_name = agent_match.group(2)
    else:
        # 尝试其他格式
        agent_alt_match = re.search(r'[-*]\s*[*]?智能体[*]?[:：]\s*(\w+)', content)
        if agent_alt_match:
            agent_name = agent_alt_match.group(1)
            agent_icon = AGENT_ICONS.get(agent_name, '🔵')
        else:
            # 从文件名推断（如果文件名包含 agent 名称）
            filename = os.path.basename(filepath) if filepath else ''
            for name in AGENT_COLORS.keys():
                if name in filename:
                    agent_name = name
                    agent_icon = AGENT_ICONS.get(name, '🔵')
                    break
            else:
                # 默认老丑
                agent_name = '老丑'
                agent_icon = '🔵'
    
    # 🔴 Bug 1 Fix: 增强状态提取（支持更多格式）
    # 格式: - **状态**: 🔄 进行中 / 状态: 🔄 进行中 / - 状态: 🔄 进行中
    status_match = re.search(r'[-*]\s*[*]?状态[*]?[:：]\s*(🔄|✅|❌)\s*(进行中|已完成|已暂停)', content)
    if not status_match:
        status_match = re.search(r'状态[:：]\s*(🔄|✅|❌)\s*(进行中|已完成|已暂停)', content)
    
    status = status_match.group(1) if status_match else '🔄'
    status_text = status_match.group(2) if status_match else '进行中'
    
    # 提取创建时间
    created_match = re.search(r'创建时间[:：]\s*(\d{4}-\d{2}-\d{2}\s*\d{2}:\d{2})', content)
    created_at = created_match.group(1) if created_match else datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # 提取更新时间
    updated_match = re.search(r'更新时间[:：]\s*(\d{4}-\d{2}-\d{2}\s*\d{2}:\d{2})', content)
    updated_at = updated_match.group(1) if updated_match else created_at
    
    # 🔴 Bug 3 Fix: 提取负责人（增强格式支持）
    owner_match = re.search(r'[-*]\s*[*]?负责人[*]?[:：]\s*(\S+)', content)
    if not owner_match:
        owner_match = re.search(r'[-*]\s*[*]?Owner[*]?[:：]\s*(\S+)', content)
    owner = owner_match.group(1) if owner_match else '未分配'
    
    # 提取智能体标识
    agent_match = re.search(r'\[(🔵|🔴|🟢|🟡|🟣)\s*(\w+)\]', content)
    agent_icon = agent_match.group(1) if agent_match else '🔵'
    agent_name = agent_match.group(2) if agent_match else '老丑'
    
    # 提取排序优先级
    order_match = re.search(r'排序[:：]\s*(\d+)', content)
    sort_order = int(order_match.group(1)) if order_match else 999
    
    # 计算进度
    total_checkboxes = len(re.findall(r'^\s*-\s*\[[x ]\]', content, re.MULTILINE))
    completed_checkboxes = len(re.findall(r'^\s*-\s*\[x\]', content, re.MULTILINE))
    progress = int(completed_checkboxes / total_checkboxes * 100) if total_checkboxes > 0 else 0
    
    # 提取当前 Phase（支持 UltraWork 格式）
    # 格式1: Phase 1: 准备阶段
    # 格式2: ## Phase 1: 准备阶段
    phase_match = re.search(r'(Phase \d+[:：]?\s*(?:.*?))(?=Phase \d+|## |$)', content, re.DOTALL)
    current_phase = phase_match.group(1).strip().split('\n')[0] if phase_match else '未开始'
    
    # 🟡 P1 Feature 7: 提取所有 Phases（支持 UltraWork 格式）
    phases = re.findall(r'(Phase \d+[:：]?\s*(?:.*?))(?=Phase \d+|## |$)', content, re.DOTALL)
    phase_list = []
    for i, phase in enumerate(phases):
        phase_name = phase.split('\n')[0].strip()
        phase_tasks = re.findall(r'- \[ \]\s*(.+)|- \[x\]\s*(.+)', phase)
        completed = sum(1 for t in phase_tasks if t[1])
        total = len(phase_tasks)
        phase_list.append({
            'id': f'phase_{i+1}',
            'name': phase_name,
            'tasks': [{'name': t[0] or t[1], 'completed': bool(t[1])} for t in phase_tasks],
            'progress': int(completed / total * 100) if total > 0 else 0
        })
    
    # 提取阻塞点
    blocker_match = re.search(r'阻塞点[:：]?\s*(.+?)(?=\n## |\n$|$)', content, re.DOTALL)
    blocker = blocker_match.group(1).strip() if blocker_match else None
    
    # 提取执行记录
    execution_match = re.findall(r'(\d{4}-\d{2}-\d{2}\s*\d{2}:\d{2})[:：]\s*(.+?)(?=\n\d{4}-\d{2}-\d{2}|## |$)', content, re.DOTALL)
    execution_records = [{'time': t, 'action': a.strip()} for t, a in execution_match[:5]] if execution_match else []
    
    task = {
        'id': os.path.basename(filepath).replace('.md', '') if filepath else 'unknown',
        'title': title,
        'status': status,
        'status_text': status_text,
        'agent_icon': agent_icon,
        'agent_name': agent_name,
        'agent_color': AGENT_COLORS.get(agent_name, 'blue'),
        'sort_order': sort_order,
        'progress': f"{completed_checkboxes}/{total_checkboxes}",
        'progress_percent': progress,
        'current_phase': current_phase,
        'phase_list': phase_list,  # 🟡 P1 Feature 7: 添加所有 Phases
        'created_at': created_at,
        'updated_at': updated_at,
        'owner': owner,
        'blocker': blocker,
        'execution_records': execution_records,
        'filepath': filepath
    }
    
    if include_full:
        task['full_content'] = content
    
    return task

def get_tasks_by_status(tasks):
    """按状态分组任务"""
    planned = []
    in_progress = []
    completed = []
    
    for task in tasks:
        if task['status'] == '✅':
            completed.append(task)
        elif task['status'] == '🔄':
            in_progress.append(task)
        else:
            planned.append(task)
    
    # 按排序优先级排序
    planned.sort(key=lambda x: x.get('sort_order', 999))
    in_progress.sort(key=lambda x: x.get('sort_order', 999))
    completed.sort(key=lambda x: x.get('sort_order', 999))
    
    return planned, in_progress, completed

def get_all_tasks_from_dir(directory, include_full=False):
    """从目录获取所有任务"""
    tasks = []
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            if filename.endswith('.md') and not filename.startswith('TEMPLATE'):
                filepath = os.path.join(directory, filename)
                task = parse_markdown_file(filepath, include_full)
                if task:
                    tasks.append(task)
    return tasks

@app.route('/')
def index():
    """渲染主页面"""
    return render_template('index.html')

@app.route('/api/tasks')
def get_tasks():
    """获取所有任务"""
    tasks = get_all_tasks_from_dir(TASKS_DIR)
    
    # 按状态分组
    planned, in_progress, completed = get_tasks_by_status(tasks)
    
    # 统计信息
    stats = {
        'total': len(tasks),
        'planned': len(planned),
        'in_progress': len(in_progress),
        'completed': len(completed),
        'by_agent': {}
    }
    
    # 按智能体统计
    for task in tasks:
        agent = task['agent_name']
        if agent not in stats['by_agent']:
            stats['by_agent'][agent] = 0
        stats['by_agent'][agent] += 1
    
    return jsonify({
        'planned': planned,
        'in_progress': in_progress,
        'completed': completed,
        'stats': stats,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/tasks/<task_id>')
def get_task_detail(task_id):
    """获取任务详情"""
    filepath = os.path.join(TASKS_DIR, f"{task_id}.md")
    if not os.path.exists(filepath):
        # 检查归档目录
        filepath = os.path.join(ARCHIVED_DIR, f"{task_id}.md")
    
    if os.path.exists(filepath):
        task = parse_markdown_file(filepath, include_full=True)
        if task:
            return jsonify(task)
    
    return jsonify({'error': 'Task not found'}), 404

@app.route('/api/tasks', methods=['POST'])
def create_task():
    """创建新任务"""
    data = request.json
    title = data.get('title', '新任务')
    owner = data.get('owner', '未分配')
    agent = data.get('agent', '老丑')
    sort_order = data.get('sort_order', 999)
    
    # 生成任务ID
    task_id = datetime.now().strftime('%Y%m%d%H%M%S')
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # 任务内容模板
    content = f"""# 任务清单：{title}

- 状态: 🔄 进行中
- 创建时间: {created_at}
- 更新时间: {created_at}
- 负责人: {owner}
- 排序: {sort_order}
- [{AGENT_ICONS.get(agent, '🔵')} {agent}]

## 任务描述

<!-- 在此添加任务描述 -->

## Phase 1: 准备阶段

- [ ] 明确任务目标和范围
- [ ] 制定详细计划
- [ ] 分配资源

## Phase 2: 执行阶段

- [ ] 执行核心任务
- [ ] 定期检查进度
- [ ] 解决遇到的问题

## Phase 3: 收尾阶段

- [ ] 完成任务验收
- [ ] 编写文档
- [ ] 总结经验

## 执行记录

{created_at}: 任务创建

## 阻塞点

<!-- 在此记录阻塞点 -->

"""
    
    filepath = os.path.join(TASKS_DIR, f"{task_id}.md")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return jsonify({
        'success': True,
        'task_id': task_id,
        'message': '任务创建成功'
    })

@app.route('/api/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    """更新任务"""
    data = request.json
    filepath = os.path.join(TASKS_DIR, f"{task_id}.md")
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'Task not found'}), 404
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
    # 🔴 Bug 1 Fix: 增强状态更新逻辑
    # 确保状态行格式统一
    if 'status' in data:
        # 查找并替换状态行，支持多种格式
        old_patterns = [
            r'[-*]\s*[*]?状态[*]?[:：]\s*(🔄|✅|❌)\s*(进行中|已完成|已暂停)',
            r'状态[:：]\s*(🔄|✅|❌)\s*(进行中|已完成|已暂停)',
            r'状态:\s*(🔄|✅|❌)\s*(进行中|已完成|已暂停)'
        ]
        for pattern in old_patterns:
            if re.search(pattern, content):
                content = re.sub(
                    pattern,
                    f"状态: {data['status']} {'进行中' if data['status'] == '🔄' else '已完成' if data['status'] == '✅' else '已暂停'}",
                    content
                )
                break
        
        # 更新排序
        if 'sort_order' in data:
            content = re.sub(
                r'排序[:：]\s*\d+',
                f"排序: {data['sort_order']}",
                content
            )
        
        # 更新时间
        updated_at = datetime.now().strftime('%Y-%m-%d %H:%M')
        content = re.sub(
            r'更新时间[:：]\s*\d{4}-\d{2}-\d{2}\s*\d{2}:\d{2}',
            f'更新时间: {updated_at}',
            content
        )
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({'success': True, 'updated_at': updated_at})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除任务"""
    filepath = os.path.join(TASKS_DIR, f"{task_id}.md")
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({'success': True})
    return jsonify({'error': 'Task not found'}), 404

@app.route('/api/tasks/archive/<task_id>', methods=['POST'])
def archive_task(task_id):
    """归档任务"""
    filepath = os.path.join(TASKS_DIR, f"{task_id}.md")
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'Task not found'}), 404
    
    try:
        # 移动到归档目录
        archive_path = os.path.join(ARCHIVED_DIR, f"{task_id}.md")
        
        # 添加归档标记到内容
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        archived_at = datetime.now().strftime('%Y-%m-%d %H:%M')
        content = f"---\narchived_at: {archived_at}\n---\n\n{content}"
        
        with open(archive_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 删除原文件
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'message': f'任务已归档'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/move/<task_id>', methods=['POST'])
def move_task(task_id):
    """移动任务状态"""
    data = request.json
    new_status = data.get('status', 'in_progress')  # planned, in_progress, completed
    
    status_map = {
        'planned': '🔄',
        'in_progress': '🔄',
        'completed': '✅'
    }
    
    status_text_map = {
        'planned': '进行中',
        'in_progress': '进行中',
        'completed': '已完成'
    }
    
    status_icon = status_map.get(new_status, '🔄')
    status_text = status_text_map.get(new_status, '进行中')
    
    filepath = os.path.join(TASKS_DIR, f"{task_id}.md")
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'Task not found'}), 404
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        updated_at = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        # 🔴 Bug 1 Fix: 支持多种状态格式
        status_patterns = [
            r'[-*]\s*[*]?状态[*]?[:：]\s*(🔄|✅|❌)\s*(进行中|已完成|已暂停)',
            r'状态[:：]\s*(🔄|✅|❌)\s*(进行中|已完成|已暂停)',
            r'状态:\s*(🔄|✅|❌)\s*(进行中|已完成|已暂停)'
        ]
        
        for pattern in status_patterns:
            if re.search(pattern, content):
                content = re.sub(
                    pattern,
                    f'状态: {status_icon} {status_text}',
                    content
                )
                break
        
        # 更新时间
        content = re.sub(
            r'更新时间[:：]\s*\d{4}-\d{2}-\d{2}\s*\d{2}:\d{2}',
            f'更新时间: {updated_at}',
            content
        )
        
        # 添加执行记录
        execution_note = data.get('note', '')
        if execution_note:
            record = f"\n{updated_at}: {execution_note}\n"
            # 如果执行记录部分不存在，先创建
            if '## 执行记录' not in content:
                # 在内容末尾添加执行记录部分
                content += f"\n\n## 执行记录\n{record}"
            else:
                content = re.sub(
                    r'(## 执行记录)',
                    f'## 执行记录{record}',
                    content
                )
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({
            'success': True,
            'status': new_status,
            'updated_at': updated_at
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/archive')
def get_archived_tasks():
    """获取归档任务列表"""
    tasks = get_all_tasks_from_dir(ARCHIVED_DIR)
    return jsonify({
        'archived': tasks,
        'count': len(tasks)
    })

@app.route('/api/archive/<task_id>', methods=['POST'])
def restore_archived_task(task_id):
    """恢复归档任务"""
    archive_path = os.path.join(ARCHIVED_DIR, f"{task_id}.md")
    
    if not os.path.exists(archive_path):
        return jsonify({'error': 'Archived task not found'}), 404
    
    try:
        with open(archive_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 移除归档标记
        content = re.sub(r'^---\n.*?---\n', '', content, flags=re.DOTALL)
        
        # 移动回任务目录
        filepath = os.path.join(TASKS_DIR, f"{task_id}.md")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 删除归档文件
        os.remove(archive_path)
        
        return jsonify({'success': True, 'message': '任务已恢复'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/archive/<task_id>', methods=['DELETE'])
def delete_archived_task(task_id):
    """永久删除归档任务"""
    archive_path = os.path.join(ARCHIVED_DIR, f"{task_id}.md")
    
    if not os.path.exists(archive_path):
        return jsonify({'error': 'Archived task not found'}), 404
    
    try:
        os.remove(archive_path)
        return jsonify({'success': True, 'message': '任务已永久删除'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/send', methods=['POST'])
def send_to_session():
    """发送消息到 OpenClaw 会话"""
    data = request.json
    task_id = data.get('task_id')
    message = data.get('message')
    
    # 记录到任务文件
    if task_id:
        filepath = os.path.join(TASKS_DIR, f"{task_id}.md")
        if os.path.exists(filepath):
            updated_at = datetime.now().strftime('%Y-%m-%d %H:%M')
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 添加消息记录
            content = re.sub(
                r'(## 执行记录)',
                f'## 执行记录\n{updated_at}: [用户消息] {message}\n',
                content
            )
            
            # 更新状态为进行中
            content = re.sub(
                r'状态[:：]\s*✅\s*已完成',
                '状态: 🔄 进行中',
                content
            )
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
    
    return jsonify({
        'success': True,
        'message': '消息已记录',
        'response': f'收到消息: {message}'
    })

@app.route('/api/stats')
def get_stats():
    """获取统计信息"""
    tasks = get_all_tasks_from_dir(TASKS_DIR)
    
    # 计算统计数据
    total = len(tasks)
    completed = len([t for t in tasks if t['status'] == '✅'])
    in_progress = len([t for t in tasks if t['status'] == '🔄'])
    
    # 按智能体统计
    by_agent = {}
    for task in tasks:
        agent = task['agent_name']
        if agent not in by_agent:
            by_agent[agent] = {'total': 0, 'completed': 0}
        by_agent[agent]['total'] += 1
        if task['status'] == '✅':
            by_agent[agent]['completed'] += 1
    
    return jsonify({
        'total': total,
        'completed': completed,
        'in_progress': in_progress,
        'planned': total - completed - in_progress,
        'completion_rate': int(completed / total * 100) if total > 0 else 0,
        'by_agent': by_agent
    })

@app.route('/api/health')
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'tasks_dir': TASKS_DIR,
        'archived_dir': ARCHIVED_DIR
    })

# 🟢 P2: UltraWork 格式支持
@app.route('/api/ultrawork/parse', methods=['POST'])
def parse_ultrawork():
    """解析 UltraWork 任务格式"""
    data = request.json
    content = data.get('content', '')
    
    # UltraWork 格式: Phase 1: xxx / Task 1: xxx
    phases = re.findall(r'(Phase \d+[:：]?\s*(?:.*?))(?=Phase \d+|## |$)', content, re.DOTALL)
    tasks = re.findall(r'(Task \d+[:：]?\s*(?:.*?))(?=Task \d+|Phase|## |$)', content, re.DOTALL)
    
    phase_list = []
    for i, phase in enumerate(phases):
        phase_name = phase.split('\n')[0].strip()
        phase_tasks = re.findall(r'- \[ \]\s*(.+)|- \[x\]\s*(.+)', phase)
        completed = sum(1 for t in phase_tasks if t[1])
        total = len(phase_tasks)
        phase_list.append({
            'id': f'phase_{i+1}',
            'name': phase_name,
            'tasks': [{'name': t[0] or t[1], 'completed': bool(t[1])} for t in phase_tasks],
            'progress': int(completed / total * 100) if total > 0 else 0
        })
    
    return jsonify({
        'phases': phase_list,
        'total_phases': len(phase_list),
        'total_tasks': len(tasks)
    })

# 🟡 P1: Jobs 任务 API (定时/轮巡任务)
JOBS_FILE = os.path.join(TASKS_DIR, '..', 'jobs.json')

def get_jobs():
    """获取 Jobs 列表"""
    if os.path.exists(JOBS_FILE):
        with open(JOBS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_jobs(jobs):
    """保存 Jobs 列表"""
    with open(JOBS_FILE, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)

@app.route('/api/jobs')
def get_jobs_list():
    """获取所有 Jobs"""
    jobs = get_jobs()
    return jsonify({
        'jobs': jobs,
        'count': len(jobs)
    })

@app.route('/api/jobs', methods=['POST'])
def create_job():
    """创建新 Job"""
    data = request.json
    jobs = get_jobs()
    
    job = {
        'id': datetime.now().strftime('%Y%m%d%H%M%S'),
        'name': data.get('name', '未命名任务'),
        'command': data.get('command', ''),
        'schedule': data.get('schedule', ''),  # cron 表达式
        'enabled': data.get('enabled', True),
        'last_run': data.get('last_run', None),
        'next_run': data.get('next_run', None),
        'history': [],
        'created_at': datetime.now().isoformat()
    }
    
    jobs.append(job)
    save_jobs(jobs)
    
    return jsonify({
        'success': True,
        'job': job
    })

@app.route('/api/jobs/<job_id>', methods=['PUT'])
def update_job(job_id):
    """更新 Job"""
    data = request.json
    jobs = get_jobs()
    
    for job in jobs:
        if job['id'] == job_id:
            job.update({
                'name': data.get('name', job['name']),
                'command': data.get('command', job['command']),
                'schedule': data.get('schedule', job['schedule']),
                'enabled': data.get('enabled', job['enabled']),
                'updated_at': datetime.now().isoformat()
            })
            save_jobs(jobs)
            return jsonify({'success': True, 'job': job})
    
    return jsonify({'error': 'Job not found'}), 404

@app.route('/api/jobs/<job_id>/run', methods=['POST'])
def run_job(job_id):
    """手动运行 Job"""
    jobs = get_jobs()
    
    for job in jobs:
        if job['id'] == job_id:
            # 记录运行历史
            run_time = datetime.now().isoformat()
            job['last_run'] = run_time
            job['history'].append({
                'run_at': run_time,
                'status': 'success',  # 简化处理
                'output': 'Job executed'
            })
            # 保留最近 10 条记录
            job['history'] = job['history'][-10:]
            save_jobs(jobs)
            return jsonify({'success': True, 'job': job})
    
    return jsonify({'error': 'Job not found'}), 404

@app.route('/api/jobs/<job_id>', methods=['DELETE'])
def delete_job(job_id):
    """删除 Job"""
    jobs = get_jobs()
    jobs = [j for j in jobs if j['id'] != job_id]
    save_jobs(jobs)
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
