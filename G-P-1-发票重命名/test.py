# import os
# import requests
# # DeepSeek API配置
# api_key = os.getenv('API_KEY')
# base_url = "https://chat.deepseek.com/api/v0/file/upload_file"
# # 打开本地MP4文件
# file_path = "content/25427000000411948251_2025年09月24日_武汉东湖学院_武汉京东世纪贸易有限公司.txt"
# with open(file_path, "rb") as file:
#    files = {"file": file}
#    headers = {
#        "Authorization": f"Bearer {api_key}",
#    }
#    # 发送POST请求
#    response = requests.post(base_url, headers=headers, files=files)
#    print(response.text)
# # 检查响应结果
# if response.status_code == 200:
#    print("上传成功:", response.json())
# else:
#    print("上传失败:", response.text)

from rename_function import run_main_ui_local
from chat_ai_rename import ImageOcrExtractor
def test_ocr2ai():
   cfg = {
      "folder": 'E:\其他\大学生创新创业\创新创业\发票',
      "fields": [
         "发票号码", "开票日期", "购方名称", "购方税号",
         "销方名称", "销方税号", "合计", "总税额",
         "价税合计", "价税合计大写", "开票人",
      ],
      "split": '_'
   }
   run_main_ui_local(cfg)

if __name__ == '__main__':

   # 1. 测试ocr识别图片 转成文本格式
   # OCR = ImageOcrExtractor()
   # path = r'E:\其他\大学生创新创业\创新创业\rename_c12f7139\25372000000053312804_2025年03月01日_武汉东湖学院_91370103575574929C_济南凝思图文制作有限公司_52420000753406283N_18.79_0_18.79_壹拾捌圆柒角玖分_杨斌.pdf'
   # text = OCR.extract_from_path(path)
   # print(text)

   # 2. 测试ocr识别图片 ai 再识别为结构化数据
   print("1. 测试ocr识别图片 ai 再识别为结构化数据")
   test_ocr2ai()