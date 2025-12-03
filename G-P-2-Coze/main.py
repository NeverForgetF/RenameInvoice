from invoice_rename_config import FieldSelector, fields
from coze import run_main_ui

def start_config():
    def on_config_confirm(cfg):
        # 只执行一次流程，去掉 on_done 回调
        run_main_ui(cfg)
    app = FieldSelector(fields, on_confirm=on_config_confirm)
    app.mainloop()

if __name__ == "__main__":
    start_config()
