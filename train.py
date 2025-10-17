import os
import io
import json
import base64
import img2pdf
import traceback
import tempfile
import shutil
from pdf2image import convert_from_path
from openai import OpenAI
from PIL import Image, ImageDraw

# --------- 配置 ---------
KEYS = ["邮箱", "本科学历", "硕士学历", "任职公司"]  # 根据需要增删
MODELSCOPE_TOKEN = "ms-3e77e144-197b-44f3-93be-87c5d0f0ce16" # 请替换为您的真实密钥
DPI = 300
OUTPUT_FOLDER = 'output'
LOCAL_INPUT_FOLDER = 'input'

# **请将您的本地 PDF 文件放入此目录下，并修改下面的路径变量**
LOCAL_PDF_FILENAME = "your_resume.pdf" 
LOCAL_PDF_PATH = "/mnt/d/project/my-app/annotated_resume.pdf"

# 创建必要的目录
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(LOCAL_INPUT_FOLDER, exist_ok=True)


# --------- 1. PDF → PNG ---------
def pdf_to_images(pdf_path, out_dir, dpi=DPI):
    """将PDF转换为PNG图片"""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"找不到文件: {pdf_path}")
    os.makedirs(out_dir, exist_ok=True)
    # convert_from_path 默认需要 poppler 库支持
    pages = convert_from_path(pdf_path, dpi=dpi) 
    out_paths = []
    for i, page in enumerate(pages, start=1):
        fn = os.path.join(out_dir, f"page_{i:03d}.png")
        page.save(fn, "PNG")
        out_paths.append(fn)
    return out_paths

# --------- 2. 批量提取多字段坐标 ---------
class ResumeFieldLocator:
    def __init__(self, api_key, base_url="https://api-inference.modelscope.cn/v1"):
        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def locate_keys(self, image_path, keys: list):
        """一次性对一张图提取 keys 列表中所有字段的 value + box"""
        try:
            # 读图并 base64 编码
            with open(image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()

            # **********************************************
            # 关键修改：增强提示词，明确要求返回边界框，即使是复杂字段
            # **********************************************
            system = {
            "role": "system",
            "content": (
                "你是一个 OCR+版面理解模型，给定一张文档图和字段列表，"
                "请找到每个字段对应的 value 和 bounding box 坐标，"
                "输出格式为JSON，格式如下："
                "{\"字段名1\": {\"value\": \"值1\", \"box\": [x0, y0, x1, y1]}, \"字段名2\": [{\"value\": \"值2\", \"box\": [x0, y0, x1, y1]}, ...]}"
                "其中box是一个包含四个**整数**元素的数组，表示矩形框的坐标[x0, y0, x1, y1]，坐标应精确到像素。"
                "**核心规则：如果成功提取了字段内容（value 非空），那么必须返回对应的 box 坐标。**"
                "对于 '本科学历' 或 '硕士学历' 这种复杂字段，请返回其在图中最小的**完整包围框**，而不是空值。"
                "如果字段在当前图片上不存在，则对应值为空字符串或空数组。"
                "只输出JSON，不要额外文本。"
            ),
            }
            
            user = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"fields: {','.join(keys)}"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{b64}"
                    }
                }
            ]
             }
            
            resp = self.client.chat.completions.create(
                model="Qwen/Qwen3-VL-8B-Instruct",
                messages=[system, user],
                stream=False,
                timeout=60
            )
            txt = resp.choices[0].message.content
            # 解析JSON
            try:
                # 尝试修复由于模型输出不稳定导致的 JSON 格式问题
                if txt.startswith("```json"):
                    txt = txt = txt.replace("```json", "").replace("```", "").strip()
                    
                result = json.loads(txt)
                return result if isinstance(result, dict) else {}
            except json.JSONDecodeError:
                print(f"JSON解析失败，原始输出: {txt}")
                return {}
        except Exception as e:
            print(f"locate_keys 错误: {e}")
            traceback.print_exc()
            return {}

