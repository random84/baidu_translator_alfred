# 百度翻译 Alfred Workflow

这是一个基于百度翻译API的Alfred workflow，支持中英互译和单词查询。

## 功能特性

- ✅ 中英文互译（自动检测语言）
- ✅ 单词音标显示（英式和美式音标）
- ✅ 详细释义和词形变化
- ✅ 支持复制翻译结果
- ✅ 实时翻译结果
- ✅ 自动Acs-Token管理

## 安装步骤

1. **安装依赖**
```bash
pip3 install requests playwright
```

2. **导入Workflow**
   - 双击 `info.plist` 文件导入Alfred
   - 或将整个文件夹拖拽到Alfred的Workflows面板

3. **配置Python路径（可选）**
   - 如果Python路径不是默认的，请在Alfred workflow配置中修改 `PYTHON_PATH` 变量

## 使用方法

1. 激活Alfred
2. 输入 `tr` 后跟要翻译的文本
3. 按回车键查看翻译结果
4. 使用Tab键选择复制选项

## 触发方式

- **关键词触发**: 输入 `tr` + 空格 + 要翻译的内容
- **快捷键触发**: 默认快捷键 `⌘ + D`（可在Alfred中自定义）

## 示例

- `tr hello` - 翻译英文单词（显示音标和详细释义）
- `tr 你好` - 翻译中文词语
- `tr How are you` - 翻译英文句子
- `tr 今天天气怎么样` - 翻译中文句子

## 文件说明

- `info.plist` - Alfred workflow配置文件（包含触发关键词和Python路径）
- `baidu_translator_alfred.py` - 主翻译脚本（处理翻译逻辑和Alfred输出格式）
- `getAcsToken.py` - Acs-Token自动获取工具（使用Playwright模拟浏览器）
- `acs_token_cache.json` - Token缓存文件（自动生成）
- `icon.png` - Workflow图标

## 技术实现

- 使用百度翻译AI API进行翻译
- 自动检测输入文本语言（中文/英文）
- 智能区分单词和句子翻译
- 自动管理Acs-Token（过期自动更新）

## 注意事项

- 首次使用时会自动获取Acs-Token，可能需要几秒钟
- 确保网络连接正常，能够访问百度翻译网站
- 如遇翻译失败，workflow会自动尝试重新获取Token

## 故障排除

如果遇到问题，可以尝试以下步骤：

1. 检查网络连接
2. 重新运行workflow（会自动更新Token）
3. 确认Python环境正确配置
4. 查看Alfred的debug日志获取详细信息