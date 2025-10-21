import os
import requests
# DeepSeek API配置
api_key = os.getenv('API_KEY')
base_url = "https://chat.deepseek.com/api/v0/file/upload_file"
# 打开本地MP4文件
file_path = "content/25427000000411948251_2025年09月24日_武汉东湖学院_武汉京东世纪贸易有限公司.txt"
with open(file_path, "rb") as file:
   files = {"file": file}
   headers = {
       "Authorization": f"Bearer {api_key}",
   }
   # 发送POST请求
   response = requests.post(base_url, headers=headers, files=files)
   print(response.text)
# 检查响应结果
if response.status_code == 200:
   print("上传成功:", response.json())
else:
   print("上传失败:", response.text)