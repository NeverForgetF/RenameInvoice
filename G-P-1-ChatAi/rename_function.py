import os
import re
import time
import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import shutil

import pdfplumber
import hashlib
import uuid
from chat_ai_rename import InvoiceExtractor, ImageOcrExtractor


def get_backup_dir(pdf_dir):
    parent_dir = os.path.dirname(pdf_dir.rstrip(os.sep))
    base_bak_dir = os.path.join(parent_dir, 'rename')

    # 生成随机后缀，取uuid的前8位，确保唯一
    random_suffix = uuid.uuid4().hex[:8]

    bak_dir = base_bak_dir + "_" + random_suffix

    # 如果刚好存在（概率极低），循环生成新的
    while os.path.abspath(bak_dir) == os.path.abspath(pdf_dir) or os.path.exists(bak_dir):
        random_suffix = uuid.uuid4().hex[:8]
        bak_dir = base_bak_dir + "_" + random_suffix

    os.makedirs(bak_dir, exist_ok=True)
    return bak_dir

def sanitize_filename(name):
    # 替换Windows文件名非法字符为下划线
    return re.sub(r'[\\/:*?"<>|]', '_', name)


def extract_projects(text):
    # 先定位“项目名称”后面跟的项目数据起始位置
    # 这里假设“项目名称 规格型号 单 位 数 量 单 价 金 额 税率/征收率 税 额”是表头
    table_header_pattern = r"项目名称\s*规格型号\s*单\s*位\s*数\s*量\s*单\s*价\s*金\s*额\s*税率/征收率\s*税\s*额"

    header_match = re.search(table_header_pattern, text)
    if not header_match:
        return []  # 找不到表头，返回空列表

    start_pos = header_match.end()  # 表头结束位置
    # 截取表头之后的文本，假设项目行以换行或“合计”之类结束
    project_text = text[start_pos:]
    # 一般项目以“合计”开始或者“价税合计”开始结束
    end_match = re.search(r"合\s*计|价税合计", project_text)
    end_pos = end_match.start() if end_match else len(project_text)
    project_text = project_text[:end_pos]

    # 定义项目行的正则，按字段顺序捕获，假设字段间空格或星号分隔
    # 这里示范一条项目行匹配：项目名称、规格型号、单位、数量、单价、金额、税率、税额
    # 注意项目名称可能包含空格和星号，我们用非贪婪匹配
    project_line_pattern = re.compile(
        r"(\*?.*?\*?)\s+"      # 项目名称，可能带*号
        r"(\S*?)\s+"           # 规格型号，允许为空
        r"(\S+)\s+"            # 单位
        r"([\d\.]+)\s+"        # 数量
        r"([\d\.]+)\s+"        # 单价
        r"([\d\.]+)\s+"        # 金额
        r"([\d\*%]+)\s+"       # 税率或征收率，允许*或%
        r"([\d\*\.]+)"         # 税额，允许*或数字
    )

    projects = []
    for match in project_line_pattern.finditer(project_text):
        project = {
            "项目名称": match.group(1).strip(),
            "规格型号": match.group(2).strip(),
            "单位": match.group(3).strip(),
            "数量": match.group(4).strip(),
            "单价": match.group(5).strip(),
            "金额": match.group(6).strip(),
            "税率": match.group(7).strip(),
            "税额": match.group(8).strip(),
        }
        projects.append(project)

    return projects

