# 123Mark

Windows 图片批量水印工具。所有处理均在本机完成，支持文本水印、图片水印、彩虹渐变、九宫格位置以及精确的平铺行列设置。

当前版本：`1.0.1`

## 直接使用

运行 `release/123Mark-v1.0.1.exe`。该文件是独立的 Windows 单文件程序，目标电脑无需安装 Python 或其他依赖。

## 主要功能

- 批量或按文件夹导入 JPG、PNG、BMP、WebP、TIFF、ICO
- 文本水印与图片水印
- 彩虹七色渐变文字
- 九宫格位置、边距、旋转、不透明度
- 平铺水印以及独立的行数、列数
- 常用水印收藏（最多 10 项），包含文字、颜色/彩虹、字号、不透明度、旋转、位置、边距和平铺行列；同一文字可收藏不同样式
- 正常退出或收起到托盘时自动保存设置，下次启动恢复上次的水印与输出设置
- 兼容旧版纯文字收藏，选用时保留当前样式；重新收藏即可保存完整样式
- 实时预览与放大查看
- 保持原格式或输出 JPEG、PNG、BMP、WebP
- 后台批处理、进度与失败汇总
- 窗口置顶和系统托盘

完整范围与验收口径见 [需求说明.md](需求说明.md)，三轮检查结果见 [测试报告.md](测试报告.md)。

## 源码运行

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

## 测试

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## 构建 Windows 单文件程序

双击 `build.bat`，或在 PowerShell 中运行：

```powershell
.\build.bat
```

构建产物：`release/123Mark-v1.0.1.exe`

用户配置与收藏保存在 `%APPDATA%\123Mark`。
