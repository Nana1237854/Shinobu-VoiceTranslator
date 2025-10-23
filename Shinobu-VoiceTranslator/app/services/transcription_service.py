# coding:utf-8
"""听写服务"""
import os
import re
import sys
import json
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from PySide6.QtCore import Signal

import openpyxl
from openpyxl.styles import Font, Alignment

from ..common.database.entity.task import Task, TaskStatus, TaskType
from ..common.database import getTaskService
from .base_service import BaseService
from ..common.signal_bus import signalBus
from ..common.concurrent import Future, FutureFailed
from ..common.config import cfg


class WhisperEngine:
    """Whisper 引擎类型"""
    GGML = "ggml"  # whisper.cpp
    FASTER_WHISPER = "faster-whisper"
    NONE = "不进行听写"


class OutputFormat:
    """输出格式"""
    SRT_ORIGINAL = "原文SRT"
    SRT_BILINGUAL = "双语SRT"
    LRC_ORIGINAL = "原文LRC"
    TXT_ORIGINAL = "原文TXT"
    TXT_BILINGUAL = "双语TXT"
    XLSX_ORIGINAL = "原文XLSX"
    XLSX_BILINGUAL = "双语XLSX"


class TranscriptionService(BaseService):
    """听写服务 - 使用 TaskExecutor 进行线程管理"""
    
    taskCreated = Signal(Task)   # 任务创建信号
    taskUpdated = Signal(Task)   # 任务更新信号
    taskFinished = Signal(Task, bool, str)   # 任务完成信号
    logGenerated = Signal(str, str)   # 日志生成信号
    
    def __init__(self):
        super().__init__(TaskType.TRANSCRIBE)
        self._check_availability()
    
    def _check_availability(self):
        """检查服务依赖是否可用"""
        # 检查 ffmpeg 是否可用
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         capture_output=True, 
                         check=True,
                         creationflags=0x08000000 if sys.platform == 'win32' else 0)
            self._available = True
            self._addLog("INFO", "听写服务已就绪")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self._available = False
            self._addLog("WARNING", "ffmpeg 未安装，听写服务不可用")
    
    def isAvailable(self) -> bool:
        """检查服务是否可用"""
        return self._available
    
    def createTask(self, input_path: str, **kwargs) -> Optional[Task]:
        """
        创建听写任务
        
        Args:
            input_path: 输入文件路径（视频/音频文件）
            **kwargs: 额外参数
                - whisper_model: Whisper 模型文件名
                - language: 源语言（ja, en, zh 等）
                - output_format: 输出格式
                    * "原文SRT" - SRT 字幕文件
                    * "双语SRT" - 双语 SRT（需配合翻译）
                    * "原文LRC" - LRC 歌词文件
                    * "原文TXT" - 纯文本文件
                    * "双语TXT" - 双语文本（需配合翻译）
                    * "原文XLSX" - Excel 表格
                    * "双语XLSX" - 双语 Excel（需配合翻译）
                - whisper_params: Whisper 参数
                - faster_whisper_params: Faster-Whisper 参数
                - translated_srt: 翻译后的 SRT 文件路径（用于双语格式）
                - include_timestamp: 是否包含时间戳（默认 True）
        
        Returns:
            创建的任务对象，如果创建失败返回 None
        """
        if not self.isAvailable():
            self._addLog("ERROR", "听写服务不可用")
            return None
        
        input_file = Path(input_path)
        if not input_file.exists():
            self._addLog("ERROR", f"输入文件不存在: {input_path}")
            return None
        
        # 检查是否是 SRT 文件（跳过听写，仅转换格式）
        is_srt = input_file.suffix.lower() == '.srt'
        
        task = Task(
            type=TaskType.TRANSCRIBE.value,
            status=TaskStatus.PENDING,
            inputPath=str(input_file.absolute()),
            fileName=input_file.name,
            name=f"听写: {input_file.name}",
            extraParams=kwargs
        )
        
        # 保存到数据库
        self.db.save_task(task)
        self._emit_task_created(task)
        
        # 自动开始任务
        self.start(task)
        
        return task
    
    def start(self, task: Task) -> bool:
        """开始听写任务"""
        if not self.isAvailable():
            self._addLog("ERROR", "听写服务不可用")
            return False
        
        if task.id in self.futures:
            self._addLog("WARNING", f"任务已在运行: {task.fileName}")
            return False
        
        task.status = TaskStatus.RUNNING
        task.startTime = datetime.now()
        self.db.save_task(task)
        self._emit_task_updated(task)
        
        # 定义听写任务函数
        def transcribe_task():
            """在线程池中执行的听写函数"""
            input_file = Path(task.inputPath)
            
            # 获取参数
            whisper_model = task.extraParams.get('whisper_model', WhisperEngine.NONE)
            language = task.extraParams.get('language', 'ja')
            output_format = task.extraParams.get('output_format', OutputFormat.SRT_ORIGINAL)
            
            # 如果是 SRT 文件，直接转换格式
            if input_file.suffix.lower() == '.srt':
                self._addLog("INFO", "检测到 SRT 文件，进行格式转换...")
                return self._convert_srt_format(task, input_file)
            
            # 检查是否跳过听写
            if whisper_model == WhisperEngine.NONE:
                self._addLog("WARNING", "未选择 Whisper 模型，跳过听写")
                return None
            
            # 1. 提取音频
            self._addLog("INFO", "正在提取音频...")
            wav_file = self._extract_audio(input_file)
            
            # 2. 执行 Whisper 听写
            self._addLog("INFO", f"正在进行语音识别...（模型: {whisper_model}）")
            srt_file = self._run_whisper(
                wav_file=wav_file,
                whisper_model=whisper_model,
                language=language,
                task=task
            )
            
            # 3. 生成输出文件
            self._addLog("INFO", "正在生成输出文件...")
            output_path = self._generate_output(
                srt_file=srt_file,
                output_format=output_format,
                task=task
            )
            
            # 4. 清理临时文件
            if wav_file.exists():
                wav_file.unlink()
            
            return {
                'output_path': str(output_path),
                'srt_path': str(srt_file)
            }
        
        # 使用 TaskExecutor 异步执行
        future = self.asyncRun(transcribe_task)
        
        # 绑定回调
        future.result.connect(lambda result: self._onTranscribeSuccess(task, result))
        future.failed.connect(lambda error: self._onTranscribeFailed(task, error))
        
        # 保存 Future 引用
        self.futures[task.id] = future
        
        self._addLog("INFO", f"开始听写任务: {task.fileName}")
        return True
    
    def _extract_audio(self, input_file: Path) -> Path:
        """
        提取音频并转换为 16k 采样率的 WAV 文件
        
        Args:
            input_file: 输入文件路径
            
        Returns:
            提取的 WAV 文件路径
        """
        wav_file = input_file.with_suffix('.16k.wav')
        
        cmd = [
            'ffmpeg', '-y',
            '-i', str(input_file),
            '-acodec', 'pcm_s16le',
            '-ac', '1',
            '-ar', '16000',
            str(wav_file)
        ]
        
        creationflags = 0x08000000 if sys.platform == 'win32' else 0
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=creationflags
        )
        
        stdout, stderr = process.communicate()
        
        if process.returncode != 0 or not wav_file.exists():
            raise RuntimeError(f"音频提取失败: {stderr.decode('utf-8', errors='ignore')}")
        
        return wav_file
    
    def _run_whisper(self, wav_file: Path, whisper_model: str, 
                     language: str, task: Task) -> Path:
        """
        运行 Whisper 听写
        
        Args:
            wav_file: WAV 音频文件路径
            whisper_model: Whisper 模型名称
            language: 源语言
            task: 任务对象
            
        Returns:
            生成的 SRT 文件路径
        """
        output_base = wav_file.with_suffix('')
        srt_file = output_base.with_suffix('.srt')
        
        if whisper_model.startswith('ggml'):
            # 使用 whisper.cpp
            cmd = self._prepare_whisper_cpp_command(
                whisper_model, wav_file, language, task
            )
        elif whisper_model.startswith('faster-whisper'):
            # 使用 faster-whisper
            cmd = self._prepare_faster_whisper_command(
                whisper_model, wav_file, language, task
            )
        else:
            raise ValueError(f"不支持的 Whisper 模型类型: {whisper_model}")
        
        # 执行命令
        creationflags = 0x08000000 if sys.platform == 'win32' else 0
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=creationflags
        )
        
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8', errors='ignore')
            raise RuntimeError(f"Whisper 听写失败: {error_msg}")
        
        if not srt_file.exists():
            raise RuntimeError(f"未生成 SRT 文件: {srt_file}")
        
        return srt_file
    
    def _prepare_whisper_cpp_command(self, model: str, wav_file: Path, 
                                     language: str, task: Task) -> list:
        """准备 whisper.cpp 命令"""
        params = task.extraParams.get('whisper_params', '')
        
        # 基础命令
        cmd = [
            'whisper/main.exe' if sys.platform == 'win32' else 'whisper/main',
            '-m', f'whisper/{model}',
            '-l', language,
            '-f', str(wav_file.with_suffix('')),
            '-osrt'
        ]
        
        # 添加额外参数
        if params:
            cmd.extend(params.split())
        
        return cmd
    
    def _prepare_faster_whisper_command(self, model: str, wav_file: Path,
                                       language: str, task: Task) -> list:
        """准备 faster-whisper 命令"""
        params = task.extraParams.get('faster_whisper_params', '')
        model_name = model.replace('faster-whisper-', '')
        
        # 基础命令
        cmd = [
            'python',
            'whisper-faster/transcribe.py',
            '--model', model_name,
            '--language', language,
            '--input', str(wav_file.with_suffix('')),
            '--output_dir', str(wav_file.parent)
        ]
        
        # 添加额外参数
        if params:
            cmd.extend(params.split())
        
        return cmd
    
    def _generate_output(self, srt_file: Path, output_format: str, 
                        task: Task) -> Path:
        """
        生成指定格式的输出文件
        
        Args:
            srt_file: SRT 文件路径
            output_format: 输出格式
            task: 任务对象
            
        Returns:
            输出文件路径
        """
        input_file = Path(task.inputPath)
        
        # 获取时间戳设置（默认为 True）
        include_timestamp = task.extraParams.get('include_timestamp', True)
        
        # 原文格式处理
        if output_format == OutputFormat.SRT_ORIGINAL:
            # 原文 SRT（始终包含时间戳，这是 SRT 格式的必需部分）
            output_file = input_file.with_suffix('.srt')
            if srt_file != output_file:
                import shutil
                shutil.copy(srt_file, output_file)
            return output_file
        
        elif output_format == OutputFormat.LRC_ORIGINAL:
            # 原文 LRC（始终包含时间戳，这是 LRC 格式的必需部分）
            output_file = input_file.with_suffix('.lrc')
            self._srt_to_lrc(srt_file, output_file)
            return output_file
        
        elif output_format == OutputFormat.TXT_ORIGINAL:
            # 原文 TXT
            output_file = input_file.with_suffix('.txt')
            self._srt_to_txt(srt_file, output_file, include_timestamp=include_timestamp)
            return output_file
        
        elif output_format == OutputFormat.XLSX_ORIGINAL:
            # 原文 XLSX
            output_file = input_file.with_suffix('.xlsx')
            self._srt_to_xlsx(srt_file, output_file, include_timestamp=include_timestamp)
            return output_file
        
        # 双语格式处理（需要翻译文件）
        elif output_format == OutputFormat.SRT_BILINGUAL:
            # 双语 SRT（始终包含时间戳）
            translated_srt = task.extraParams.get('translated_srt')
            if not translated_srt or not Path(translated_srt).exists():
                self._addLog("WARNING", "未找到翻译文件，仅输出原文")
                return self._generate_output(srt_file, OutputFormat.SRT_ORIGINAL, task)
            
            output_file = input_file.with_name(f"{input_file.stem}_bilingual.srt")
            self._merge_bilingual_srt(srt_file, Path(translated_srt), output_file)
            return output_file
        
        elif output_format == OutputFormat.TXT_BILINGUAL:
            # 双语 TXT
            translated_srt = task.extraParams.get('translated_srt')
            if not translated_srt or not Path(translated_srt).exists():
                self._addLog("WARNING", "未找到翻译文件，仅输出原文")
                return self._generate_output(srt_file, OutputFormat.TXT_ORIGINAL, task)
            
            output_file = input_file.with_name(f"{input_file.stem}_bilingual.txt")
            self._merge_bilingual_txt(srt_file, Path(translated_srt), output_file, 
                                      include_timestamp=include_timestamp)
            return output_file
        
        elif output_format == OutputFormat.XLSX_BILINGUAL:
            # 双语 XLSX
            translated_srt = task.extraParams.get('translated_srt')
            if not translated_srt or not Path(translated_srt).exists():
                self._addLog("WARNING", "未找到翻译文件，仅输出原文")
                return self._generate_output(srt_file, OutputFormat.XLSX_ORIGINAL, task)
            
            output_file = input_file.with_name(f"{input_file.stem}_bilingual.xlsx")
            self._merge_bilingual_xlsx(srt_file, Path(translated_srt), output_file,
                                       include_timestamp=include_timestamp)
            return output_file
        
        else:
            # 默认返回 SRT
            self._addLog("WARNING", f"未知的输出格式: {output_format}，使用默认 SRT")
            return srt_file
    
    def _convert_srt_format(self, task: Task, srt_file: Path) -> Dict[str, str]:
        """
        转换 SRT 文件格式（用于直接输入 SRT 文件的情况）
        
        Args:
            task: 任务对象
            srt_file: SRT 文件路径
            
        Returns:
            结果字典
        """
        output_format = task.extraParams.get('output_format', OutputFormat.SRT_ORIGINAL)
        
        output_path = self._generate_output(srt_file, output_format, task)
        
        return {
            'output_path': str(output_path),
            'srt_path': str(srt_file)
        }
    
    def _parse_srt(self, srt_file: Path) -> list:
        """解析 SRT 文件"""
        segments = []
        
        with open(srt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 简单的 SRT 解析
        blocks = content.strip().split('\n\n')
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                # 时间戳行
                time_line = lines[1]
                match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})', time_line)
                if match:
                    start, end = match.groups()
                    text = '\n'.join(lines[2:])
                    segments.append({
                        'start': start,
                        'end': end,
                        'text': text
                    })
        
        return segments
    
    def _srt_to_lrc(self, srt_file: Path, lrc_file: Path):
        """将 SRT 文件转换为 LRC 格式"""
        segments = self._parse_srt(srt_file)
        
        with open(lrc_file, 'w', encoding='utf-8') as f:
            for seg in segments:
                # 转换时间格式：00:01:23,456 -> [01:23.45]
                start_time = seg['start']
                # 解析时间
                time_parts = start_time.replace(',', ':').split(':')
                hours, minutes, seconds, milliseconds = map(int, time_parts)
                
                # 计算总分钟和秒
                total_minutes = hours * 60 + minutes
                total_seconds = seconds
                centiseconds = milliseconds // 10
                
                # 写入 LRC 格式
                f.write(f"[{total_minutes:02d}:{total_seconds:02d}.{centiseconds:02d}]{seg['text']}\n")

    def _srt_to_txt(self, srt_file: Path, txt_file: Path, include_timestamp: bool = True):
        """将 SRT 文件转换为 TXT 格式"""
        segments = self._parse_srt(srt_file)
        
        with open(txt_file, 'w', encoding='utf-8') as f:
            for seg in segments:
                if include_timestamp:
                    f.write(f"[{seg['start']} --> {seg['end']}]\n")
                f.write(f"{seg['text']}\n\n")

    def _srt_to_xlsx(self, srt_file: Path, xlsx_file: Path, include_timestamp: bool = True):
        """将 SRT 文件转换为 XLSX 格式"""
        
        segments = self._parse_srt(srt_file)
        
        # 创建工作簿
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "字幕"
        
        # 根据时间戳设置设置表头
        if include_timestamp:
            headers = ['序号', '开始时间', '结束时间', '字幕内容']
        else:
            headers = ['序号', '字幕内容']
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
        
        # 写入数据
        for idx, seg in enumerate(segments, 1):
            if include_timestamp:
                ws.cell(row=idx+1, column=1, value=idx)
                ws.cell(row=idx+1, column=2, value=seg['start'])
                ws.cell(row=idx+1, column=3, value=seg['end'])
                ws.cell(row=idx+1, column=4, value=seg['text'])
            else:
                ws.cell(row=idx+1, column=1, value=idx)
                ws.cell(row=idx+1, column=2, value=seg['text'])
        
        # 调整列宽
        if include_timestamp:
            ws.column_dimensions['A'].width = 8
            ws.column_dimensions['B'].width = 15
            ws.column_dimensions['C'].width = 15
            ws.column_dimensions['D'].width = 60
        else:
            ws.column_dimensions['A'].width = 8
            ws.column_dimensions['B'].width = 60
        
        # 保存
        wb.save(xlsx_file)

    def _merge_bilingual_srt(self, original_srt: Path, translated_srt: Path, output_srt: Path):
        """合并原文和翻译生成双语 SRT"""
        original_segments = self._parse_srt(original_srt)
        translated_segments = self._parse_srt(translated_srt)
        
        with open(output_srt, 'w', encoding='utf-8') as f:
            for idx, (orig, trans) in enumerate(zip(original_segments, translated_segments), 1):
                f.write(f"{idx}\n")
                f.write(f"{orig['start']} --> {orig['end']}\n")
                f.write(f"{orig['text']}\n")
                f.write(f"{trans['text']}\n")
                f.write("\n")

    def _merge_bilingual_txt(self, original_srt: Path, translated_srt: Path, 
                             output_txt: Path, include_timestamp: bool = True):
        """合并原文和翻译生成双语 TXT"""
        original_segments = self._parse_srt(original_srt)
        translated_segments = self._parse_srt(translated_srt)
        
        with open(output_txt, 'w', encoding='utf-8') as f:
            for orig, trans in zip(original_segments, translated_segments):
                if include_timestamp:
                    f.write(f"[{orig['start']} --> {orig['end']}]\n")
                f.write(f"{orig['text']}\n")
                f.write(f"{trans['text']}\n\n")

    def _merge_bilingual_xlsx(self, original_srt: Path, translated_srt: Path, 
                              output_xlsx: Path, include_timestamp: bool = True):
        """合并原文和翻译生成双语 XLSX"""
        
        original_segments = self._parse_srt(original_srt)
        translated_segments = self._parse_srt(translated_srt)
        
        # 创建工作簿
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "双语字幕"
        
        # 根据时间戳设置设置表头
        if include_timestamp:
            headers = ['序号', '开始时间', '结束时间', '原文', '译文']
        else:
            headers = ['序号', '原文', '译文']
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
        
        # 写入数据
        for idx, (orig, trans) in enumerate(zip(original_segments, translated_segments), 1):
            if include_timestamp:
                ws.cell(row=idx+1, column=1, value=idx)
                ws.cell(row=idx+1, column=2, value=orig['start'])
                ws.cell(row=idx+1, column=3, value=orig['end'])
                ws.cell(row=idx+1, column=4, value=orig['text'])
                ws.cell(row=idx+1, column=5, value=trans['text'])
            else:
                ws.cell(row=idx+1, column=1, value=idx)
                ws.cell(row=idx+1, column=2, value=orig['text'])
                ws.cell(row=idx+1, column=3, value=trans['text'])
        
        # 调整列宽
        if include_timestamp:
            ws.column_dimensions['A'].width = 8
            ws.column_dimensions['B'].width = 15
            ws.column_dimensions['C'].width = 15
            ws.column_dimensions['D'].width = 40
            ws.column_dimensions['E'].width = 40
        else:
            ws.column_dimensions['A'].width = 8
            ws.column_dimensions['B'].width = 40
            ws.column_dimensions['C'].width = 40
        
        # 保存
        wb.save(output_xlsx)
    
    def _onTranscribeSuccess(self, task: Task, result: Dict[str, str]):
        """听写成功的回调 - 在主线程中执行"""
        if result:
            task.outputPath = result.get('output_path')
            task.progress = 100.0
            
            # 保存额外信息
            task.extraParams['srt_path'] = result.get('srt_path')
            
            self._onWorkerFinished(task, True, "听写完成")
        else:
            self._onWorkerFinished(task, True, "任务完成（已跳过听写）")
    
    def _onTranscribeFailed(self, task: Task, error: FutureFailed):
        """听写失败的回调 - 在主线程中执行"""
        error_msg = str(error.exception) if hasattr(error, 'exception') else str(error)
        self._onWorkerFinished(task, False, error_msg)


# 全局服务实例
transcriptionService = TranscriptionService()