#!/usr/bin/env python3
# coding:utf-8
"""
Faster-Whisper 转录脚本
使用 faster-whisper 库进行语音识别，输出 SRT 字幕文件
"""

import argparse
import sys
from pathlib import Path
from datetime import timedelta

def format_timestamp(seconds: float) -> str:
    """
    将秒数转换为 SRT 时间戳格式 (HH:MM:SS,mmm)
    
    Args:
        seconds: 秒数
        
    Returns:
        格式化的时间戳字符串
    """
    td = timedelta(seconds=seconds)
    hours = int(td.total_seconds() // 3600)
    minutes = int((td.total_seconds() % 3600) // 60)
    secs = int(td.total_seconds() % 60)
    millis = int((td.total_seconds() % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def transcribe_audio(model_path: str, audio_path: str, language: str, 
                     output_dir: str, device: str = "auto", 
                     compute_type: str = "auto") -> str:
    """
    使用 faster-whisper 转录音频文件
    
    Args:
        model_path: 模型路径或模型名称
        audio_path: 音频文件路径
        language: 语言代码 (ja, en, zh, etc.)
        output_dir: 输出目录
        device: 设备 (cpu, cuda, auto)
        compute_type: 计算类型 (int8, float16, auto)
        
    Returns:
        生成的 SRT 文件路径
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("错误: 未安装 faster-whisper 库")
        print("请运行: pip install faster-whisper")
        sys.exit(1)
    
    # 加载模型
    print(f"正在加载模型: {model_path}")
    
    # 如果是相对路径，转换为绝对路径
    if not Path(model_path).is_absolute():
        script_dir = Path(__file__).parent
        model_full_path = script_dir / model_path
        if model_full_path.exists():
            model_path = str(model_full_path)
    
    try:
        # 自动检测设备和计算类型
        if device == "auto":
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"
        
        if compute_type == "auto":
            compute_type = "float16" if device == "cuda" else "int8"
        
        print(f"使用设备: {device}, 计算类型: {compute_type}")
        
        model = WhisperModel(
            model_path, 
            device=device, 
            compute_type=compute_type
        )
    except Exception as e:
        print(f"加载模型失败: {e}")
        sys.exit(1)
    
    # 转录音频
    print(f"正在转录音频: {audio_path}")
    audio_file = Path(audio_path)
    
    if not audio_file.exists():
        # 尝试添加 .wav 后缀
        audio_file = Path(f"{audio_path}.wav")
        if not audio_file.exists():
            print(f"错误: 音频文件不存在: {audio_path}")
            sys.exit(1)
    
    segments, info = model.transcribe(
        str(audio_file),
        language=language if language != "auto" else None,
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500)
    )
    
    print(f"检测到的语言: {info.language} (概率: {info.language_probability:.2%})")
    
    # 生成 SRT 文件
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    srt_file = output_path / f"{audio_file.stem}.srt"
    
    print(f"正在生成 SRT 文件: {srt_file}")
    
    with open(srt_file, 'w', encoding='utf-8') as f:
        segment_count = 0
        for segment in segments:
            segment_count += 1
            start_time = format_timestamp(segment.start)
            end_time = format_timestamp(segment.end)
            text = segment.text.strip()
            
            f.write(f"{segment_count}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{text}\n\n")
        
        print(f"转录完成，共 {segment_count} 个片段")
    
    return str(srt_file)


def main():
    parser = argparse.ArgumentParser(description="Faster-Whisper 转录脚本")
    parser.add_argument('--model', required=True, help='模型路径或模型名称 (如: medium, large-v2)')
    parser.add_argument('--input', required=True, help='输入音频文件路径')
    parser.add_argument('--language', default='auto', help='语言代码 (ja, en, zh, 等)')
    parser.add_argument('--output_dir', required=True, help='输出目录')
    parser.add_argument('--device', default='auto', choices=['auto', 'cpu', 'cuda'], 
                       help='计算设备 (auto, cpu, cuda)')
    parser.add_argument('--compute_type', default='auto', 
                       choices=['auto', 'int8', 'int8_float16', 'int16', 'float16', 'float32'],
                       help='计算类型')
    
    args = parser.parse_args()
    
    try:
        srt_file = transcribe_audio(
            model_path=args.model,
            audio_path=args.input,
            language=args.language,
            output_dir=args.output_dir,
            device=args.device,
            compute_type=args.compute_type
        )
        print(f"✅ 成功! SRT 文件: {srt_file}")
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

