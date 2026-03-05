import pandas as pd
import os
import glob

# =================配置区域=================
INPUT_FOLDER = 'input_files'  # 把你的活动标注表(xlsx/csv)都放在这里
OUTPUT_FOLDER = 'output_files'  # 生成的结果会自动保存在这里


# =========================================

def time_str_to_seconds(time_str):
    """将时间字符串转换为秒"""
    try:
        time_str = str(time_str).strip()
        parts = list(map(int, time_str.split(':')))
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2:
            return parts[0] * 60 + parts[1]
    except:
        return 0
    return 0


def seconds_to_time_str(seconds):
    """将秒转换为时间字符串"""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "{:02d}:{:02d}:{:02d}".format(int(h), int(m), int(s))


def process_single_file(file_path, output_path):
    print(f"正在处理: {os.path.basename(file_path)}...")

    try:
        # === 改进点：自动尝试 header=1 和 header=0 ===
        df = None
        # 先尝试按“第二行是表头”读取（兼容旧模版）
        try:
            df_try = pd.read_excel(file_path, header=1) if not file_path.endswith('.csv') else pd.read_csv(file_path,
                                                                                                           header=1)
            # 检查关键列是否在
            if any('编号' in str(c) for c in df_try.columns):
                df = df_try
        except:
            pass

        # 如果没读对，尝试按“第一行是表头”读取
        if df is None:
            df_try = pd.read_excel(file_path, header=0) if not file_path.endswith('.csv') else pd.read_csv(file_path,
                                                                                                           header=0)
            if any('编号' in str(c) for c in df_try.columns):
                df = df_try

        # 如果还是空，说明真的找不到
        if df is None:
            print(f"⚠️ 跳过: {os.path.basename(file_path)} (不管读第1行还是第2行，都没找到'编号'列)")
            return
        # ==========================================

        # 清理列名空格
        df.columns = df.columns.astype(str).str.strip()
        id_col = next((c for c in df.columns if '编号' in c), None)
        start_col = next((c for c in df.columns if '开始' in c), None)
        end_col = next((c for c in df.columns if '结束' in c), None)
        type_col = next((c for c in df.columns if '活动类型' in c), None)

        if not (id_col and start_col and end_col):
            print(f"⚠️ 跳过: {os.path.basename(file_path)} (未找到关键列，请检查表头)")
            return

        # 3. 准备输出结构 (标准 V3 方案列名)
        output_columns = [
            '行为编号', '所属活动', '开始时间', '结束时间', '行为类型',
            '主体', '客体（行为目的）', '布鲁姆教育目标分类', '任务完成情况',
            '工具', '共同体（互动范围）', '证据来源', '备注'
        ]

        behavior_rows = []
        counter = 1

        # 4. 遍历每一行活动
        for index, row in df.iterrows():
            act_id = str(row[id_col])

            # 只处理 AV (视频) 片段
            if not act_id.startswith('AV'):
                continue

            start_sec = time_str_to_seconds(row[start_col])
            end_sec = time_str_to_seconds(row[end_col])

            if end_sec <= start_sec:
                continue

            # 按 3秒 切分
            current_sec = start_sec
            while current_sec < end_sec:
                slice_end = min(current_sec + 3, end_sec)

                new_row = {col: "" for col in output_columns}

                new_row['行为编号'] = f"B{counter}"
                new_row['所属活动'] = act_id
                new_row['开始时间'] = seconds_to_time_str(current_sec)
                new_row['结束时间'] = seconds_to_time_str(slice_end)
                new_row['证据来源'] = "V, R"

                # 将活动类型填入备注，辅助人工
                if type_col and not pd.isna(row[type_col]):
                    new_row['备注'] = f"[{row[type_col]}]"

                behavior_rows.append(new_row)
                counter += 1
                current_sec += 3

        # 5. 保存结果
        output_df = pd.DataFrame(behavior_rows, columns=output_columns)
        output_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"✅ 完成! 已保存至: {output_path}")

    except Exception as e:
        print(f"❌ 处理失败: {os.path.basename(file_path)} | 错误: {str(e)}")


def batch_process():
    # 创建输出目录
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    # 获取所有 xlsx 和 csv 文件
    all_files = glob.glob(os.path.join(INPUT_FOLDER, "*.xlsx")) + \
                glob.glob(os.path.join(INPUT_FOLDER, "*.csv"))

    if not all_files:
        print(f"在 '{INPUT_FOLDER}' 文件夹里没找到文件。请先放入数据！")
        return

    print(f"找到 {len(all_files)} 个文件，开始批处理...\n" + "-" * 30)

    for file_path in all_files:
        # 生成输出文件名： 原文件名_behavior.csv
        file_name = os.path.basename(file_path)
        name_without_ext = os.path.splitext(file_name)[0]
        output_name = f"{name_without_ext}_行为标注骨架.csv"
        output_path = os.path.join(OUTPUT_FOLDER, output_name)

        process_single_file(file_path, output_path)

    print("-" * 30 + "\n🎉 所有文件处理完毕！")


if __name__ == "__main__":
    batch_process()