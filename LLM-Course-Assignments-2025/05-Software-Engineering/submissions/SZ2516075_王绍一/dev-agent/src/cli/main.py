# src/cli/main.py
import click
import json
import tempfile
import subprocess
import time
import os
import sys
from typing import Dict, List, Optional, Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn

# 添加src到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from src.models.model_manager import ModelManager
    from src.agents.reflex_agent import ReflexAgent
    from src.datasets.humaneval_loader import HumanEvalLoader
    from src.evaluation.humaneval_eval import HumanEvalEvaluator
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保所有模块都已正确创建")
    # 创建缺失的类作为临时替代
    class ModelManager:
        def __init__(self, config_path):
            pass
        def get_model(self, model_name):
            return {"model": None, "tokenizer": None}
    
    class ReflexAgent:
        def __init__(self, model_info, max_iterations=3):
            self.model_info = model_info
            self.max_iterations = max_iterations
        
        def solve(self, requirement):
            return {"success": True, "final_code": "# 模拟生成的代码", "iterations": []}
    
    class HumanEvalLoader:
        def __init__(self, cache_dir=None):
            pass
        def load(self):
            return []
    
    class HumanEvalEvaluator:
        def __init__(self, model_manager, model_name):
            pass
        def evaluate(self, num_samples=10, progress=None):
            return {"stats": {}}

console = Console()

@click.group()
@click.option('--model', default='deepseek-coder-6.7b', 
              help='使用的模型')
@click.option('--config', default='config.yaml', 
              help='配置文件路径')
@click.pass_context
def cli(ctx, model, config):
    """AI驱动的软件开发助手"""
    ctx.ensure_object(dict)
    ctx.obj['model_name'] = model
    ctx.obj['config_path'] = config
    
    # 初始化模型管理器
    try:
        model_manager = ModelManager(config)
        ctx.obj['model_manager'] = model_manager
    except Exception as e:
        console.print(f"[red]初始化模型管理器失败: {e}[/red]")
        ctx.obj['model_manager'] = None

# @cli.command()
# @click.option('--prompt', '-p', help='编程需求描述')
# @click.option('--iterations', '-i', default=3, help='反思迭代次数')
# @click.option('--output', '-o', help='输出文件路径')
# @click.pass_context
# def generate(ctx, prompt, iterations, output):
#     """生成代码"""
    
#     if not ctx.obj['model_manager']:
#         console.print("[red]错误: 模型管理器未初始化[/red]")
#         return
    
#     if not prompt:
#         console.print("[red]错误: 请提供需求描述[/red]")
#         return
    
#     with Progress(
#         SpinnerColumn(),
#         TextColumn("[progress.description]{task.description}"),
#         transient=True,
#     ) as progress:
        
#         progress.add_task(description="初始化模型...", total=None)
#         model_info = ctx.obj['model_manager'].get_model(ctx.obj['model_name'])
        
#         progress.add_task(description="创建Agent...", total=None)
#         agent = ReflexAgent(model_info, max_iterations=iterations)
        
#         progress.add_task(description="处理需求...", total=None)
#         result = agent.solve(prompt)
    
#     # 显示结果
#     console.print(Panel.fit("🧠 AI代码助手 - 生成结果", style="bold blue"))
    
#     # 显示迭代过程
#     for i, iteration in enumerate(result.get("iterations", [])):
#         console.print(f"\n[bold cyan]迭代 {i+1}:[/bold cyan]")
        
#         if iteration.get("test_results", {}).get("all_passed", False):
#             console.print("✅ [green]所有测试通过[/green]")
#         else:
#             console.print("❌ [red]测试未通过[/red]")
        
#         reflection = iteration.get("reflection", "")
#         console.print(f"[yellow]反思:[/yellow] {reflection[:200]}..." if reflection else "")
    
#     # 显示最终代码
#     if result.get("success", False):
#         console.print("\n[bold green]🎉 成功生成代码！[/bold green]")
#         final_code = result.get("final_code", "")
#         syntax = Syntax(final_code, "python", theme="monokai", line_numbers=True)
#         console.print(Panel(syntax, title="最终代码", border_style="green"))
        
#         if output:
#             with open(output, 'w', encoding='utf-8') as f:
#                 f.write(final_code)
#             console.print(f"📁 代码已保存到: {output}")
#     else:
#         console.print("\n[bold red]❌ 未能生成通过测试的代码[/bold red]")
@cli.command()
@click.option('--prompt', '-p', help='编程需求描述')
@click.option('--simple', '-s', is_flag=True, help='使用简化模式')
@click.pass_context
def generate(ctx, prompt, simple):
    """生成代码"""
    
    console.print(Panel.fit("🚀 AI代码助手 - 小模型模式", style="bold blue"))
    
    if not prompt:
        console.print("[red]错误: 请提供需求描述[/red]")
        console.print("示例: devagent generate -p '写一个函数，反转字符串'")
        return
    
    # 获取模型
    model_info = ctx.obj['model_manager'].get_model()
    
    # 使用简化的生成器
    from src.models.simple_generator import SimpleCodeGenerator
    
    generator = SimpleCodeGenerator(model_info)
    
    with console.status("[bold green]正在生成代码..."):
        code = generator.generate_code(prompt)
    
    console.print("\n[bold green]✅ 代码生成完成！[/bold green]")
    
    # 显示代码
    syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title="生成的代码", border_style="green"))
    
    # 询问是否保存
    if click.confirm("\n💾 是否保存到文件？"):
        import re
        safe_name = re.sub(r'[^\w\s-]', '', prompt[:30]).strip().replace(' ', '_')
        
        with open(f"{safe_name}.py", 'w', encoding='utf-8') as f:
            f.write(code)
        
        console.print(f"📁 代码已保存到: {safe_name}.py")

