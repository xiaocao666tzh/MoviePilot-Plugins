# Torrent Bridge

Torrent Bridge 是一个 MoviePilot 独立插件，为外部程序提供获取种子文件的 HTTP 接口。插件利用 MoviePilot 已配置的站点信息解析下载地址，返回种子文件或磁力链接，由调用方决定如何保存和提交下载器。

当前版本为 **1.0.0**，按 **MoviePilot v2.15.6** 的接口实现。其他版本需要核对兼容性。

## 功能与工作方式

- 获取种子文件，文件大小上限为 16 MiB。
- 支持返回 MoviePilot 解析所得的磁力链接。
- 复用 MoviePilot 的站点 Cookie、UA 和代理配置，调用方无需传入这些信息。
- 沿用 MoviePilot 的 `API_TOKEN` 鉴权，无需单独设置插件密钥。
- 提供启用开关，安装后默认关闭。

```text
外部程序选择资源
       ↓ 资源标题、站点编号、原始下载地址
Torrent Bridge
       ↓ 调用 MoviePilot 下载链获取种子内容
返回种子文件或磁力链接
       ↓
外部程序保存文件并提交下载器
```

插件只负责获取种子内容，不创建 MoviePilot 下载任务，也不负责资源搜索、下载分类、保存路径、媒体整理或失败重试。反馈平台使用 MoviePilot 自带的搜索接口查找资源，再通过本插件取文件。

这是继承 `_PluginBase` 的独立插件，不能直接粘贴到基于 `UserTaskBase` 的自定义任务编辑框运行。
