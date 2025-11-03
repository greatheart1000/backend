import fitz  # PyMuPDF for PDF handling
from PIL import Image, ImageDraw, ImageFont
import json
import io
import re
import numpy as np
from typing import List, Dict, Tuple, Optional
from paddleocr import PaddleOCR
import base64

# --- 1. 初始化和配置 ---

try:
    ocr_engine = PaddleOCR(use_angle_cls=True, lang="ch", use_gpu=False, show_log=False)
except Exception as e:
    print(f"PaddleOCR 初始化失败，请确保环境已配置：{e}")
    ocr_engine = None

BOX_WIDTH = 5
HIGHLIGHT_COLOR = (255, 255, 0, 100)
KEY_BOX_COLOR = "blue"

# --- 2. 辅助工具函数 ---

FIELD_VALIDATORS = {
    "邮件": lambda v: bool(re.search(r'[\w\.-]+@[\w\.-]+\.\w+', v)),
    "邮箱": lambda v: bool(re.search(r'[\w\.-]+@[\w\.-]+\.\w+', v)),
    "电话": lambda v: bool(re.search(r'1[3-9]\d{9}', v)),
    "姓名": lambda v: 2 <= len(v) <= 10 and not any(c.isdigit() for c in v),
    "学历": lambda v: any(edu in v for edu in ["本科", "硕士", "博士", "专科", "高中"]),
    "工作年限": lambda v: bool(re.search(r'\d+年', v)),
    "专业": lambda v: len(v) <= 20 and "工程师" not in v and "公司" not in v,
}


def _validate_field_value(field_name: str, value: str) -> bool:
    fn = FIELD_VALIDATORS.get(field_name)
    return fn(value) if fn else True


def _get_bounding_box_from_8_points(
        box_8_points: List[Tuple[float, float]]
) -> List[int]:
    xs = [p[0] for p in box_8_points]
    ys = [p[1] for p in box_8_points]
    return [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))]


def _find_best_ocr_match(target_text: str, ocr_results: List[Tuple[List[Tuple[float, float]], Tuple[str, float]]], min_match_score: float = 0.3):
    """
    在OCR结果中查找与目标文本最匹配的框
    """
    best_ocr_box = None
    best_match_score = 0.0
    matched_ocr_text = ""

    for box8, (txt, conf) in ocr_results:
        clean_ocr_txt = txt.strip()
        clean_target = target_text.strip()

        # 检查目标文本是否是OCR框文本的一部分
        if clean_target in clean_ocr_txt:
            # 计算匹配分数 (目标文本长度 / OCR 文本长度)
            score = len(clean_target) / len(clean_ocr_txt)
            if score > best_match_score and score >= min_match_score:
                best_match_score = score
                best_ocr_box = _get_bounding_box_from_8_points(box8)
                matched_ocr_text = clean_ocr_txt
        # 检查OCR框文本是否是目标文本的一部分
        elif clean_ocr_txt in clean_target:
            # 计算匹配分数 (OCR 文本长度 / 目标文本长度)
            score = len(clean_ocr_txt) / len(clean_target)
            if score > best_match_score and score >= min_match_score:
                best_match_score = score
                best_ocr_box = _get_bounding_box_from_8_points(box8)
                matched_ocr_text = clean_ocr_txt

    return best_ocr_box, best_match_score, matched_ocr_text


def _finalize_extraction_and_refine_boxes(
        vlm_results: List[Dict],
        ocr_results: List[Tuple[List[Tuple[float, float]], Tuple[str, float]]]
) -> List[Dict]:
    """
    使用 OCR 结果精修 VLM 提取的 Key 和 Value 的坐标
    """
    validated: List[Dict] = []

    for res in vlm_results:
        field = res.get('field_name', '未知')
        val_text = res.get('extracted_text', '').strip()
        key_text = res.get('key_text', '').strip() if 'key_text' in res else field
        vlm_key_box = res.get('key_box')
        vlm_value_box = res.get('value_box')

        if not val_text:
            continue

        # 1. 使用 OCR 精确定位 Value 的坐标
        final_value_box, value_match_score, matched_value_text = _find_best_ocr_match(val_text, ocr_results, 0.3)

        # 2. 使用 OCR 精确定位 Key 的坐标
        final_key_box, key_match_score, matched_key_text = _find_best_ocr_match(key_text, ocr_results, 0.3)

        # 3. 如果 OCR 找到了匹配的框，则使用它们
        if final_value_box:
            final_extracted_text = matched_value_text
            confidence = 0.9 * value_match_score  # 基于匹配度计算置信度
            status = 'OCR_Refined'
        else:
            # 如果 OCR 没有找到匹配框，说明 VLM 的文本可能不准确
            print(f"   -> [警告] 无法为字段 '{field}' (VLM 提取: '{val_text}') 找到对应的 OCR 框，丢弃。")
            continue

        if not final_key_box:
            # 如果 Key 框没找到，使用 VLM 的原始框
            final_key_box = vlm_key_box
            if final_key_box:
                print(f"   -> [注意] 字段 '{field}' 的 Key 框使用 VLM 原始坐标。")
            else:
                print(f"   -> [警告] 字段 '{field}' 的 Key 框也未找到，丢弃。")
                continue

        # 4. 语义验证
        passed_semantic = _validate_field_value(field, final_extracted_text)
        if not passed_semantic:
            confidence *= 0.7  # 语义验证失败，降低置信度
            status += '_Semantic_Fail'

        # 5. 添加到最终结果
        validated.append({
            'field_name': field,
            'extracted_text': final_extracted_text,
            'key_text': matched_key_text if final_key_box else key_text,
            'key_box': final_key_box,
            'value_box': final_value_box,
            'confidence': round(confidence, 3),
            'status': status
        })

    return validated


