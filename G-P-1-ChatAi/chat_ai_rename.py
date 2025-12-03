import os
import random
import time
from typing import Optional, Dict

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from openai import RateLimitError
from pydantic import BaseModel, Field


# --- 1. 定义 Pydantic 输出模型 ---
# 这个模型定义了我们希望从发票中提取的所有信息结构
class InvoiceInfo(BaseModel):
    """从发票中提取的结构化信息模型"""
    invoice_number: Optional[str] = Field(default=None, description="发票上的唯一号码（如：2511700000321326035）")
    issue_date: Optional[str] = Field(default=None, description="发票开票日期，格式为YYYY年MM月DD日（如：2025年02月27日）")
    buyer_name: Optional[str] = Field(default=None, description="购买方公司名称（如：武汉东湖学院）")
    buyer_tax_id: Optional[str] = Field(default=None, description="购买方统一社会信用代码/纳税人识别号")
    seller_name: Optional[str] = Field(default=None, description="销售方公司名称（如：腾讯云计算（北京）有限责任公司）")
    seller_tax_id: Optional[str] = Field(default=None, description="销售方统一社会信用代码/纳税人识别号")
    total_amount: Optional[str] = Field(default=None, description="发票合计金额（不含税，如：94.34）")
    total_tax: Optional[str] = Field(default=None, description="发票合计税额（如：5.66）")
    total_including_tax: Optional[str] = Field(default=None, description="发票价税合计，仅数字（如：100.00）")
    total_including_tax_in_words: Optional[str] = Field(default=None, description="价税合计（大写），如：壹佰元整")
    preparer: Optional[str] = Field(default=None, description="开票人姓名（如：王丽丽）")


# --- 2. 创建封装类 ---
class InvoiceExtractor:
    """
    一个用于从发票文本中提取结构化信息的封装类。
    """
    # --- 新增：中文显示名到 Pydantic 模型字段名的映射 ---
    _FIELD_MAP = {
        "发票号码": "invoice_number",
        "开票日期": "issue_date",
        "购方名称": "buyer_name",
        "购方税号": "buyer_tax_id",
        "销方名称": "seller_name",
        "销方税号": "seller_tax_id",
        "合计": "total_amount",
        "总税额": "total_tax",
        "价税合计": "total_including_tax",
        "价税合计大写": "total_including_tax_in_words",
        "开票人": "preparer",
    }

    def __init__(
            self,
            model_name: str = 'moonshot-v1-8k',
            api_key: str = None,
            temperature: float = 0.0
        ):
        """
        初始化提取器。

        :param model_name: 要使用的模型名称，例如 'moonshot-v1-8k' 或 'deepseek-chat'。
        :param api_key: OpenAI API Key。如果为 None，将从环境变量 OPENAI_API_KEY 读取。
        :param temperature: 模型的温度参数。
        """
        # 设置 API Key（如果提供了的话）
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key

        # 初始化模型和提示
        self.model = ChatOpenAI(model_name=model_name, temperature=temperature)

        self.prompt = ChatPromptTemplate.from_messages([
            ("system",
             "你是一个专业的发票信息提取算法。请仅从用户提供的发票文本中提取相关信息，"
             "并填充到预定义的JSON结构中。如果某个字段的值在文本中找不到，请不要编造，"
             "让该字段的值为null。"
             "如果遇到 下面这样的"
             "'名称：武汉东湖学院"
             " 名称：中国移动通信集团湖北有限公司武汉分公司"
             " 一社会信用代码/纳税人识别号：52420000123406283N"
             " 一社会信用代码/纳税人识别号：91420100717918134N'"
             "切记 购方税号 和 销方税号是按照 单位名称顺序对应"
             "即：武汉东湖学院-52420000123406283N"
             ),
            ("human", "{invoice_text}")
        ])

        # 创建结构化输出链
        # 注意：根据之前的讨论，如果模型不支持 json_schema，需要显式指定 method="function_calling"
        # 对于 moonshot 和 deepseek，通常需要这样做。
        self.extraction_chain = self.prompt | self.model.with_structured_output(InvoiceInfo, method="function_calling")

    def extract(self, invoice_text: str) -> Dict[str, Optional[str]]:
        """
        从给定的发票文本中提取信息，包含自动重试逻辑。

        :param invoice_text: 发票的完整原始文本。
        :return: 一个字典，包含提取的字段和值。如果字段未找到，值为 None。
        """
        max_retries = 3
        initial_wait = 60  # 首次重试等待2秒
        retries = 0
        wait_time = initial_wait

        while retries <= max_retries:
            try:
                # 尝试调用API
                extracted_info: InvoiceInfo = self.extraction_chain.invoke({"invoice_text": invoice_text})
                return extracted_info.model_dump()

            except RateLimitError as e:
                # 专门捕获速率限制错误
                retries += 1
                if retries > max_retries:
                    print(f"❌ 达到最大重试次数 {max_retries}，放弃重试。最终错误：{e}")
                    # --- 修复点：使用 .keys() 获取字段名 ---
                    return {key: None for key in InvoiceInfo.model_fields.keys()}

                print(f"⚠️ API 速率限制 (429)，将在 {wait_time} 秒后进行第 {retries} 次重试...")
                time.sleep(wait_time)
                wait_time *= 1.5  # 指数退避：下次等待时间翻倍 (2s, 4s, 8s...)

            except Exception as e:
                # 对于其他类型的错误（如网络问题、API密钥错误），直接返回失败
                print(f"❌ 处理过程中发生非速率限制错误：{e}")
                # --- 修复点：使用 .keys() 获取字段名 ---
                return {key: None for key in InvoiceInfo.model_fields.keys()}

        # 理论上不会执行到这里，但为了代码完整性
        return {key: None for key in InvoiceInfo.model_fields.keys()}

    # --- 新增函数 ---
    def format_by_fields(self, extracted_data: Dict[str, Optional[str]], fields: list[str]) -> Dict[str, Optional[str]]:
        """
        根据用户提供的中文字段列表，从提取的数据中筛选并格式化输出。

        :param extracted_data: extract 方法返回的原始字典。
        :param fields: 用户需要的字段列表，例如 ['开票日期', '总税额']。
        :return: 一个新的字典，键是用户传入的中文名，值是对应的提取结果。
        """
        formatted_result = {}
        for chinese_key in fields:
            # 从映射表中找到对应的英文键
            english_key = self._FIELD_MAP.get(chinese_key)

            if english_key:
                # 用英文键从原始数据中取值
                value = extracted_data.get(english_key)
                formatted_result[chinese_key] = value
            else:
                # 如果找不到映射，可以给出提示或赋值为 None
                formatted_result[chinese_key] = None
                print(f"⚠️ 警告：未知的字段名 '{chinese_key}'，已将其值设为 None。")

        return formatted_result

    # 调用ai方法 文本专用
    def get_rename_by_chat_ai(self, invoice_text, fields, split):
        # 1. 先提取所有信息
        full_data_dict = self.extract(invoice_text)

        # 2. 调用新函数，按需格式化
        formatted_data = self.format_by_fields(full_data_dict, fields)
        time.sleep(random.randint(1, 3))
        # 3. 改成文件命名
        return split.join(formatted_data.values())

