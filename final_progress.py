import pandas as pd
import os


def process_behavior_files(input_dir='output_files', output_dir='final_files'):
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    # 检查输入目录是否存在
    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist.")
        return

    # 获取输入目录下的所有CSV文件
    files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]

    if not files:
        print(f"No CSV files found in {input_dir}")
        return

    for file_name in files:
        file_path = os.path.join(input_dir, file_name)

        try:
            # 读取CSV文件，尝试不同编码
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding='gbk')

            # 需要检查变化的列
            check_cols = ['主体', '客体（行为目的）', '工具', '共同体（互动范围）', '行为类型']

            # 填充空值以确保比较准确
            df_comp = df[check_cols].fillna("")

            new_ids = []
            current_num = 1
            prev_vals = None

            # 遍历每一行进行判断
            for index, row in df_comp.iterrows():
                curr_vals = tuple(row.values)  # 使用 tuple 方便比较

                if prev_vals is None:
                    # 第一行
                    prev_vals = curr_vals
                else:
                    # 比较当前行与上一行
                    if curr_vals != prev_vals:
                        current_num += 1
                        prev_vals = curr_vals

                # 格式化编号为 B1, B2, ...
                new_ids.append(f"B{current_num}")

            # 将新的行为编号赋值回原数据
            df['行为编号'] = new_ids

            # --- 修改开始：处理文件名逻辑 ---
            base_name, ext = os.path.splitext(file_name)

            if '_' in base_name:
                # 如果有下划线，取第一个下划线前的部分，加上"_行为标注"
                # split('_')[0] 获取前缀
                new_file_name = f"{base_name.split('_')[0]}_行为标注{ext}"
            else:
                # 如果没有下划线，保持原名
                new_file_name = file_name
            # --- 修改结束 ---

            # 保存结果到 final_files 文件夹，使用新文件名
            output_path = os.path.join(output_dir, new_file_name)
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            print(f"成功处理并保存: {output_path}")

        except Exception as e:
            print(f"处理文件 {file_name} 时出错: {e}")


# 执行主函数
if __name__ == "__main__":
    process_behavior_files()