def extract_fields_from_text(text, fields):
    results = {}

    # 这里text已经是合并空白后的完整字符串
    # 先合并多余空白
    text = re.sub(r'\s+', ' ', text)

    # 1. 统一提取所有“统一社会信用代码/纳税人识别号”后的号码（按顺序）
    tax_numbers = re.findall(r"统一社会信用代码/纳税人识别号[：:]\s*([\w\d]+)", text)
    buy_tax_number = tax_numbers[0] if len(tax_numbers) > 0 else ""
    sell_tax_number = tax_numbers[1] if len(tax_numbers) > 1 else ""
    if "购方税号" in fields:
        results["购方税号"] = buy_tax_number
    if "销方税号" in fields:
        results["销方税号"] = sell_tax_number

    # 2. 购方名称 + 销方名称 （一行内）
    m = re.search(r"购\s*名称[：:]\s*(.*?)\s+销\s*名称[：:]\s*(.*?)\s", text)
    if m:
        if "购方名称" in fields:
            results["购方名称"] = m.group(1).strip()
        if "销方名称" in fields:
            results["销方名称"] = m.group(2).strip()

    # 3. 发票号码
    m = re.search(r"发票号码[：:]\s*([\d\w]+)", text)
    if "发票号码" in fields:
        results["发票号码"] = m.group(1).strip() if m else ""

    # 4. 开票日期
    m = re.search(r"开票日期[：:]\s*([\d年月日\-]+)", text)
    if "开票日期" in fields:
        results["开票日期"] = m.group(1).strip() if m else ""

    # 5. 合计金额
    m = re.search(r"合\s*计\s*¥?([\d\.]+)", text)
    if "合计" in fields:
        results["合计"] = m.group(1).strip() if m else ""

    # 如果没有明确字段“总税额”，你可以尝试匹配合计行后紧跟的数字，或者暂时置空
    m = re.search(r"合\s*计.*?¥?([\d\.]+)\s*\*?\s*¥?([\d\.]+)", text)
    if m and "总税额" in fields:
        # 如果匹配到两组金额，则第二组是总税额
        results["总税额"] = m.group(2).strip()

    # 6. 价税合计（数字，小写）
    m = re.search(r"价税合计.*（小写）¥([\d\.]+)", text, re.DOTALL)
    if "价税合计" in fields:
        results["价税合计"] = m.group(1).strip() if m else ""

    # 7. 价税合计（大写）
    m = re.search(r"价税合计（大写）\s*([\S]+)", text)
    if "价税合计大写" in fields:
        results["价税合计大写"] = m.group(1).strip() if m else ""

    # 8. 开票人
    m = re.search(r"开票人[:：]\s*([\S]+)", text)
    if "开票人" in fields:
        results["开票人"] = m.group(1).strip() if m else ""

    # # 9. 备注（匹配“备 注”到“开票人”之间的内容）
    # m = re.search(r"备\s*注\s*(.*?)(?=开票人|$)", text, re.DOTALL)
    # if "备注" in fields:
    #     results["备注"] = m.group(1).strip() if m else ""

    # # 多条项目解析
    # if any(f in fields for f in ["项目名称", "规格型号", "单位", "数量", "单价", "金额", "税率", "税额"]):
    #     projects = extract_projects(text)
    #     # 如果只想要第一条项目
    #     if projects:
    #         first_project = projects[0]
    #         for key in first_project:
    #             if key in fields:
    #                 results[key] = first_project[key]
    #     else:
    #         # 没有项目数据就空
    #         for key in ["项目名称", "规格型号", "单位", "数量", "单价", "金额", "税率", "税额"]:
    #             if key in fields:
    #                 results[key] = ""

    return results

