import hashlib
import os
import re
import tkinter as tk
from tkinter import messagebox, scrolledtext
import requests
import json
import shutil
import threading

def run_play(file_id, ACCESS_TOKEN, WORKFLOW_ID, system):
    url = 'https://api.coze.cn/v1/workflow/run'
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        "workflow_id": WORKFLOW_ID,
        "parameters": {
            "system": system,
            "image": "{\"file_id\": \"" + file_id + "\"}"
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.json()

def upload_file(file_path, ACCESS_TOKEN):
    upload_url = "https://api.coze.cn/v1/files/upload"
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}'
    }
    with open(file_path, "rb") as file:
        files = {"file": file}
        print(files)
        resp = requests.post(upload_url, headers=headers, files=files).json()
        if resp.get("data") and resp["data"].get("id"):
            print(resp['data']['id'])
            return resp["data"]["id"]
        else:
            return None

def get_backup_dir(pdf_dir):
    parent_dir = os.path.dirname(pdf_dir.rstrip(os.sep))
    base_bak_dir = os.path.join(parent_dir, 'rename')
    bak_dir = base_bak_dir
    idx = 1
    while os.path.abspath(bak_dir) == os.path.abspath(pdf_dir) or os.path.abspath(bak_dir) == os.path.abspath(base_bak_dir) and os.path.exists(bak_dir):
        if idx == 1:
            bak_dir = base_bak_dir + "（副本）"
        else:
            bak_dir = base_bak_dir + f"（副本{idx}）"
        idx += 1
    os.makedirs(bak_dir, exist_ok=True)
    return bak_dir

def process_files(text_area, ACCESS_TOKEN, pdf_dir, WORKFLOW_ID, field_list, split, rename_rule):
    with open('发票命名规则.txt', 'r', encoding='utf-8') as f:
        system = f.read()
    fields = "、".join(field_list)
    system = system.replace('fields', fields)
    system = system.replace('split', "'" + split + "'")
    system = system.replace('rename', rename_rule)
    # print(system)
    text_area.insert(tk.INSERT, "AI 系统提示词如下：\n")
    text_area.insert(tk.END, system + '\n\n')
    bak_dir = get_backup_dir(pdf_dir)
    text_area.insert(tk.END, f"你选择的文件夹是：{pdf_dir}\n")
    text_area.insert(tk.END, f"命名规则：{rename_rule}\n")
    text_area.insert(tk.END, "开始处理...\n")
    text_area.insert(tk.END, f"\n正在备份PDF文件到：{bak_dir}\n")
    text_area.see(tk.END)
    count = 0
    for filename in os.listdir(pdf_dir):
        if filename.lower().endswith('.pdf'):
            src = os.path.join(pdf_dir, filename)
            dst = os.path.join(bak_dir, filename)
            shutil.copy2(src, dst)
            count += 1
    text_area.insert(tk.END, f"已备份{count}个PDF文件到 {bak_dir}\n")
    text_area.see(tk.END)

    total = 0
    for filename in os.listdir(bak_dir):
        if not filename.lower().endswith('.pdf'):
            continue
        old_path = os.path.join(bak_dir, filename)
        text_area.insert(tk.END, f"\n正在上传：{filename} ...\n")
        text_area.see(tk.END)
        file_id = upload_file(old_path, ACCESS_TOKEN)
        if not file_id:
            text_area.insert(tk.END, f"上传失败：{filename}\n")
            text_area.see(tk.END)
            continue
        try:
            run_result = run_play(file_id, ACCESS_TOKEN, WORKFLOW_ID, system).get("data")
            if run_result is None:
                raise ValueError("API未返回预期字符串")
            if not isinstance(run_result, str):
                raise ValueError("API未返回预期字符串")
            output_dict = json.loads(run_result)
            new_name = output_dict['output'] + '.pdf'
            new_name = re.sub(r'[\\/:*?"<>|]', 'FORBIDDEN_CHARS', new_name)
        except Exception as e:
            text_area.insert(tk.END, f"获取新文件名失败：{filename}，错误：{e}\n")
            text_area.see(tk.END)
            continue
        new_path = os.path.join(bak_dir, new_name)
        if os.path.exists(new_path):
            text_area.insert(tk.END, f"文件名冲突：{new_name}，跳过\n")
            text_area.see(tk.END)
            continue
        os.rename(old_path, new_path)
        text_area.insert(tk.END, f"重命名：{filename} -> {new_name}\n")
        text_area.see(tk.END)
        total += 1

    text_area.insert(tk.END, f"\n全部处理完成！共成功处理{total}个PDF。\n")
    text_area.see(tk.END)
    messagebox.showinfo("处理完成", f"全部处理完成！共成功处理{total}个PDF。")

def run_main_ui(cfg, on_done=None):
    root = tk.Tk()
    root.title("Coze PDF智能重命名工具")

    pdf_dir = cfg.get("folder", "")
    fields = cfg.get("fields", [])
    split = cfg.get("split", "")
    rename_rule = cfg.get("rename", "")

    try:
        with open('./config.json', "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        tk.messagebox.showerror("错误", f"读取config.json失败：{e}\n请将config.json放在本程序同目录！")
        root.destroy()
        return

    access_token = config["access_token"]
    workflow_id = config.get("workflow_id", "")

    text_area = scrolledtext.ScrolledText(root, width=80, height=24, font=("微软雅黑", 11))
    text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    text_area.see(tk.END)
    text_area.insert(tk.INSERT, "文件名中若出现 FORBIDDEN_CHARS 字符串说明 字段 中有不符合文件名规则的符合......\n")

    def finish_and_return():
        try:
            if root.winfo_exists():
                root.destroy()
        except Exception:
            pass
        if on_done:
            on_done()

    def threaded_process():
        process_files(text_area, access_token, pdf_dir, workflow_id, fields, split, rename_rule)
        finish_and_return()

    threading.Thread(target=threaded_process, daemon=True).start()
    root.mainloop()


def filter_duplicate_files(folder):
    """
    检查folder下所有文件，按内容去重（保留一个，删除其它重复的）。
    """
    if not os.path.isdir(folder):
        messagebox.showerror("错误", f"目录不存在: {folder}")
        return

    hash_map = {}  # hash值 -> 文件路径
    removed = []
    total = 0

    for fname in os.listdir(folder):
        path = os.path.join(folder, fname)
        if not os.path.isfile(path):
            continue
        with open(path, "rb") as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        if file_hash in hash_map:
            # 已存在相同内容，删除当前文件
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


if __name__ == '__main__':
    with open('发票命名规则.txt', 'r', encoding='utf-8') as f:
        system = f.read()
    file_id = upload_file(r"C:\Users\Lenovo\Desktop\发票重命名\pdfs\25427000000075998447_IBOSS27001.pdf",
                "sat_sjfxQImkTziWtLQ3xXkcbGGHuVThmGcISfwLItos0MVz28px7PpdJjvDEp4y03hK")
    data = run_play(file_id, "sat_sjfxQImkTziWtLQ3xXkcbGGHuVThmGcISfwLItos0MVz28px7PpdJjvDEp4y03hK", "7552460259597926440", system)
    print(data)
