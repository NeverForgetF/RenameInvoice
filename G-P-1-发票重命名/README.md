# Windows 环境配置与项目启动

## 一、安装 Python 3.10

1. **下载 Python 3.10**
2. 
   请访问 [Python 官方网站](https://www.python.org/downloads/release/python-31010/) 下载适合你的操作系统的 Python 3.10 版本。
   或者[点击这里直接下载python3.10.10版本](https://www.python.org/ftp/python/3.10.10/python-3.10.10-amd64.exe)
   
3. **安装 Python**
   * 双击 python-3.10.10-amd64.exe 可执行文件
   * 在安装过程中，请确保勾选 **“Add Python to PATH”**，这将自动将 Python 添加到环境变量中。
   * 完成安装后，可以在终端（或命令提示符）中输入 `python --version` 来确认安装成功。

## 二、安装项目依赖

1. 在项目目录下，确保有一个 `requirements.txt` 文件，其中列出了所有依赖的库。
2. 打开终端，进入项目根目录，执行以下命令来安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

   该命令会自动安装 `requirements.txt` 文件中列出的所有 Python 包。

## 三、配置环境变量（如果没有 `config.json`）

1. **打开系统环境变量设置**：

   * 按 `Win + S`，搜索并选择 **“编辑系统环境变量”**。
   * 点击 **环境变量**。

2. **在“用户变量”中添加以下变量**：

   * 点击 **新建**，然后逐个添加以下变量：

   | 变量名             | 示例值                                                    |
   | --------------- | ------------------------------------------------------ |
   | MODEL_NAME      | qwen-vl-chat                                           |
   | OPENAI_API_BASE | [https://api.openai.com/v1](https://api.openai.com/v1) |
   | OPENAI_API_KEY  | sk-xxx                                                 |

3. **确认并重启终端或 PyCharm**。

## 四、使用 `config.json` 配置（如果存在）

如果你的项目目录下存在 `config.json` 文件，程序会自动读取该文件中的配置，无需再配置系统环境变量。

**`config.json` 示例**：

```json
{
  "MODEL_NAME": "qwen-vl-chat",
  "OPENAI_API_BASE": "https://api.openai.com/v1",
  "OPENAI_API_KEY": "sk-xxx"
}
```

## 五、启动项目

在完成以上配置后，进入项目根目录，运行以下命令来启动项目：

```bash
python main.py
```

---

## 六、总结

1. **安装 Python 3.10** 并确认安装成功。
2. **执行 `pip install -r requirements.txt`** 安装依赖。
3. **如果没有 `config.json`**，手动配置系统环境变量。
4. **如果有 `config.json`**，项目会自动读取该配置。
5. 最后，在项目目录下执行 `python main.py` 启动项目。

---
