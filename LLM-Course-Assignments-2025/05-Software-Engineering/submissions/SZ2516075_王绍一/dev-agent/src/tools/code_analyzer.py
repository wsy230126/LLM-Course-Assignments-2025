# src/tools/code_analyzer.py
import ast
import pylint.lint
from pylint.reporters.text import TextReporter

class CodeAnalyzer:
    """代码静态分析"""
    
    def analyze(self, code: str) -> Dict:
        """分析代码质量"""
        
        analysis = {
            "syntax_valid": False,
            "ast_analysis": {},
            "pylint_score": 0,
            "issues": [],
            "suggestions": []
        }
        
        # 检查语法
        try:
            tree = ast.parse(code)
            analysis["syntax_valid"] = True
            analysis["ast_analysis"] = self._analyze_ast(tree)
        except SyntaxError as e:
            analysis["issues"].append(f"语法错误: {e}")
            return analysis
        
        # 运行pylint
        pylint_result = self._run_pylint(code)
        analysis.update(pylint_result)
        
        return analysis
    
    def _run_pylint(self, code: str) -> Dict:
        """运行pylint检查"""
        import io
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # 捕获pylint输出
            pylint_output = io.StringIO()
            reporter = TextReporter(pylint_output)
            
            # 运行pylint
            pylint.lint.Run(
                ['--disable=all', '--enable=error', temp_file],
                reporter=reporter,
                exit=False
            )
            
            output = pylint_output.getvalue()
            
            return {
                "pylint_output": output,
                "issues": self._parse_pylint_output(output)
            }
        finally:
            os.unlink(temp_file)