@cli.command()
@click.option('--dataset', type=click.Choice(['humaneval', 'mbpp', 'swebench']), 
              default='humaneval', help='评估数据集')
@click.option('--num-samples', default=10, help='评估样本数量')
@click.option('--output', help='评估结果输出文件')
@click.pass_context
def evaluate(ctx, dataset, num_samples, output):
    """在基准数据集上评估模型"""
    
    if not ctx.obj['model_manager']:
        console.print("[red]错误: 模型管理器未初始化[/red]")
        return
    
    evaluator = HumanEvalEvaluator(ctx.obj['model_manager'], ctx.obj['model_name'])
    
    with Progress() as progress:
        task = progress.add_task("评估中...", total=num_samples)
        
        results = evaluator.evaluate(num_samples=num_samples, progress=progress)
    
    # 显示评估结果
    console.print(Panel.fit("📊 评估结果", style="bold blue"))
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("指标", style="dim")
    table.add_column("值", justify="right")
    
    stats = results.get('stats', {})
    table.add_row("通过率", f"{stats.get('pass_rate', 0):.2%}")
    table.add_row("平均执行时间", f"{stats.get('avg_execution_time', 0):.2f}s")
    table.add_row("平均迭代次数", f"{stats.get('avg_iterations', 0):.1f}")
    table.add_row("平均代码长度", f"{stats.get('avg_code_length', 0):.0f} 字符")
    
    console.print(table)
    
    if output:
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        console.print(f"📁 评估结果已保存到: {output}")

@cli.command()
@click.option('--host', default='127.0.0.1', help='Web服务器主机')
@click.option('--port', default=7860, help='Web服务器端口')
@click.pass_context
def web(ctx, host, port):
    """启动Web界面"""
    try:
        import gradio as gr
    except ImportError:
        console.print("[red]未安装Gradio，请运行: pip install gradio[/red]")
        return
    
    if not ctx.obj['model_manager']:
        console.print("[red]错误: 模型管理器未初始化[/red]")
        return
    
    model_info = ctx.obj['model_manager'].get_model(ctx.obj['model_name'])
    agent = ReflexAgent(model_info)
    
    def process_requirement(requirement, iterations):
        result = agent.solve(requirement)
        
        output = {
            "success": result.get("success", False),
            "final_code": result.get("final_code", ""),
            "iterations": len(result.get("iterations", [])),
            "reflections": [it.get("reflection", "")[:200] + "..." for it in result.get("iterations", [])]
        }
        
        return output.get("success", False), output.get("final_code", ""), str(output.get("iterations", 0))
    
    # 创建Gradio界面
    with gr.Blocks(title="AI代码助手") as demo:
        gr.Markdown("# 🧠 AI代码助手")
        
        with gr.Row():
            with gr.Column():
                requirement = gr.Textbox(
                    label="编程需求",
                    placeholder="请输入你的编程需求...",
                    lines=3
                )
                iterations = gr.Slider(
                    minimum=1, maximum=5, value=3,
                    label="反思迭代次数"
                )
                generate_btn = gr.Button("生成代码", variant="primary")
            
            with gr.Column():
                success = gr.Textbox(label="成功状态")
                final_code = gr.Code(
                    label="生成的代码",
                    language="python"
                )
                iterations_info = gr.Textbox(label="迭代信息")
        
        generate_btn.click(
            fn=process_requirement,
            inputs=[requirement, iterations],
            outputs=[success, final_code, iterations_info]
        )
    
    demo.launch(server_name=host, server_port=port)


# src/cli/main.py 中添加以下命令
@cli.command()
@click.option('--list-models', '-l', is_flag=True, help='列出所有可用模型')
@click.option('--model-info', '-m', help='查看指定模型信息')
@click.pass_context
def models(ctx, list_models, model_info):
    """模型管理命令"""
    model_manager = ctx.obj['model_manager']
    
    if list_models:
        console.print(Panel.fit("📋 可用模型列表", style="bold blue"))
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("模型名称", style="dim")
        table.add_column("类型", justify="center")
        table.add_column("大小(GB)", justify="right")
        table.add_column("最大长度", justify="right")
        table.add_column("状态", justify="center")
        
        for model_name in model_manager.list_available_models():
            info = model_manager.get_model_info(model_name)
            model_type = info.get('type', '未知')
            size = info.get('size_gb', '?')
            max_tokens = info.get('max_tokens', '?')
            
            # 检查是否已加载
            status = "✅ 已加载" if model_name in model_manager.models else "⏳ 未加载"
            
            table.add_row(model_name, model_type, str(size), str(max_tokens), status)
        
        console.print(table)
        
    elif model_info:
        info = model_manager.get_model_info(model_info)
        if info:
            console.print(Panel.fit(f"📊 模型信息: {model_info}", style="bold blue"))
            
            info_table = Table(show_header=False, box=None)
            info_table.add_column("属性", style="dim")
            info_table.add_column("值")
            
            for key, value in info.items():
                info_table.add_row(key, str(value))
            
            console.print(info_table)
        else:
            console.print(f"[red]❌ 未找到模型: {model_info}[/red]")
    
    else:
        console.print("使用 --list-models 查看所有可用模型")
        console.print("使用 --model-info <模型名> 查看具体信息")

if __name__ == "__main__":
    cli()