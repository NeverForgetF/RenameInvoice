# def valid_date():
#     expire_str = "2030-08-14"
#     now = datetime.now()
#     expire_date = datetime.strptime(expire_str, "%Y-%m-%d")
#
#     if now.date() > expire_date.date():
#         root = tk.Tk()
#         root.withdraw()  # 隐藏主窗口
#         messagebox.showinfo("激活状态", f"激活已过期，截止日期为 {expire_str}，程序退出。")
#         root.destroy()
#         return
import json
import os
import sys

from invoice_rename_config import FieldSelector, fields
from rename_function import run_main_ui_local

def load_config_to_environ(config_file: str = "config.json") -> None:
    """读 config.json；找不到就 用.env """
    if not os.path.isfile(config_file):
        print("使用.env文件加载环境变量")
        return
    print("使用config.json加载环境变量")
    """
    将 config.json 中的 MODEL_NAME / OPENAI_API_BASE / OPENAI_API_KEY
    加载到当前进程的 os.environ 中（仅本次运行有效，不会写系统注册表）。
    """
    with open(config_file, encoding='utf-8') as f:
        cfg = json.load(f)

    if (cfg.get("JSON_ENVIRON") is False
            or cfg.get("JSON_ENVIRON") is None)\
            or cfg.get("JSON_ENVIRON") == 'false':
        return

    # 3. 写入 os.environ（只写我们关心的 3 个 key）
    for key in ("MODEL_NAME", "OPENAI_API_BASE", "OPENAI_API_KEY"):
        value = cfg.get(key)
        if value is not None:                       # 允许空字符串，但不允许缺失
            os.environ[key] = str(value)

def start_config():
    # 存放json配置的路径
    # load_config_to_environ()    # 用.env 可以注释这行
    def on_config_confirm(cfg):
        run_main_ui_local(cfg)

    app = FieldSelector(fields, on_confirm=on_config_confirm)
    app.mainloop()


if __name__ == "__main__":
    start_config()
