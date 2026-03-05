import streamlit as st
import pandas as pd
import re
import base64
import mammoth

# --- 页面配置 ---
st.set_page_config(page_title="标注流水线-环节2：教案对齐", layout="wide")
st.title("🏭 教学标注流水线 - 步骤2：教案与任务对齐")
st.markdown("ℹ️ **使用说明：** 导入步骤1生成的表格，选择特定活动，补充 AP(教案) 和 AT(任务单) 证据。")


# --- 辅助函数：Word 转 HTML (带滚动条) ---
def read_docx_content(file):
    try:
        result = mammoth.convert_to_html(file)
        html = result.value
        style = """
        <style>
            .docx-preview {
                background-color: #ffffff !important; color: #000000 !important;
                padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                height: 700px; overflow-y: auto; display: block; border: 1px solid #ddd;
            }
            .docx-preview table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
            .docx-preview td, .docx-preview th { border: 1px solid #444444 !important; padding: 10px; color: #000000 !important; }
            .docx-preview tr:nth-child(even) { background-color: #f9f9f9 !important; }
            .docx-preview p { margin-bottom: 10px; color: #000000 !important; }
        </style>
        """
        return f"{style}<div class='docx-preview'>{html}</div>"
    except Exception as e:
        return f"⚠️ Word 解析失败: {e}"


# --- 辅助函数：通用预览 ---
def display_file_preview(uploaded_file):
    if uploaded_file is None:
        st.info("👈 请在左侧上传文档")
        return
    file_type = uploaded_file.type
    if "pdf" in file_type:
        base64_pdf = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
        st.markdown(f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="700"></iframe>',
                    unsafe_allow_html=True)
    elif "word" in file_type or uploaded_file.name.endswith(".docx"):
        st.markdown(read_docx_content(uploaded_file), unsafe_allow_html=True)
    elif "image" in file_type:
        st.image(uploaded_file, use_column_width=True)
    else:
        st.warning("不支持的预览格式")


# --- 辅助函数：提取活动序号列表 ---
def get_activity_indices(df):
    if df.empty: return []
    indices = set()
    for id_str in df['编号'].astype(str):
        nums = re.findall(r'\d+', id_str)
        if nums: indices.add(int(nums[0]))
    return sorted(list(indices))


# --- 初始化 ---
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(
        columns=['编号', '开始时间', '结束时间', '活动类型', '核心任务或目标', '证据说明', '备注'])

# =======================
# 1. 侧边栏：只关注文档和表格导入
# =======================
with st.sidebar:
    st.header("📂 1. 导入工作流")

    uploaded_csv = st.file_uploader("1️⃣ 导入步骤1的标注表 (CSV/Excel)", type=['csv', 'xlsx'])
    if uploaded_csv:
        if st.button("📥 加载/刷新表格"):
            try:
                if uploaded_csv.name.endswith('.csv'):
                    st.session_state.data = pd.read_csv(uploaded_csv)
                else:
                    st.session_state.data = pd.read_excel(uploaded_csv)
                st.success("表格加载成功！")
                st.rerun()
            except Exception as e:
                st.error(f"加载失败: {e}")

    st.markdown("---")
    design_file = st.file_uploader("2️⃣ 教学设计 (AP)", type=['pdf', 'docx', 'png'])
    task_file = st.file_uploader("3️⃣ 学习任务单 (AT)", type=['pdf', 'docx', 'png'])

    st.markdown("---")
    # 导出时进行排序，确保 AP/AT 紧跟在 AV/AR 后面
    if not st.session_state.data.empty:
        # 创建一个临时排序列
        export_df = st.session_state.data.copy()
        # 提取数字用于排序
        export_df['_sort_id'] = export_df['编号'].apply(
            lambda x: int(re.findall(r'\d+', str(x))[0]) if re.findall(r'\d+', str(x)) else 9999)
        # 提取前缀用于排序 (AV < AR < AP < AT)
        priority_map = {'AV': 1, 'AR': 2, 'AP': 3, 'AT': 4}
        export_df['_sort_type'] = export_df['编号'].apply(
            lambda x: priority_map.get(re.findall(r'[A-Z]+', str(x))[0], 9) if re.findall(r'[A-Z]+', str(x)) else 9)

        export_df = export_df.sort_values(by=['_sort_id', '_sort_type']).drop(columns=['_sort_id', '_sort_type'])

        csv_buffer = export_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="💾 导出合并后的表格 (CSV)",
            data=csv_buffer,
            file_name="教学活动标注_合并版.csv",
            mime="text/csv"
        )

# =======================
# 2. 主界面
# =======================
col_docs, col_edit = st.columns([1.5, 1])

# --- 左侧：文档对照区 ---
with col_docs:
    tab1, tab2 = st.tabs(["📘 教学设计 (AP)", "📄 学习任务单 (AT)"])
    with tab1:
        display_file_preview(design_file)
    with tab2:
        display_file_preview(task_file)

    st.markdown("---")
    st.markdown("### 📊 全局数据预览")
    # 支持直接在表格里修改（比如改错别字）
    edited_df = st.data_editor(st.session_state.data, use_container_width=True, height=300, num_rows="dynamic")
    # 如果用户在表格控件里直接改了数据，同步回 session
    if not edited_df.equals(st.session_state.data):
        st.session_state.data = edited_df
        st.rerun()

