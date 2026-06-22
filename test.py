import os

# pdf_path = "C:/Users/jiaojiao/Desktop/test.pdf"
#
# print(os.path.basename(pdf_path))
import os
import json

DATA_DIR = r"E:\大模型学习记录\微调\苏格拉底\SocraticMath-main\SocraticMath-main\data"

def convert_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        raw = f.read().strip()
        if not raw:
            print(f"跳过空文件：{os.path.basename(file_path)}")
            return

    # 分支1：文件是顶层数组 [{},{}]
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            # 写入标准jsonl，覆盖原文件
            with open(file_path, "w", encoding="utf-8") as fw:
                for item in data:
                    fw.write(json.dumps(item, ensure_ascii=False) + "\n")
            print(f"【已转换】{os.path.basename(file_path)} 样本数：{len(data)}")
            return
        else:
            # 顶层是单个字典，直接转一行
            with open(file_path, "w", encoding="utf-8") as fw:
                fw.write(json.dumps(data, ensure_ascii=False) + "\n")
            print(f"【已转换】{os.path.basename(file_path)} 单条字典")
            return
    except json.JSONDecodeError as e:
        # 分支2：报Extra data = 已经是标准jsonl，无需处理
        if "Extra data" in str(e):
            print(f"【跳过】{os.path.basename(file_path)} 已是标准jsonl格式")
            return
        # 其他JSON语法错误，抛出提示
        else:
            print(f"【格式损坏】{os.path.basename(file_path)} JSON解析失败：{e}")
            return

if __name__ == "__main__":
    for fname in os.listdir(DATA_DIR):
        if fname.lower().endswith(".jsonl"):
            full_p = os.path.join(DATA_DIR, fname)
            convert_file(full_p)
    print("\n==== 全部处理完成 ====")