# Windows 环境变量配置

## 一、config.json（放代码同级目录）

```json
{
  "JSON_ENVIRON": true,
  "MODEL_NAME": "qwen-vl-chat",
  "OPENAI_API_BASE": "https://api.openai.com/v1",
  "OPENAI_API_KEY": "sk-xxx"
}
```

| JSON_ENVIRON | 怎么用 |
|--------------|--------|
| **true** | 直接运行，**不用配系统变量** |
| **false** | 按下面步骤配系统变量，再运行 |

---

## 二、配系统变量（仅 JSON_ENVIRON = false 时）

1. Win + S → 搜 **“编辑系统环境变量”** → **环境变量**  
2. **用户变量** → **新建** → 逐个添加：

| 变量名 | 示例值 |
|--------|--------|
| MODEL_NAME | qwen-vl-chat |
| OPENAI_API_BASE | https://api.openai.com/v1 |
| OPENAI_API_KEY | sk-xxx |

3. 确定 → **重启终端/PyCharm** → 运行程序

---

## 三、一句话总结
> **JSON_ENVIRON true 改文件就行；false 就按上面配系统变量。**