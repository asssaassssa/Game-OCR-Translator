import os
import sys
import re

def setup_env():
    """初始化环境"""
    os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

def clean_word(word):
    """
    清洗单词：去除首尾的标点符号，但保留单词内部的连字符
    """
    # 移除首尾的常见标点
    return word.strip(" .,;:!?[]()\"'<>《》“”‘’/\\|`~")

def find_word_in_text(text, ratio_x):
    """
    高级光标定位算法：
    1. 支持按 . 和 _ 切分单词 (user.name -> user, name)
    2. 基于字符宽度的加权估算，解决 'i' 和 'W' 宽度不等导致的偏移问题
    
    Args:
        text: OCR 识别出的完整文本 (例如 "hello_world.py")
        ratio_x: 鼠标在文本框内的相对横坐标 (0.0 ~ 1.0)
    """
    if not text: return None
    
    # 1. 预处理：把下划线替换为空格，统一处理逻辑
    # 这样 "hello_world" 变成 "hello world"，方便后续切分
    processed_text = text.replace('_', ' ').replace('.', ' ')
    
    # 2. 构造 Token 列表 (记录每个单词在原句中的字符区间)
    # 我们不直接 split，而是用 finditer 保留位置信息
    tokens = []
    # 匹配所有连续的字母/数字部分
    for match in re.finditer(r'[a-zA-Z0-9\-\']+', processed_text):
        word = match.group()
        start = match.start()
        end = match.end()
        tokens.append({
            "word": word,
            "start": start,  # 字符起始索引
            "end": end,      # 字符结束索引
            "length": end - start
        })
    
    if not tokens: return None

    # 3. 估算每个字符的物理宽度 (核心优化)
    # 在变宽字体中，大写字母和宽字母(w, m)占位更多
    # 我们给每个字符赋予一个“权重”，用来计算它在屏幕上的大致宽度
    def get_char_weight(char):
        if char.isupper() or char in "wmWM@%":
            return 1.4  # 宽字符
        if char in "iljftI1.,!|":
            return 0.6  # 窄字符
        return 1.0      # 普通字符
    
    # 计算整个字符串的总权重 (模拟总像素宽度)
    total_weight = sum(get_char_weight(c) for c in text)
    if total_weight == 0: return None
    
    # 4. 计算鼠标指向的“权重位置”
    target_weight = ratio_x * total_weight
    
    # 5. 遍历 Token，看鼠标落在哪个 Token 的权重区间内
    current_weight = 0.0
    
    # 还要考虑 Token 之间的间隔 (比如空格、标点)，它们也占宽度
    # 我们通过遍历原文本的每个字符来累加权重
    
    # 优化：直接遍历原文本，找到 target_weight 对应的字符索引
    target_char_index = 0
    accumulated_weight = 0.0
    
    for i, char in enumerate(text):
        w = get_char_weight(char)
        if accumulated_weight + w >= target_weight:
            target_char_index = i
            break
        accumulated_weight += w
    else:
        # 如果循环结束还没到，说明在最后
        target_char_index = len(text) - 1

    # 6. 检查这个字符索引落在哪个 Token 里
    for token in tokens:
        # 稍微放宽边界 (Buffer)，防止鼠标刚好指在两个词中间的缝隙
        # 只要指在单词范围内，或者紧挨着单词末尾
        if token["start"] <= target_char_index < token["end"]:
            return clean_word(token["word"])
            
    # 7. 兜底策略：如果没落在任何 Token 上 (比如指着中间的空格或标点)
    # 找距离最近的 Token
    best_token = None
    min_dist = float('inf')
    
    for token in tokens:
        # 计算 Token 中心点
        token_center = (token["start"] + token["end"]) / 2
        dist = abs(token_center - target_char_index)
        if dist < min_dist:
            min_dist = dist
            best_token = token
            
    if best_token and min_dist < 5: # 只有距离足够近才返回
        return clean_word(best_token["word"])
        
    return None