# --- 3. 核心流程函数 ---

def pdf_to_image(pdf_path, dpi=300):
    doc = fitz.open(pdf_path)
    images = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix)
        img_data = pix.tobytes("ppm")
        image = Image.open(io.BytesIO(img_data))
        images.append(image)
    return images


def run_paddle_ocr(image):
    if ocr_engine is None:
        return []

    img_array = np.array(image.convert('RGB'))
    result = ocr_engine.ocr(img_array, cls=True)

    if result and result[0]:
        return result[0]
    return []


def extract_fields_with_ocr(
        ocr_results: List[Tuple[List[Tuple[float, float]], Tuple[str, float]]],
        target_fields: List[str]
) -> List[Dict]:
    """
    基于OCR结果直接提取目标字段
    """
    extracted_data = []
    
    # 遍历OCR结果，查找目标字段
    for i, (box8, (text, conf)) in enumerate(ocr_results):
        text_lower = text.lower()
        
        for field in target_fields:
            # 检查字段名是否在文本中
            if field.lower() in text_lower:
                # 找到字段名，提取其后的值
                key_box = _get_bounding_box_from_8_points(box8)
                
                # 寻找值：字段名后的文本
                parts = re.split(r'[:：]', text)
                if len(parts) > 1:
                    value_text = parts[1].strip()
                    # 查找值的OCR框
                    value_box = key_box  # 默认使用字段名的框
                    
                    # 尝试在后续OCR结果中找到值的框
                    for j in range(i + 1, len(ocr_results)):
                        next_box8, (next_text, next_conf) = ocr_results[j]
                        if value_text in next_text:
                            value_box = _get_bounding_box_from_8_points(next_box8)
                            break
                else:
                    # 如果没有冒号分隔，尝试在相邻OCR框中找值
                    value_text = ""
                    value_box = key_box
                    
                    # 检查下一个OCR框是否包含值
                    if i + 1 < len(ocr_results):
                        next_box8, (next_text, next_conf) = ocr_results[i + 1]
                        next_bbox = _get_bounding_box_from_8_points(next_box8)
                        
                        # 检查是否在右侧相邻
                        x1, y1, x2, y2 = key_box
                        nx1, ny1, nx2, ny2 = next_bbox
                        
                        # 简单的相邻判断：Y轴重叠且X轴紧邻
                        y_overlap = min(y2, ny2) - max(y1, ny1)
                        height = y2 - y1
                        if (nx1 > x2 and nx1 - x2 < height * 2) and (y_overlap / height > 0.5):
                            value_text = next_text.strip()
                            value_box = next_bbox
                        else:
                            # 如果不在右侧，尝试在字段名文本中查找值
                            remaining_text = text[len(field):].strip()
                            if remaining_text.startswith(':') or remaining_text.startswith('：'):
                                remaining_text = remaining_text[1:].strip()
                            if remaining_text:
                                value_text = remaining_text
                                value_box = key_box
                    else:
                        # 如果没有下一个框，在字段名文本中查找值
                        remaining_text = text[len(field):].strip()
                        if remaining_text.startswith(':') or remaining_text.startswith('：'):
                            remaining_text = remaining_text[1:].strip()
                        if remaining_text:
                            value_text = remaining_text
                            value_box = key_box
                
                if value_text:
                    extracted_data.append({
                        'field_name': field,
                        'key_text': field,
                        'extracted_text': value_text,
                        'key_box': key_box,
                        'value_box': value_box
                    })
    
    return extracted_data


