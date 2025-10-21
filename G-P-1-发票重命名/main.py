from datetime import datetime
from tkinter import messagebox

from PIL._tkinter_finder import tk
from invoice_rename_config import FieldSelector, fields
from rename_function import run_main_ui_local


def start_config():
    expire_str = "2030-08-14"
    now = datetime.now()
    expire_date = datetime.strptime(expire_str, "%Y-%m-%d")

    if now.date() > expire_date.date():
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        messagebox.showinfo("激活状态", f"激活已过期，截止日期为 {expire_str}，程序退出。")
        root.destroy()
        return

    def on_config_confirm(cfg):
        run_main_ui_local(cfg)

    app = FieldSelector(fields, on_confirm=on_config_confirm)
    app.mainloop()


if __name__ == "__main__":
    start_config()


# if __name__ == '__main__':
#     cfg = {
#         "folder": 'E:\其他\大学生创新创业\创新创业\发票',
#         "fields": ['发票号码', '开票日期', '购方名称', '销方名称'],
#         "split": '_'
#     }
#     pdf_dir = cfg.get("folder", "")
#     fields = cfg.get("fields", [])
#     split = cfg.get("split", "_")
#     rename_rule = split.join(fields)
#     run_main_ui_local(cfg)