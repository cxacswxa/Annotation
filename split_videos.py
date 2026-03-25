import os
import pandas as pd
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip


def time_to_seconds(time_val):
    """
    辅助函数：将多种格式的时间转换为秒数
    支持的格式: 'HH:MM:SS', 'MM:SS', 或者纯数字的秒数
    """
    time_str = str(time_val).strip()
    try:
        # 如果本身就是纯数字形式的秒数
        return float(time_str)
    except ValueError:
        pass

    # 如果是包含冒号的字符串形式 (如 00:01:30)
    parts = time_str.split(':')
    if len(parts) == 3:  # HH:MM:SS
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    elif len(parts) == 2:  # MM:SS
        return int(parts[0]) * 60 + float(parts[1])
    else:
        raise ValueError(f"无法识别的时间格式: {time_str}")


def split_videos_by_csv():
    # 1. 定义文件夹路径
    video_dir = 'video'
    csv_dir = 'csv'
    result_dir = 'result'

    # 如果 result 文件夹不存在，则创建它
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)

    # 获取 video 文件夹下的所有文件
    if not os.path.exists(video_dir) or not os.path.exists(csv_dir):
        print("错误: 当前目录下未找到 'video' 或 'csv' 文件夹，请检查目录结构。")
        return

    video_files = [f for f in os.listdir(video_dir) if os.path.isfile(os.path.join(video_dir, f))]

    # 2. 遍历视频文件进行匹配
    for video_filename in video_files:
        # 拆分文件名和后缀 (例如: 'lesson1', '.mp4')
        video_name, video_ext = os.path.splitext(video_filename)

        # 过滤掉隐藏文件等非视频文件
        if video_filename.startswith('.') or video_ext.lower() not in ['.mp4', '.avi', '.mov', '.mkv']:
            continue

        # 构造对应的 CSV 文件名
        csv_filename = f"{video_name}_教学活动标注.csv"
        csv_path = os.path.join(csv_dir, csv_filename)
        video_path = os.path.join(video_dir, video_filename)

        # 3. 检查 CSV 是否存在
        if os.path.exists(csv_path):
            print(f"\n匹配成功: [{video_filename}] <---> [{csv_filename}]")

            # 在 result 目录下创建以原视频名命名的子文件夹
            output_sub_dir = os.path.join(result_dir, video_name)
            if not os.path.exists(output_sub_dir):
                os.makedirs(output_sub_dir)

            # 4. 读取 CSV 文件并切割视频
            try:
                # 尝试用 utf-8-sig 读取（兼容带BOM或不带BOM的UTF-8），若失败可按需改为 'gbk'
                df = pd.read_csv(csv_path, encoding='utf-8-sig')

                for index, row in df.iterrows():
                    # 提取起始和结束时间 (请确保 CSV 的列名严格匹配如下字符串)
                    start_time_raw = row['开始时间']
                    end_time_raw = row['结束时间']

                    # 转换时间为秒 (供 moviepy 使用)
                    start_sec = time_to_seconds(start_time_raw)
                    end_sec = time_to_seconds(end_time_raw)

                    # 构造分视频的文件名
                    # 注意: Windows 文件名不支持冒号 ":"，所以我们将时间里的冒号替换为中划线 "-"
                    safe_start_str = str(start_time_raw).replace(':', '-')
                    clip_filename = f"{video_name}_{safe_start_str}{video_ext}"
                    clip_path = os.path.join(output_sub_dir, clip_filename)

                    print(f"  -> 正在提取片段: {clip_filename} ({start_time_raw} - {end_time_raw})")

                    # 5. 执行无损秒切视频
                    ffmpeg_extract_subclip(video_path, start_sec, end_sec, targetname=clip_path)

            except Exception as e:
                print(f"处理文件 {csv_filename} 时发生错误: {e}")
                print("提示: 请检查 CSV 文件的编码是否为 UTF-8，或者列名是否为完全匹配的 '开始时间' 和 '结束时间'。")
        else:
            print(f"\n未找到匹配文件: 视频 [{video_filename}] 没有对应的标注文件 [{csv_filename}]，已跳过。")

    print("\n所有任务处理完毕！请前往 result 文件夹查看结果。")


if __name__ == "__main__":
    split_videos_by_csv()