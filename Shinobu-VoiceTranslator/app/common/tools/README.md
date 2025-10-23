# 工具文件夹 (Tools Directory)

此文件夹用于存放听写服务所需的工具。

## 📦 需要的文件

### ffmpeg.exe
用于音频提取和格式转换。

**下载地址**:
- 官方网站: https://ffmpeg.org/download.html
- Windows 编译版本: https://github.com/BtbN/FFmpeg-Builds/releases

**安装步骤**:
1. 下载 `ffmpeg-master-latest-win64-gpl.zip`
2. 解压后找到 `bin\ffmpeg.exe`
3. 将 `ffmpeg.exe` 复制到此目录（`app\common\tools\ffmpeg.exe`）

**验证**:
运行程序后，如果听写服务显示"听写服务已就绪"，说明 ffmpeg 配置成功。

## 📁 文件结构

```
app/common/tools/
├── README.md          # 本说明文件
└── ffmpeg.exe         # ffmpeg 可执行文件 (需要自行下载)
```

## ⚠️ 注意事项

- 文件大小: ffmpeg.exe 约 100-150 MB
- 仅支持 Windows 64位版本
- 确保下载的是完整版 (GPL 版本)，包含所有编解码器

## 🔍 故障排除

如果听写服务显示"ffmpeg 未找到"：
1. 检查文件是否在正确位置：`app\common\tools\ffmpeg.exe`
2. 检查文件名是否正确（区分大小写）
3. 确保文件有执行权限
4. 尝试从命令行运行 `ffmpeg.exe -version` 测试

## 📝 替代方案

如果不想手动下载，也可以：
1. 将 ffmpeg 添加到系统 PATH 环境变量
2. 程序会自动尝试使用系统 PATH 中的 ffmpeg

---

**版本要求**: ffmpeg 4.0 或更高版本  
**推荐版本**: ffmpeg 6.0+