######################### 下面是用ocr识别图片，不太准 #########################
from typing import Union, List
import numpy as np
from PIL import Image
from paddleocr import PaddleOCR
from pdf2image import convert_from_path
import logging
logging.getLogger('ppocr').setLevel(logging.ERROR)   # 只显示错误

# --- 1. 创建封装类 ---
class ImageOcrExtractor:
    """
    一个用于从图片或PDF文件中提取文本的封装类。
    """

    def __init__(self, use_angle_cls: bool = True, lang: str = 'ch'):
        """
        初始化OCR提取器，并加载PaddleOCR模型。

        :param use_angle_cls: 是否使用文字方向分类器。
        :param lang: 指定OCR的语言，'ch'代表中文。
        """
        # 在实际项目中，请使用下面这行
        self.ocr = PaddleOCR(use_angle_cls=use_angle_cls, lang=lang)

    def _extract_text_from_single_image(self, image: Union[np.ndarray, Image.Image]) -> str:
        """
        从单个图像对象（PIL.Image 或 np.ndarray）中提取文本。

        :param image: 图像对象。
        :return: 提取出的合并文本字符串。
        """
        # 如果是PIL图像，转换为numpy数组
        if isinstance(image, Image.Image):
            image = np.array(image)

        # 调用OCR进行识别
        result = self.ocr.ocr(image, cls=True)

        # 检查结果是否为空
        if not result or not result[0]:
            return ""

        # 提取所有文本行并合并
        text_lines = [line[1][0] for line in result[0]]
        return '\n'.join(text_lines)

    def extract_from_path(self, file_path: str) -> str:
        """
        从图片文件或PDF文件的路径中提取所有文本。

        :param file_path: 文件的路径。
        :return: 提取出的完整文本字符串。
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件未找到: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        images: List[Image.Image] = []

        # 根据文件扩展名处理
        if ext == '.pdf':
            try:
                # 将PDF转换为PIL图像列表
                images = convert_from_path(file_path, dpi=300)
            except Exception as e:
                return f"处理PDF文件时出错: {e}"
        elif ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']:
            try:
                # 打开单个图片文件
                images = [Image.open(file_path)]
            except Exception as e:
                return f"打开图片文件时出错: {e}"
        else:
            return f"不支持的文件类型: {ext}"

        # 遍历所有图像页，提取文本并合并
        image_text = ''
        for i, img in enumerate(images):
            # print(f"正在处理第 {i + 1}/{len(images)} 页...")
            image_text += self._extract_text_from_single_image(img)
            if i < len(images) - 1:
                image_text += "\n\n"  # 在不同页面之间添加分隔

        return image_text
