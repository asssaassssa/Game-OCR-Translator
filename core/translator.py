import csv
import os
from config.settings import DICT_PATH

class LocalDictionary:
    def __init__(self):
        self.data = {}
        self.load_data()

    def load_data(self):
        if not os.path.exists(DICT_PATH):
            print(f"⚠️ [Dict] 未找到词典: {DICT_PATH}")
            return
        
        try:
            with open(DICT_PATH, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                if reader.fieldnames:
                    for row in reader:
                        word = row.get('word') or row.get('sw')
                        trans = row.get('translation') or row.get('definition')
                        if word and trans:
                            self.data[word.strip().lower()] = trans.replace('\\n', '; ')
                            count += 1
            print(f"✅ [Dict] 词典加载完成: {count} 条")
        except Exception as e:
            print(f"❌ [Dict] 加载失败: {e}")

    def query(self, word):
        """查询单词，包含简单的词形还原"""
        w = word.lower()
        if w in self.data: return self.data[w]
        # 简单的复数处理
        if w.endswith('s') and w[:-1] in self.data: return self.data[w[:-1]]
        if w.endswith('es') and w[:-2] in self.data: return self.data[w[:-2]]
        return None

    def format_definition(self, definition):
        """格式���释义用于显示"""
        formatted = definition.replace('\\n', '\n').replace('；', '\n')
        lines = formatted.split('\n')
        if len(lines) > 6:
            formatted = '\n'.join(lines[:6]) + "\n..."
        return formatted