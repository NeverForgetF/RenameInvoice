import tkinter as tk
from tkinter import messagebox, filedialog

fields = [
    {"key": "发票号码", "desc": "发票上的唯一号码（如：2511702321248076035）"},
    {"key": "开票日期", "desc": "发票开票日期（如：2025年02月27日）"},
    {"key": "购方名称", "desc": "购买方公司名称（如：武汉东湖学院）"},
    {"key": "购方税号", "desc": "购买方统一社会信用代码/纳税人识别号"},
    {"key": "销方名称", "desc": "销售方公司名称（如：腾讯云计算（北京）有限责任公司）"},
    {"key": "销方税号", "desc": "销售方统一社会信用代码/纳税人识别号"},
    # {"key": "项目名称", "desc": "项目名称（如：信息技术服务*云服务费）"},
    # {"key": "规格型号", "desc": "项目规格型号（如：空，未填写）"},
    # {"key": "单位", "desc": "项目计量单位（如：套）"},
    # {"key": "数量", "desc": "项目数量（如：1）"},
    # {"key": "单价", "desc": "项目单价（如：94.34）"},
    # {"key": "金额", "desc": "项目金额（如：94.34）"},
    # {"key": "税率", "desc": "税率（如：6%）"},
    # {"key": "税额", "desc": "税额（如：5.66）"},
    {"key": "合计", "desc": "发票合计金额（如：94.34，表格下方“合计”对应金额，不含税）"},
    {"key": "总税额", "desc": "发票合计税额（如：5.66，表格下方“合计”对应税额）"},
    {"key": "价税合计", "desc": "发票价税合计，仅数字，不要中文大写（如：100.00）"},
    {"key": "价税合计大写", "desc": "价税合计（大写），如：壹佰元整"},
    # {"key": "备注", "desc": "备注栏内容（如：空，未填写）"},
    {"key": "开票人", "desc": "开票人姓名（如：王丽丽）"}
]

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height()
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw, text=self.text, justify="left",
            background="#ffffe0", relief="solid", borderwidth=1,
            font=("微软雅黑", 10), wraplength=280
        )
        label.pack(ipadx=6, ipady=4)

    def hide_tip(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

class FieldSelector(tk.Tk):
    CELL_WIDTH = 140  # 每个字段项大致宽度，像素

    def __init__(self, fields, on_confirm=None):
        super().__init__()
        self.on_confirm = on_confirm  # 增加这行
        self.title("发票重命名参数配置")
        self.geometry("750x550")
        self.configure(bg="#f4f4f9")
        self.selected_order = []
        self.field_vars = {}
        self.field_items = []  # 存储 (chk, tip)
        self.split_var = tk.StringVar(value="_")
        self.rename_preview = tk.StringVar()

        # 提示区
        hint_frame = tk.Frame(self, bg="#f4f4f9", pady=10)
        hint_frame.pack(fill="x", padx=20)  # 原来20，可以减小一点

        tk.Label(
            hint_frame,
            text="【命名规范】重命名将以你选择字段的顺序，使用分隔符拼接而成。\n 示例：{销方名称}_{开票日期}_{合计}",
            fg="#0052cc",
            font=("微软雅黑", 13, "bold"),
            bg="#f4f4f9",
            justify="left",
            wraplength=540  # 比如用hint_frame宽度-按钮宽度
        ).pack(side="left", fill="x", expand=True, pady=2)

        # 过滤文件按钮
        filter_btn = tk.Button(
            hint_frame, text="过滤文件",
            font=("微软雅黑", 13, "bold"), bg="#388e3c", fg="#ffffff",
            command=self.filter_files
        )
        # 问号说明
        filter_tip_label = tk.Label(
            hint_frame, text="?", fg="#388e3c",
            cursor="hand2", font=("微软雅黑", 15, "bold"), bg="#f4f4f9"
        )
        filter_tip_label.pack(side="right", padx=(2, 8), pady=2)
        ToolTip(
            filter_tip_label,
            "一键过滤并删除当前文件夹下内容完全相同的重复文件，仅保留每组中的一个。\n"
            "仅比较文件内容（不比对文件名），不会遍历子文件夹。"
        )
        filter_btn.pack(side="right", padx=8, pady=2)

        tk.Button(
            hint_frame, text="确认",
            font=("微软雅黑", 13, "bold"), bg="#1976d2", fg="#ffffff",
            command=self.confirm
        ).pack(side="right", padx=8, pady=2)

        # 命名模板区
        template_frame = tk.LabelFrame(
            self, text="命名模板", bg="#f4f4f9", font=("微软雅黑", 10, "bold"), height=120
        )
        template_frame.pack(fill="x", padx=20, pady=5)
        template_frame.pack_propagate(False)
        # 横排，左边一行，右边Label独立
        row_frame = tk.Frame(template_frame, bg="#f4f4f9")
        row_frame.pack(side="top", fill="both", expand=True)
        # 左侧一行内容
        left_row = tk.Frame(row_frame, bg="#f4f4f9")
        left_row.pack(side="left", anchor="n", padx=(10, 0), pady=8)
        tk.Label(left_row, text="分隔符：", font=("微软雅黑", 10), bg="#f4f4f9").pack(side="left")
        sep_entry = tk.Entry(left_row, textvariable=self.split_var, width=5, font=("微软雅黑", 10))
        sep_entry.pack(side="left", padx=5)
        sep_entry.bind("<KeyRelease>", lambda e: self.update_preview())
        tk.Label(left_row, text="命名预览：", font=("微软雅黑", 10), bg="#f4f4f9").pack(side="left", padx=(20, 5))

        # 右侧Label，内容撑高自己但不挤左侧
        right = tk.Frame(row_frame, bg="#f4f4f9")
        right.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=8)
        self.preview_label = tk.Label(
            right, textvariable=self.rename_preview,
            font=("Consolas", 11, "bold"), fg="#1a73e8",
            bg="#f4f4f9",
            anchor="nw",  # 关键：Label内容左上对齐
            justify="left",
            wraplength=470,  # 可调整
        )
        self.preview_label.pack(fill="both", expand=True)

        # 目标文件夹和清除按钮
        folder_frame = tk.LabelFrame(self, text="目标文件夹", bg="#f4f4f9", font=("微软雅黑", 10, "bold"))
        folder_frame.pack(fill="x", padx=20, pady=5)
        self.folder_var = tk.StringVar()
        tk.Entry(
            folder_frame, textvariable=self.folder_var,
            width=60, font=("微软雅黑", 10)
        ).pack(side="left", padx=8, pady=5)
        tk.Button(
            folder_frame, text="选择文件夹",
            font=("微软雅黑", 10), command=self.choose_folder
        ).pack(side="left", padx=(8,0), pady=5)
        tk.Button(
            folder_frame, text="清除选择",
            font=("微软雅黑", 10), command=self.clear_fields
        ).pack(side="left", padx=8, pady=5)

        # 字段选择区
        self.field_frame = tk.LabelFrame(self, text="选择重命名字段", bg="#f4f4f9", font=("微软雅黑", 10, "bold"))
        self.field_frame.pack(fill="x", padx=20, pady=5)
        # 创建所有字段控件但不布局
        for f in fields:
            var = tk.BooleanVar()
            chk = tk.Checkbutton(
                self.field_frame, text=f['key'], variable=var,
                font=("微软雅黑", 10), bg="#f4f4f9",
                command=lambda k=f['key']: self.on_field_click(k)
            )
            tip = tk.Label(
                self.field_frame, text="?", fg="#d32f2f",
                cursor="hand2", font=("微软雅黑", 11, "bold"), bg="#f4f4f9"
            )
            ToolTip(tip, f["desc"] )
            self.field_vars[f['key']] = var
            self.field_items.append((chk, tip))
        # 自适应布局绑定
        self.field_frame.bind('<Configure>', lambda e: self.relayout_fields())

        # 默认选中并更新预览
        for key in ["销方名称", "开票日期", "合计"]:
            self.select_field(key, True)
        self.update_preview()

    def filter_files(self):
        folder = self.folder_var.get()
        from rename_function import filter_duplicate_files
        filter_duplicate_files(folder)

    def relayout_fields(self):
        # 动态计算列数
        total_width = self.field_frame.winfo_width()
        cols = max(1, total_width // self.CELL_WIDTH)
        # 清理旧布局
        for chk, tip in self.field_items:
            chk.grid_forget()
            tip.grid_forget()
        # 重新布局
        for idx, (chk, tip) in enumerate(self.field_items):
            r = idx // cols
            c = (idx % cols) * 2
            chk.grid(row=r, column=c, sticky="w", padx=10, pady=4)
            tip.grid(row=r, column=c+1, sticky="w", padx=(0,20), pady=4)

    def clear_fields(self):
        self.selected_order.clear()
        for var in self.field_vars.values(): var.set(False)
        self.update_preview()

    def choose_folder(self):
        folder = filedialog.askdirectory(title="选择目标文件夹")
        if folder: self.folder_var.set(folder)

    def on_field_click(self, key):
        var = self.field_vars[key]
        if var.get() and key not in self.selected_order:
            self.selected_order.append(key)
        elif not var.get() and key in self.selected_order:
            self.selected_order.remove(key)
        self.update_preview()

    def select_field(self, key, select=True):
        var = self.field_vars[key]
        var.set(select)
        if select and key not in self.selected_order:
            self.selected_order.append(key)
        elif not select and key in self.selected_order:
            self.selected_order.remove(key)

    def update_preview(self):
        sel = self.selected_order
        split = self.split_var.get()
        text = split.join([f"{f}" for f in sel]) if sel else "（未选择）"
        self.rename_preview.set(text)

    # def confirm(self):
    #     if not self.selected_order:
    #         messagebox.showerror("错误", "请至少选择一个字段！")
    #         return
    #     if not self.folder_var.get():
    #         messagebox.showerror("错误", "请选择目标文件夹！")
    #         return
    #     cfg = {
    #         "fields": self.selected_order,
    #         "split": self.split_var.get(),
    #         "rename": self.rename_preview.get(),
    #         "folder": self.folder_var.get()
    #     }
    #     messagebox.showinfo("配置完成", f"{cfg}")
    #     self.destroy()
    #     print(cfg)
    # # ...
    def confirm(self):
        if not self.selected_order:
            messagebox.showerror("错误", "请至少选择一个字段！")
            return
        if not self.folder_var.get():
            messagebox.showerror("错误", "请选择目标文件夹！")
            return
        cfg = {
            "fields": self.selected_order,
            "split": self.split_var.get(),
            "rename": self.rename_preview.get(),
            "folder": self.folder_var.get()
        }
        if self.on_confirm:
            self.on_confirm(cfg)  # 调用外部回调，把配置数据传出去


if __name__ == "__main__":
    app = FieldSelector(fields)
    app.mainloop()