# 提取pdf文本
import pdfplumber
def get_full_text(text_area, file_path):
    """
    从 PDF 文件中提取文本内容。
    如果提取失败或文件打不开，返回 None，并在 text_area 显示错误信息。
    """
    try:
        with pdfplumber.open(file_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:  # 如果页面提取到文本
                    full_text += page_text + "\n"
            # 如果整个文档没有提取到任何文本，返回 None
            if not full_text.strip():
                text_area.insert(tk.END, "PDF 中未提取到有效文本。\n")
                text_area.see(tk.END)
                return None
    except Exception as e:
        text_area.insert(tk.END, f"打开PDF失败: {e}\n")
        text_area.see(tk.END)
        return None
    return full_text


def process_files_local(text_area, pdf_dir, fields, split, rename_rule):
    text_area.insert(tk.END, f"开始处理目录：{pdf_dir}\n")
    text_area.see(tk.END)

    bak_dir = get_backup_dir(pdf_dir)
    text_area.insert(tk.END, f"备份目录为：{bak_dir}\n")
    text_area.see(tk.END)

    ai_extractor = InvoiceExtractor(model_name=os.environ.get("MODEL_NAME", 'moonshot-v1-8k'))
    ocr_extractor = ImageOcrExtractor()
    count = 0
    # 文件备份
    for filename in os.listdir(pdf_dir):
        src = os.path.join(pdf_dir, filename)
        dst = os.path.join(bak_dir, filename)
        shutil.copy2(src, dst)
        count += 1
    text_area.insert(tk.END, f"已备份{count}个PDF文件到：{bak_dir}\n")
    text_area.see(tk.END)

    total = 0   # 总数
    success_count = 0   # 处理成功总数
    filename_same_count = 0     # 文件名冲突数
    for filename in os.listdir(bak_dir):
        total += 1
        file_path = os.path.join(bak_dir, filename)
        text_area.insert(tk.END, f"\n处理文件：{filename}\n")
        text_area.see(tk.END)
        full_text = get_full_text(text_area, file_path)
        field_values = extract_fields_from_text(full_text, fields) if full_text is not None else None
        if filename.lower().endswith('.pdf') and full_text is not None and any(field_values.values()):
            parts = [field_values.get(key, "") for key in fields]
            new_name_base = split.join(parts)
        else:
            # 不是pdf，就走图片识别
            text_area.insert(tk.END, "\n未提取到有效字段，图片识别发票中，请稍候...")
            text_area.see(tk.END)
            full_text = ocr_extractor.extract_from_path(file_path)
            new_name_base = ai_extractor.get_rename_by_chat_ai(full_text, fields, split)

        # 如果 new_name_base 有两个 __ ，说明图片识别没有成功
        # 直接把文本扔给ai识别
        if '__' in new_name_base or new_name_base[0] == '_' or new_name_base[-1] == '_':
            text_area.insert(tk.END, "\nAI处理发票中，请稍候...")
            text_area.see(tk.END)
            new_name_base = ai_extractor.get_rename_by_chat_ai(full_text, fields, split)
        # 提取原始文件的后缀名
        _, original_ext = os.path.splitext(filename)
        # 将新的文件名基础部分与原始后缀名拼接
        new_name = sanitize_filename(new_name_base) + original_ext
        new_path = os.path.join(bak_dir, new_name)
        if os.path.exists(new_path):
            filename_same_count += 1
            text_area.insert(tk.END, f"文件名冲突，加个随机数: {new_name}\n")
            text_area.see(tk.END)
            new_path = sanitize_filename(new_name_base) + time.strftime("%Y%m%d%H%M%S") + original_ext

        try:
            os.rename(file_path, new_path)
            text_area.insert(tk.END, f"重命名成功: {filename} -> {new_name}\n")
            text_area.see(tk.END)
            success_count += 1
        except Exception as e:
            text_area.insert(tk.END, f"重命名失败: {e}\n")
            text_area.see(tk.END)

    text_area.insert(tk.END, f"\n全部处理完成。共处理{total}个PDF，成功重命名{success_count}个。\n")
    text_area.see(tk.END)
    messagebox.showinfo("处理完成", f"全部处理完成。共处理{total}个PDF，成功重命名{success_count}个，其中文件名冲突{filename_same_count}个。")

def run_main_ui_local(cfg):
    root = tk.Tk()
    root.title("本地PDF智能重命名工具")

    pdf_dir = cfg.get("folder", "")
    fields = cfg.get("fields", [])
    split = cfg.get("split", "_")
    rename_rule = cfg.get("rename", "")

    text_area = scrolledtext.ScrolledText(root, width=80, height=24, font=("微软雅黑", 11))
    text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    text_area.insert(tk.INSERT, "文件名中若出现非法字符已被替换为下划线。\n")
    text_area.see(tk.END)

    def finish_and_return():
        try:
            if root.winfo_exists():
                root.destroy()
        except Exception:
            pass

    def threaded_process():
        process_files_local(text_area, pdf_dir, fields, split, rename_rule)
        # finish_and_return()

    threading.Thread(target=threaded_process, daemon=True).start()
    root.mainloop()

def filter_duplicate_files(folder):
    if not os.path.isdir(folder):
        messagebox.showerror("错误", f"目录不存在: {folder}")
        return

    hash_map = {}
    removed = []
    total = 0

    for fname in os.listdir(folder):
        path = os.path.join(folder, fname)
        if not os.path.isfile(path):
            continue
        with open(path, "rb") as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        if file_hash in hash_map:
            try:
                os.remove(path)
                removed.append(fname)
            except Exception as e:
                messagebox.showerror("删除失败", f"{fname} 删除失败: {e}")
        else:
            hash_map[file_hash] = path
        total += 1

    msg = f"共检测到{total}个文件，已删除{len(removed)}个重复文件。"
    if removed:
        msg += "\n已删除文件:\n" + "\n".join(removed)
    messagebox.showinfo("过滤完成", msg)
