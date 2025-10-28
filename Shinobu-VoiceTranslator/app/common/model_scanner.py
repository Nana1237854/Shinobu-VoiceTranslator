# coding:utf-8
"""Whisper 模型扫描工具"""
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple


class ModelScanner:
    """模型扫描器，用于自动发现和管理 Whisper 模型"""
    
    def __init__(self):
        # 获取应用根目录
        self.app_dir = Path(__file__).parent.parent
        self.whisper_faster_dir = self.app_dir / 'common' / 'models' / 'whisper-faster'
        self.param_file = self.whisper_faster_dir / 'param.txt'
    
    def scan_faster_whisper_models(self) -> List[str]:
        """
        扫描 whisper-faster 目录，查找所有 Faster-Whisper 模型
        
        Returns:
            模型名称列表，格式为 "faster-whisper-{model_name}"
        """
        models = []
        
        try:
            if not self.whisper_faster_dir.exists():
                print(f"[模型扫描] whisper-faster 目录不存在: {self.whisper_faster_dir}")
                return models
            
            # 扫描目录中的文件和文件夹
            for item in os.listdir(self.whisper_faster_dir):
                item_path = self.whisper_faster_dir / item
                
                # 跳过特殊文件
                if item in ['param.txt', 'transcribe.py', 'config.json']:
                    continue
                
                # 检查是否符合模型命名规则
                # 1. 以 faster-whisper 开头的文件/文件夹
                if item.startswith('faster-whisper'):
                    models.append(item)
                    print(f"[模型扫描] 发现模型: {item}")
                
                # 2. 包含 whisper-faster 的文件/文件夹
                elif 'whisper-faster' in item.lower():
                    models.append(item)
                    print(f"[模型扫描] 发现模型: {item}")
                
                # 3. 以 .exe 结尾的 whisper 相关文件
                elif item.endswith('faster.exe') or item.endswith('whisper.exe'):
                    models.append(item)
                    print(f"[模型扫描] 发现可执行文件: {item}")
                
                # 4. 检查是否为模型目录（包含 config.json 和 model.bin）
                elif item_path.is_dir():
                    if self._is_model_directory(item_path):
                        model_name = f"faster-whisper-{item}"
                        models.append(model_name)
                        print(f"[模型扫描] 发现模型目录: {item} -> {model_name}")
            
            # 去重并排序
            models = sorted(list(set(models)))
            
            if models:
                print(f"[模型扫描] 共发现 {len(models)} 个模型")
            else:
                print(f"[模型扫描] 未发现任何模型")
            
            return models
            
        except Exception as e:
            print(f"[模型扫描] 扫描失败: {e}")
            import traceback
            traceback.print_exc()
            return models
    
    def _is_model_directory(self, dir_path: Path) -> bool:
        """
        检查目录是否为有效的模型目录
        
        Args:
            dir_path: 目录路径
        
        Returns:
            如果包含必要的模型文件则返回 True
        """
        required_files = ['config.json', 'model.bin']
        
        for required_file in required_files:
            if not (dir_path / required_file).exists():
                return False
        
        return True
    
    def read_param_template(self) -> str:
        """
        读取参数模板文件
        
        Returns:
            参数模板内容
        """
        try:
            if not self.param_file.exists():
                print(f"[参数模板] 文件不存在: {self.param_file}")
                # 返回默认模板
                return self._get_default_template()
            
            with open(self.param_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"[参数模板] 已加载: {self.param_file}")
            return content
            
        except Exception as e:
            print(f"[参数模板] 读取失败: {e}")
            return self._get_default_template()
    
    def _get_default_template(self) -> str:
        """返回默认参数模板"""
        return """python
app/common/models/whisper-faster/transcribe.py
--model
$whisper_file
--input
$input_file
--language
$language
--output_dir
$output_dir"""
    
    def parse_param_template(self, template: str) -> List[str]:
        """
        解析参数模板，提取命令行参数
        
        Args:
            template: 参数模板内容
        
        Returns:
            参数列表（每行一个参数，忽略注释和空行）
        """
        lines = template.split('\n')
        params = []
        
        for line in lines:
            line = line.strip()
            
            # 跳过注释和空行
            if not line or line.startswith('#'):
                continue
            
            params.append(line)
        
        return params
    
    def prepare_command_args(self, template: str, **replacements) -> List[str]:
        """
        准备命令行参数，替换模板中的占位符
        
        Args:
            template: 参数模板
            **replacements: 占位符替换字典
                - $whisper_file: 模型名称
                - $input_file: 输入文件路径
                - $language: 源语言
                - $output_dir: 输出目录
        
        Returns:
            处理后的命令行参数列表
        """
        # 解析模板
        params = self.parse_param_template(template)
        
        # 替换占位符
        result = []
        for param in params:
            # 替换所有占位符
            for placeholder, value in replacements.items():
                param = param.replace(placeholder, str(value))
            
            result.append(param)
        
        return result
    
    def get_all_models(self) -> Dict[str, List[str]]:
        """
        获取所有可用的模型
        
        Returns:
            字典格式:
            {
                'faster-whisper': ['faster-whisper-large-v2', ...],
                'whisper': ['whisper-base', ...]
            }
        """
        models = {
            'faster-whisper': self.scan_faster_whisper_models(),
            'whisper': []  # 可以扩展 whisper.cpp 模型扫描
        }
        
        return models
    
    def get_model_display_name(self, model_name: str) -> str:
        """
        获取模型的显示名称
        
        Args:
            model_name: 模型内部名称
        
        Returns:
            用户友好的显示名称
        """
        # 移除 faster-whisper- 前缀
        if model_name.startswith('faster-whisper-'):
            display = model_name[15:]  # 去掉前15个字符
            return f"Faster-Whisper ({display})"
        
        return model_name


# 全局实例
modelScanner = ModelScanner()