def draw_box_on_image(image, box_data, draw_type="box"):
    """
    根据置信度同时绘制 Key 和 Value 的边界框/高亮，并解决标签重叠问题。
    """
    COLOR_GREEN = "green"
    COLOR_ORANGE = "orange"
    COLOR_RED = "red"
    KEY_BOX_OUTLINE_COLOR = "blue"

    if draw_type == "highlight" and image.mode != 'RGBA':
        image = image.convert('RGBA')

    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()

    for item in box_data:
        key_box = item.get('key_box')
        value_box = item.get('value_box')
        conf = item.get('confidence', 0.5)

        if not key_box or len(key_box) != 4 or not value_box or len(value_box) != 4:
            print(f"警告：跳过绘制无效的框数据: {item}")
            continue

        if conf >= 0.85:
            col = COLOR_GREEN
        elif conf >= 0.6:
            col = COLOR_ORANGE
        else:
            col = COLOR_RED

        kx0, ky0, kx1, ky1 = map(int, key_box)
        vx0, vy0, vx1, vy1 = map(int, value_box)
        label = f"{item['field_name']}({conf:.2f})"

        if draw_type == "box":
            draw.rectangle([kx0, ky0, kx1, ky1], outline=KEY_BOX_OUTLINE_COLOR, width=BOX_WIDTH // 2)
            draw.rectangle([vx0, vy0, vx1, vy1], outline=col, width=BOX_WIDTH)

            label_x = vx0
            label_y = min(ky0, vy0) - 20

            if label_x < 50:
                label_x = kx1 + 5

            draw.text((label_x, label_y), label, fill=col, font=font)

        elif draw_type == "highlight":
            mb = [min(kx0, vx0), min(ky0, vy0), max(kx1, vx1), max(ky1, vy1)]

            overlay = Image.new('RGBA', image.size, (255, 255, 255, 0))
            draw_overlay = ImageDraw.Draw(overlay)
            draw_overlay.rectangle(mb, fill=HIGHLIGHT_COLOR)
            image = Image.alpha_composite(image, overlay)

            draw = ImageDraw.Draw(image)

            label_x = max(kx1, vx1) + 5
            label_y = min(ky0, vy0) - 5

            if label_x > image.width - 150:
                label_x = min(kx0, vx0)
                label_y = min(ky0, vy0) - 20

            draw.text((label_x, label_y), label, fill=col, font=font)

    return image


def images_to_pdf(images, output_path):
    if not images:
        print("没有图像可以合并。")
        return

    rgb_images = [img.convert('RGB') for img in images]

    rgb_images[0].save(
        output_path,
        save_all=True,
        append_images=rgb_images[1:],
        resolution=300
    )
    print(f"成功创建画框后的PDF文件: {output_path}")


# --- 4. 主服务函数 ---

def process_pdf_and_draw_boxes(pdf_path, target_fields, output_path, draw_type="box"):
    print(f"1. 开始处理 PDF: {pdf_path}")
    page_images = pdf_to_image(pdf_path)
    processed_images = []

    for i, image in enumerate(page_images):
        print(f"\n--- 处理第 {i + 1} / {len(page_images)} 页 ---")

        # 1. OCR 识别
        ocr_results = run_paddle_ocr(image)
        print(f"   -> OCR 识别到 {len(ocr_results)} 个文本框")

        # 2. 直接使用OCR提取目标字段
        extracted_fields = extract_fields_with_ocr(ocr_results, target_fields)
        print(f"   -> OCR 提取到 {len(extracted_fields)} 个字段")

        # 3. 对提取结果进行验证和精修
        validated_boxes = _finalize_extraction_and_refine_boxes(extracted_fields, ocr_results)
        print(f"   -> 验证后保留 {len(validated_boxes)} 个字段")

        # 4. 确保最终结果中没有重复字段
        unique_results = {}
        for box in validated_boxes:
            field = box['field_name']
            if field not in unique_results or box['confidence'] > unique_results[field]['confidence']:
                unique_results[field] = box

        final_validated_boxes = list(unique_results.values())
        print(f"   -> 页面 {i + 1} 最终确认 {len(final_validated_boxes)} 个 Key/Value 对，并准备画框。")

        # 在图片上绘制双框/合并高亮
        final_image = draw_box_on_image(image, final_validated_boxes, draw_type=draw_type)
        processed_images.append(final_image)

    images_to_pdf(processed_images, output_path)
    print("\n服务运行完成。")


# --- 5. 示例调用 ---

if __name__ == '__main__':
    # !!! 确保此文件存在于您的运行目录 !!!
    INPUT_PDF = "example.pdf"
    OUTPUT_PDF = "result_ocr_based.pdf"

    FIELDS_TO_EXTRACT = ["姓名", "邮件", "电话", "学历", "专业", "毕业学校", "工作年限", "工作性质", "目标职能", "邮箱"]

    DRAW_MODE = "box"

    print("--- 启动 OCR 基础 PDF 简历字段标注服务 ---")

    process_pdf_and_draw_boxes(INPUT_PDF, FIELDS_TO_EXTRACT, OUTPUT_PDF, DRAW_MODE)