# --- 右侧：补充标注操作区 ---
with col_edit:
    st.subheader("🛠️ 活动补充工作台")

    # 获取所有活动序号
    act_indices = get_activity_indices(st.session_state.data)

    if not act_indices:
        st.info("请先导入包含数据的表格。")
    else:
        # 1. 选择要处理的活动
        selected_idx = st.selectbox("🎯 选择要补充的活动序号", act_indices)

        # 2. 自动获取该活动的已知信息 (从 AV 或 AR 行)
        current_rows = st.session_state.data[st.session_state.data['编号'].str.contains(f"{selected_idx}")]

        if not current_rows.empty:
            # 尝试提取这一组活动已经填好的共性信息
            ref_row = current_rows.iloc[0]
            ref_start = ref_row.get('开始时间', '')
            ref_end = ref_row.get('结束时间', '')
            ref_type = ref_row.get('活动类型', '')
            ref_task = ref_row.get('核心任务或目标', '')
            ref_notes = ref_row.get('备注', '')

            st.info(f"**活动 {selected_idx} 信息概览**：\n\n🕒 {ref_start}-{ref_end} | 🏷️ {ref_type}\n\n📝 {ref_task}")

            # 检查是否已经存在 AP 或 AT
            has_ap = any(f"AP{selected_idx}" in str(x) for x in current_rows['编号'])
            has_at = any(f"AT{selected_idx}" in str(x) for x in current_rows['编号'])

            if has_ap: st.success(f"✅ AP{selected_idx} 已存在")
            if has_at: st.success(f"✅ AT{selected_idx} 已存在")

            st.markdown("---")

            with st.form("supplement_form"):
                st.markdown("**补充/覆盖证据信息：**")

                # AP 部分
                c1, c2 = st.columns([0.3, 0.7])
                with c1:
                    do_ap = st.checkbox("补充 AP", value=not has_ap)  # 如果没存，默认勾选
                with c2:
                    txt_ap = st.text_input("AP 依据 (教案环节)", placeholder="如：环节一：导入")

                # AT 部分
                c3, c4 = st.columns([0.3, 0.7])
                with c3:
                    do_at = st.checkbox("补充 AT", value=not has_at)
                with c4:
                    txt_at = st.text_input("AT 依据 (任务单Task)", placeholder="如：Task 1")

                # 允许修改共性信息（可选）
                with st.expander("修改该活动的时间/类型/任务 (同步更新所有行)"):
                    new_start = st.text_input("开始时间", value=ref_start)
                    new_end = st.text_input("结束时间", value=ref_end)
                    new_type = st.text_input("活动类型", value=ref_type)
                    new_task = st.text_area("核心任务", value=ref_task)
                    new_notes = st.text_input("备注", value=ref_notes)

                btn_save = st.form_submit_button("💾 保存/更新该活动", type="primary")

                if btn_save:
                    # 1. 先把内存中关于该活动的所有旧行拿出来，进行更新
                    # 这里的逻辑是：保留 AV/AR 行，更新它们的共性信息；新增/更新 AP/AT 行

                    # 查找已有的 AV/AR
                    av_row = current_rows[current_rows['编号'].str.contains('AV')].to_dict('records')
                    ar_row = current_rows[current_rows['编号'].str.contains('AR')].to_dict('records')

                    # 准备新的行列表
                    updated_rows_list = []

                    # 处理 AV (如果有，更新共性字段后保留)
                    if av_row:
                        r = av_row[0]
                        r.update({'开始时间': new_start, '结束时间': new_end, '活动类型': new_type,
                                  '核心任务或目标': new_task, '备注': new_notes})
                        updated_rows_list.append(r)

                    # 处理 AR (同上)
                    if ar_row:
                        r = ar_row[0]
                        r.update({'开始时间': new_start, '结束时间': new_end, '活动类型': new_type,
                                  '核心任务或目标': new_task, '备注': new_notes})
                        updated_rows_list.append(r)

                    # 处理 AP
                    if do_ap:
                        evidence = txt_ap if txt_ap else "教学设计对应环节"
                        updated_rows_list.append({
                            '编号': f"AP{selected_idx}",
                            '开始时间': new_start, '结束时间': new_end, '活动类型': new_type,
                            '核心任务或目标': new_task, '证据说明': evidence, '备注': new_notes
                        })

                    # 处理 AT
                    if do_at:
                        evidence = txt_at if txt_at else "学习任务单任务"
                        updated_rows_list.append({
                            '编号': f"AT{selected_idx}",
                            '开始时间': new_start, '结束时间': new_end, '活动类型': new_type,
                            '核心任务或目标': new_task, '证据说明': evidence, '备注': new_notes
                        })

                    # 2. 将 Session State 中该活动的旧数据全部删除
                    # 过滤掉编号中包含当前 Index 的行
                    df_rest = st.session_state.data[
                        ~st.session_state.data['编号'].str.contains(f"(?<!\d){selected_idx}(?!\d)", regex=True)]

                    # 3. 合并新行
                    st.session_state.data = pd.concat([df_rest, pd.DataFrame(updated_rows_list)], ignore_index=True)

                    st.success(f"活动 {selected_idx} 已更新！")
                    st.rerun()