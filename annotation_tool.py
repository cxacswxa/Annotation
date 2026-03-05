import streamlit as st
import pandas as pd
import re
import base64
import mammoth

# streamlit run annotation_tool.py


st.set_page_config(page_title="教学活动标注工具V8", layout="wide")
st.title("📹 教学活动标注工具 (V8: 含教学结构版)")
def read_docx_content(file):
    """使用 mammoth 将 docx 转换为 html，并强制应用高对比度 + 内部滚动样式"""
    try:
        result = mammoth.convert_to_html(file)
        html = result.value

        style = """
        <style>
            /* 1. 外层容器：固定高度，内部滚动 */
            .docx-preview {
                background-color: #ffffff !important;
                color: #000000 !important;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                height: 800px;       /* 固定高度 */
                overflow-y: auto;    /* 垂直方向自动出现滚动条 */
                display: block;      
                border: 1px solid #ddd;
            }
            /* 2. 表格样式 */
            .docx-preview table { border-collapse: collapse; width: 100%; margin-bottom: 20px; background-color: #ffffff !important; color: #000000 !important; }
            .docx-preview td, .docx-preview th { border: 1px solid #444444 !important; padding: 10px; text-align: left; color: #000000 !important; }
            .docx-preview th { background-color: #e0e0e0 !important; font-weight: bold; position: sticky; top: 0; }
            /* 3. 斑马纹 */
            .docx-preview tr:nth-child(even) { background-color: #f9f9f9 !important; }
            .docx-preview tr:nth-child(odd) { background-color: #ffffff !important; }
            /* 4. 文字样式 */
            .docx-preview p { margin-bottom: 12px; line-height: 1.6; color: #000000 !important; }
            .docx-preview h1, .docx-preview h2, .docx-preview h3 { color: #000000 !important; border-bottom: 1px solid #eee; padding-bottom: 5px; }
        </style>
        """
        return f"{style}<div class='docx-preview'>{html}</div>"
    except Exception as e:
        return f"⚠️ Word 解析失败: {e}"


# --- 辅助函数：通用文件预览 ---
def display_file_preview(uploaded_file):
    if uploaded_file is None:
        st.info("👈 请在左侧侧边栏上传文件")
        return

    file_type = uploaded_file.type
    file_name = uploaded_file.name.lower()

    if "image" in file_type:
        st.markdown(
            f"""<div style="height: 800px; overflow-y: auto; border: 1px solid #ddd; padding: 10px;">
                <img src="data:{file_type};base64,{base64.b64encode(uploaded_file.getvalue()).decode()}" style="width: 100%;">
            </div>""",
            unsafe_allow_html=True
        )
    elif "pdf" in file_type:
        base64_pdf = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    elif "word" in file_type or file_name.endswith(".docx"):
        st.markdown("### 📄 文档预览 (Word)")
        uploaded_file.seek(0)
        html_content = read_docx_content(uploaded_file)
        st.markdown(html_content, unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ 暂不支持直接预览此格式: {file_type}")


# --- 辅助函数：智能序号 ---
def get_next_activity_index(df):
    if df.empty:
        return 1
    try:
        ids = df['编号'].astype(str).tolist()
        max_idx = 0
        for i in ids:
            nums = re.findall(r'\d+', i)
            if nums:
                curr = int(nums[0])
                if curr > max_idx:
                    max_idx = curr
        return max_idx + 1
    except:
        return 1


# --- 初始化 (增加 '教学结构' 列) ---
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=[
        '编号', '开始时间', '结束时间', '活动类型', '教学结构', '核心任务或目标', '证据说明', '备注'
    ])

# =======================
# 1. 侧边栏
# =======================
with st.sidebar:
    st.header("📂 1. 素材导入")
    video_file = st.file_uploader("1️⃣ 上传教学视频", type=['mp4', 'mov', 'avi'])
    st.markdown("---")
    design_file = st.file_uploader("2️⃣ 上传教学设计 (AP)", type=['pdf', 'docx', 'png', 'jpg'])
    task_file = st.file_uploader("3️⃣ 上传学习任务单 (AT)", type=['pdf', 'docx', 'png', 'jpg'])

    st.header("💾 2. 数据管理")
    uploaded_csv = st.file_uploader("导入已有标注表", type=['csv', 'xlsx'])
    if uploaded_csv:
        if st.button("加载数据"):
            try:
                if uploaded_csv.name.endswith('.csv'):
                    df_load = pd.read_csv(uploaded_csv)
                else:
                    df_load = pd.read_excel(uploaded_csv)

                # 兼容性处理：如果旧表没有'教学结构'列，补上
                if '教学结构' not in df_load.columns:
                    # 插入到'活动类型'后面
                    col_idx = df_load.columns.get_loc('活动类型') + 1 if '活动类型' in df_load.columns else 3
                    df_load.insert(col_idx, '教学结构', '')

                st.session_state.data = df_load
                st.success("加载成功！")
                st.rerun()
            except Exception as e:
                st.error(f"加载失败: {e}")

    st.markdown("---")
    csv_buffer = st.session_state.data.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 下载最终标注表 (CSV)",
        data=csv_buffer,
        file_name="教学活动标注结果_V8.csv",
        mime="text/csv"
    )

# =======================
# 2. 主界面
# =======================
col_materials, col_form = st.columns([1.5, 1])