# --------- 3. 在图片上画红框 ---------
def annotate_image(image_path, detections: dict, out_path):
    """
    在图片上根据 detections 标注红框。
    detections 格式：{ key1: {"value": "...", "box": [x0, y0, x1, y1]}, 
                      key2: [{"value": "...", "box": [x0, y0, x1, y1]}, ...], ... }
    """
    try:
        if not detections:
            img = Image.open(image_path)
            img.save(out_path)
            return
            
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        
        def draw_single_box(box_coords):
            # **********************************************
            # 关键修改：坐标健壮性检查和类型转换
            # **********************************************
            if box_coords and isinstance(box_coords, (list, tuple)) and len(box_coords) == 4:
                # 确保坐标是整数，并按 PIL/ImageDraw 要求输入 (x0, y0, x1, y1)
                try:
                    box = [int(c) for c in box_coords]
                    # 简单校验 x0 < x1 且 y0 < y1
                    if box[0] < box[2] and box[1] < box[3]:
                         draw.rectangle(box, outline="red", width=3)
                    else:
                         print(f"警告: 坐标不合法或顺序错误: {box_coords}")
                except ValueError:
                    print(f"警告: 坐标非整数类型: {box_coords}")

        if detections:
            for key, info in detections.items():
                if isinstance(info, dict) and "box" in info:
                    # 单个对象格式
                    draw_single_box(info.get("box"))
                elif isinstance(info, list):
                    # 列表格式
                    for item in info:
                        if isinstance(item, dict) and "box" in item:
                            draw_single_box(item.get("box"))
        
        img.save(out_path)
    except Exception as e:
        print(f"annotate_image 错误: {e}")
        tracebox.print_exc()

# --------- 4. 处理PDF文件 (保持多页转换逻辑) ---------
def process_pdf(pdf_path):
    """处理PDF文件并返回标注后的PDF路径 和 提取的数据"""
    temp_dir = tempfile.mkdtemp()
    pages_dir = os.path.join(temp_dir, "pages")
    annotated_dir = os.path.join(temp_dir, "annotated")
    all_extracted_data = {} 
    
    try:
        print(f"开始处理PDF: {pdf_path}")
        
        # 1. PDF→PNG
        print("步骤1: 转换PDF为PNG图片...")
        pngs = pdf_to_images(pdf_path, pages_dir, dpi=DPI)
        print(f"转换完成，共生成 {len(pngs)} 页图片")
        
        # 2. 调用 ModelScope 批量提取字段
        print("步骤2: 提取字段信息...")
        locator = ResumeFieldLocator(api_key=MODELSCOPE_TOKEN)
        annotated_png_paths = []
        
        for i, img_path in enumerate(pngs):
            print(f"处理第 {i+1} 页: {img_path}")
            det = locator.locate_keys(img_path, KEYS)
            
            # 记录提取结果
            all_extracted_data[f"page_{i+1}"] = det 
            print(f"第 {i+1} 页提取结果: {det}")
            
            # 保存带框图片
            fn = os.path.basename(img_path)
            out_img = os.path.join(annotated_dir, fn)
            os.makedirs(annotated_dir, exist_ok=True)
            annotate_image(img_path, det, out_img)
            annotated_png_paths.append(out_img)
            print(f"第 {i+1} 页标注完成: {out_img}")
        
        # 3. 转换为多页PDF
        print("步骤3: 转换为多页PDF...")
        output_pdf_filename = f"annotated_{os.path.splitext(os.path.basename(pdf_path))[0]}.pdf"
        output_pdf = os.path.join(OUTPUT_FOLDER, output_pdf_filename)
        
        pdf_bytes = img2pdf.convert(annotated_png_paths) 
        with open(output_pdf, "wb") as f:
            f.write(pdf_bytes)
        print(f"PDF生成完成: {output_pdf}")
            
        return output_pdf, all_extracted_data 
    
    except Exception as e:
        print(f"process_pdf 错误: {e}")
        traceback.print_exc()
        raise e
    finally:
        # 清理临时目录
        print(f"清理临时目录: {temp_dir}")
        shutil.rmtree(temp_dir, ignore_errors=True)

# --------- 主流程 ---------
if __name__ == "__main__":
    
    # 检查本地文件是否存在
    if not os.path.exists(LOCAL_PDF_PATH):
        print("\n--- 启动失败 ---")
        print(f"错误: 找不到本地PDF文件路径: {LOCAL_PDF_PATH}")
        print("请在脚本所在目录创建 'input' 文件夹，并将您的PDF文件放入其中。")
        print(f"请修改 LOCAL_PDF_FILENAME = \"{LOCAL_PDF_FILENAME}\" 以匹配您的文件名。")
    else:
        try:
            print(f"开始处理本地文件: {LOCAL_PDF_PATH}")
            output_pdf_path, extracted_data = process_pdf(LOCAL_PDF_PATH)
            
            print("\n====================================")
            print("         ✅ 任务完成 ✅             ")
            print("====================================")
            print(f"标注后的PDF已保存至: {output_pdf_path}")
            print("\n--- 提取的结构化数据 ---")
            print(json.dumps(extracted_data, ensure_ascii=False, indent=4))
            
        except Exception as e:
            print(f"处理失败: {e}")