with col_materials:
    tab1, tab2, tab3 = st.tabs(["📺 教学视频", "📘 教学设计 (AP)", "📄 学习任务单 (AT)"])

    with tab1:
        if video_file is not None:
            st.markdown(
                '<div style="position: sticky; top: 0; z-index: 100; background: white; padding-bottom: 10px;">',
                unsafe_allow_html=True)
            st.video(video_file)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("👈 请在左侧上传视频")

    with tab2:
        display_file_preview(design_file)

    with tab3:
        display_file_preview(task_file)

    st.markdown("---")
    st.markdown("### 📊 已标注数据预览")
    st.dataframe(st.session_state.data, use_container_width=True, height=300)

    if st.button("🛑 撤销上一次提交"):
        if not st.session_state.data.empty:
            last_id_str = st.session_state.data.iloc[-1]['编号']
            last_nums = re.findall(r'\d+', str(last_id_str))
            if last_nums:
                target_idx = last_nums[0]
                mask = st.session_state.data['编号'].apply(lambda x: target_idx not in re.findall(r'\d+', str(x)))
                st.session_state.data = st.session_state.data[mask]
                st.rerun()

with col_form:
    st.subheader("📝 标注操作区 (V8)")

    with st.form("annotation_form", clear_on_submit=False):

        current_act_idx = get_next_activity_index(st.session_state.data)
        st.markdown(f"**🔥 当前活动序号：{current_act_idx}**")

        c1, c2 = st.columns(2)
        with c1:
            start_time = st.text_input("开始时间", value="00:00:00", key="start_t")
        with c2:
            end_time = st.text_input("结束时间", value="00:00:00", key="end_t")

        st.markdown("---")

        # --- 活动类型 ---
        st.markdown("**1. 活动类型**")
        activity_type = st.radio(
            "选择阶段",
            options=["导入", "新知学习", "评价", "总结迁移", "其他"],
            index=1,
            horizontal=True,
            key="act_type"
        )

        st.markdown("---")

        # --- 新增：教学结构 ---
        st.markdown("**2. 教学结构 (四选一)**")
        # 使用 columns 稍微优化布局，或者直接用 radio
        structure_type = st.radio(
            "选择师生主导权结构",
            options=["H", "L", "L+H", "H+L"],
            captions=[
                "H: 教师指导为主 (高结构)",
                "L: 学生活动为主 (低结构)",
                "L+H: 学生活动为主，教师指导为辅",
                "H+L: 教师指导为主，学生活动为辅"
            ],
            index=0,
            horizontal=True,  # 横向排列更省空间
            key="struct_type"
        )

        st.markdown("---")

        task_desc = st.text_area("3. 核心任务/目标", height=80, placeholder="描述核心教学目标...", key="task_desc")

        st.markdown("---")

        st.markdown("**4. 证据来源 & 具体内容**")

        # AV
        c_av_check, c_av_text = st.columns([0.2, 0.8])
        with c_av_check:
            check_av = st.checkbox("AV", value=True, help="视频")
        with c_av_text:
            text_av = st.text_input("视频依据", placeholder="如：屏幕出现'练习'", label_visibility="collapsed")

        # AR
        c_ar_check, c_ar_text = st.columns([0.2, 0.8])
        with c_ar_check:
            check_ar = st.checkbox("AR", value=True, help="实录")
        with c_ar_text:
            text_ar = st.text_input("实录依据", placeholder="如：老师说'开始'", label_visibility="collapsed")

        # AP
        c_ap_check, c_ap_text = st.columns([0.2, 0.8])
        with c_ap_check:
            check_ap = st.checkbox("AP", help="教案")
        with c_ap_text:
            text_ap = st.text_input("教案依据", placeholder="如：环节一", label_visibility="collapsed")

        # AT
        c_at_check, c_at_text = st.columns([0.2, 0.8])
        with c_at_check:
            check_at = st.checkbox("AT", help="任务单")
        with c_at_text:
            text_at = st.text_input("任务单依据", placeholder="如：Task 1", label_visibility="collapsed")

        st.markdown("---")
        notes = st.text_input("备注", placeholder="选填：规则或分工", key="notes")

        submitted = st.form_submit_button("✅ 确认提交", type="primary")

        if submitted:
            new_rows = []
            sources = [
                ('AV', check_av, text_av, '视频画面记录'),
                ('AR', check_ar, text_ar, '课堂实录文本'),
                ('AP', check_ap, text_ap, '教学设计对应环节'),
                ('AT', check_at, text_at, '学习任务单任务')
            ]

            has_selection = False
            for prefix, is_checked, user_text, default_text in sources:
                if is_checked:
                    has_selection = True
                    final_evidence = user_text if user_text.strip() else default_text
                    row_id = f"{prefix}{current_act_idx}"

                    row = {
                        '编号': row_id,
                        '开始时间': start_time,
                        '结束时间': end_time,
                        '活动类型': activity_type,
                        '教学结构': structure_type,  # 写入新增字段
                        '核心任务或目标': task_desc,
                        '证据说明': final_evidence,
                        '备注': notes
                    }
                    new_rows.append(row)

            if not has_selection:
                st.error("请至少勾选一个证据来源！")
            else:
                st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame(new_rows)], ignore_index=True)
                st.rerun()
# 将以下代码添加到 annotation_tool.py 的最末尾


