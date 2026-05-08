import streamlit as st
import fitz  # PyMuPDF
import io
import pandas as pd

# 1. 设置网页标题
st.set_page_config(page_title="PDF 自动化提效平台", layout="wide")
st.title("🚀 全能 PDF 自动化提效平台")

tab1, tab2, tab3 = st.tabs(["🚀 封面交互补丁工具", "📑 智能目录 (TOC) 提取", "🔍 智能目录搜索DEMO"])

# ================= TAB 1: 封面排版与透明补丁 =================
with tab1:
    st.header("🎯 自动生成封面/目录热区跳转")
    uploaded_file = st.file_uploader("把设计部定稿的 report.pdf 拖进来", type="pdf", key="cover")
    
    if uploaded_file:
        st.markdown("---")
        # 将原有的侧边栏改为 Tab 内的双列排版，显得更专业干练
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📌 基础排版设置")
            page_mode = st.radio("PDF 页面布局", ["Single (单页)", "Spread (双页跨页)"])
            cols = st.number_input("每行几个按钮", value=10)
            start_y = st.slider("起始高度 (避开封面标题)", 100, 500, 200)
            
            st.subheader("⚙️ 高级特殊设定")
            prefix_names = st.text_input("前插特殊页名称 (用英文逗号隔开，按顺序避让正文)", value="Cover")
            fold_pages = st.text_input("折叠/展开页 (直接填入展开页所在的 PDF 物理页码如 8，也就是要重复编号的那一页，支持逗号隔开)", value="")
            
        with col2:
            st.subheader("📏 进阶尺寸微调")
            gap = st.number_input("按钮间距 Gap (越小按钮越宽)", value=5, min_value=0)
            margin = st.number_input("左右留白 Margin", value=40, min_value=0)
            btn_h = st.number_input("按钮高度", value=25, min_value=10)
            font_size = st.number_input("字体大小 (设为 0 可防截断)", value=11, min_value=0)
            zoom_mode = st.selectbox("跳转缩放级别 (Zoom Level)", ["Fit Page", "Fit Width", "Inherit Zoom", "100%", "125%", "150%", "200%"], index=0)
            
            st.subheader("✨ 隐形打底模式")
            show_label = st.checkbox("显示按钮文字 (当制作纯透明热区时，请取消勾选)", value=True)
            show_tooltip = st.checkbox("开启鼠标悬停提示词 (Tooltip)", value=False)
        
        st.markdown("---")
        
        if st.button("🔥 开始生成热区补丁", type="primary"):
            zoom_map = {
                "Fit Page": "/Fit",
                "Fit Width": "/FitH null",
                "Inherit Zoom": "/XYZ null null null",
                "100%": "/XYZ null null 1.0",
                "125%": "/XYZ null null 1.25",
                "150%": "/XYZ null null 1.5",
                "200%": "/XYZ null null 2.0"
            }
            selected_zoom = zoom_map[zoom_mode]
            
            prefix_list = [p.strip() for p in prefix_names.split(",") if p.strip()]
            offset_pages = len(prefix_list)
            fold_list = [int(x.strip()) - 1 for x in fold_pages.split(",") if x.strip().isdigit()]
            
            input_bytes = uploaded_file.read()
            doc = fitz.open(stream=input_bytes, filetype="pdf")
            total_pages = len(doc)
            
            cover = doc[0]
            w, h = cover.rect.width, cover.rect.height
            btn_w = (w - (2 * margin) - (cols - 1) * gap) / cols
            
            for i in range(total_pages):
                row = i // cols
                col = i % cols
                
                x0 = margin + (col * (btn_w + gap))
                y0 = start_y + (row * (btn_h + gap))
                rect = fitz.Rect(x0, y0, x0 + btn_w, y0 + btn_h)
                
                # 确定按钮文字（完美解决 Cover, I, II, III 前插页错位）
                if i < offset_pages:
                    btn_text = prefix_list[i]
                else:
                    rel_i = i - offset_pages
                    logical_i = rel_i - sum(1 for f_i in fold_list if i >= f_i)
                    if page_mode == "Spread (双页跨页)":
                        btn_text = f"P{logical_i*2}-{logical_i*2+1}"
                    else:
                        btn_text = f"P{logical_i+1}"
                
                target_page_xref = doc[i].xref
                
                widget = fitz.Widget()
                widget.rect = rect
                widget.field_type = fitz.PDF_WIDGET_TYPE_BUTTON
                widget.field_flags = fitz.PDF_BTN_FIELD_IS_PUSHBUTTON
                widget.field_name = btn_text
                
                if show_label:
                    widget.button_caption = btn_text
                else:
                    widget.button_caption = "" 
                
                if show_tooltip:
                    widget.field_label = btn_text
                    
                widget.text_fontsize = font_size
                widget.text_font = "HeBo"
                widget.text_color = (0, 0, 0)
                widget.fill_color = None
                widget.border_color = None
                
                annot = cover.add_widget(widget)
                doc.xref_set_key(annot.xref, "H", "/N")
                doc.xref_set_key(annot.xref, "A", f"<< /S /GoTo /D [{target_page_xref} 0 R {selected_zoom}] >>")

            # 增强功能：回首页按钮
            home_rect = fitz.Rect(w - 60, h - 40, w - 20, h - 20)
            for j in range(1, total_pages):
                widget_home = fitz.Widget()
                widget_home.rect = home_rect
                widget_home.field_type = fitz.PDF_WIDGET_TYPE_BUTTON
                widget_home.field_flags = fitz.PDF_BTN_FIELD_IS_PUSHBUTTON
                widget_home.field_name = "BACK"
                widget_home.button_caption = "BACK"
                
                widget_home.text_fontsize = 8
                widget_home.text_font = "HeBo"
                widget_home.text_color = (0, 0, 0)
                widget_home.fill_color = (0.9, 0.9, 0.9)
                widget_home.border_color = (0.6, 0.6, 0.6)
                
                annot_home = doc[j].add_widget(widget_home)
                doc.xref_set_key(annot_home.xref, "A", f"<< /S /GoTo /D [{doc[0].xref} 0 R {selected_zoom}] >>")

            output_stream = io.BytesIO()
            doc.save(output_stream)
            
            st.success(f"搞定！已成功注入热区交互，总共处理 {total_pages} 页。")
            st.download_button(
                label="📩 点击下载处理后的 PDF",
                data=output_stream.getvalue(),
                file_name="interactive_report_ready.pdf",
                mime="application/pdf"
            )

import re

# ================= TAB 2: 原生电子书签抓取 =================
with tab2:
    st.header("📑 智能目录提取与修正仪")
    st.info("💡 如果 PDF 自带书签，会秒出数据；如果没有原生书签，我们将启动视觉正则引擎，自动从文字排版中“硬抓”目录！")
    
    toc_file = st.file_uploader("全自动提取书签与目录... 请把 PDF 拖进来", type="pdf", key="toc_uploader")
    
    if toc_file:
        input_bytes = toc_file.read()
        doc = fitz.open(stream=input_bytes, filetype="pdf")
        
        # 1. 尝试：原生 TOC (Bookmarks)
        toc = doc.get_toc() # [[层级, 标题, 页码], ...]
        
        if toc:
            st.success(f"🎉 成功秒抓！检测到 {len(toc)} 条原生目录数据。")
            df = pd.DataFrame(toc, columns=["层级 (Level)", "目录标题 (Title)", "对应页码 (Page)"])
            
            # 使用 Data Editor 允许用户二次修补
            st.markdown("👇 **你可以在下面的表格里手工修改错别字或调整顺序，改完即自动保存**")
            edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
            
            csv = edited_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 导出最终版为 Excel (CSV)", data=csv, file_name='extracted_bookmarks.csv', mime='text/csv', type="primary")
            
        else:
            # 2. 备用方案：视觉目录引擎 (Visual OCR/Regex Regex)
            st.warning("⚠️ 糟糕，该 PDF 没有系统自带书签。启动【视觉图片/文字双模探测引擎】。")
            
            st.markdown("---")
            st.subheader("🤖 视觉目录分析 (Visual TOC Analysis)")
            
            col_search_type, col_search_val = st.columns(2)
            with col_search_type:
                search_mode = st.radio("如何寻找目录所在地？", ["自动检索特征文字 (Auto)", "手动输入 PDF 页码 (Manual)"])
            
            target_pages = []
            if search_mode == "自动检索特征文字 (Auto)":
                with col_search_val:
                    keyword = st.text_input("探测雷达 (关键词)", value="Inside This Report")
                
                if st.button("开始深度扫描"):
                    with st.spinner("正在逐页解析文字底层..."):
                        # 扫描前20页寻找关键字
                        for p in range(min(20, len(doc))):
                            text = doc[p].get_text("text")
                            if keyword.lower() in text.lower():
                                target_pages.append(p)
                                # 找到连续的可能目录页 (假设目录最多连着 3 页)
                                if p+1 < len(doc) and keyword.lower() in doc[p+1].get_text("text").lower():
                                    target_pages.append(p+1)
                                break
                    if not target_pages:
                        st.error(f"前20页未找到包含 `{keyword}` 的页面，请尝试手动模式。")
            else:
                with col_search_val:
                    pg_range = st.text_input("请输入目录所在的 PDF 页码 (例如: 1-2, 或 3)", value="1")
                    toc_pattern = st.selectbox("目录排版类型", ["Title + Number", "Number + Title", "Label + Title + Number"], key="toc_pattern_tab2")
                
                if st.button("指定页码开始提取"):
                    with st.spinner("正在提取强制页码排版..."):
                        try:
                            if "-" in pg_range:
                                start, end = pg_range.split("-")
                                target_pages = list(range(int(start)-1, int(end)))
                            else:
                                target_pages = [int(pg_range)-1]
                        except Exception:
                            st.error("页码格式输入错误！")
            
            # --- 核心正则表达式处理 ---
            if target_pages:
                st.success(f"✔️ 锁定目录位于 PDF 的第 {[p+1 for p in target_pages]} 页，开始解析数据...")
                
                extracted_data = []
                for p_num in target_pages:
                    page = doc[p_num]
                    w, h = page.rect.width, page.rect.height
                    blocks = page.get_text("blocks")
                    
                    # 1. 区域过滤：忽略页眉页脚 (上下 8%)
                    v_margin = h * 0.08
                    filtered_blocks = [b for b in blocks if b[1] > v_margin and b[3] < h - v_margin]
                    if not filtered_blocks: continue
                    
                    # 2. 纵向分组 (行)
                    filtered_blocks.sort(key=lambda b: b[1])
                    lines = []
                    current_line = [filtered_blocks[0]]
                    for i in range(1, len(filtered_blocks)):
                        prev = current_line[-1]
                        curr = filtered_blocks[i]
                        # V3 优化：压低公差 (25% 或最大 8px)
                        bh = curr[3] - curr[1]
                        tol = min(bh * 0.25, 8)
                        if abs(curr[1] - prev[1]) < tol:
                            current_line.append(curr)
                        else:
                            lines.append(current_line)
                            current_line = [curr]
                    lines.append(current_line)
                    
                    # 3. 横向切分 (列) 并匹配
                    for line_blocks in lines:
                        line_blocks.sort(key=lambda b: b[0])
                        segments = []
                        curr_seg = [line_blocks[0]]
                        for i in range(1, len(line_blocks)):
                            prev = curr_seg[-1]
                            curr = line_blocks[i]
                            gap = curr[0] - prev[2]
                            bh = curr[3] - curr[1]
                            if gap > bh * 1.5: # 稍微收紧分栏检测
                                segments.append(curr_seg)
                                curr_seg = [curr]
                            else:
                                curr_seg.append(curr)
                        segments.append(curr_seg)
                        
                        for seg in segments:
                            # V3 优化：宽度过滤
                            seg_x0 = min(b[0] for b in seg)
                            seg_x1 = max(b[2] for b in seg)
                            if (seg_x1 - seg_x0) > w * 0.7:
                                continue
                                
                            text = " ".join([b[4].strip() for b in seg]).replace("\n", " ").strip()
                            if not text: continue
                            
                            match = None
                            # V3 优化：限制页码位数为 1-3 位
                            if toc_pattern == "Title + Number":
                                match = re.search(r'^(.*?)\s+[\.·\-_]*\s*(\d{1,3})$', text)
                            elif toc_pattern == "Number + Title":
                                match = re.search(r'^(\d{1,3})\s+[\.·\-_]*\s*(.*)$', text)
                            elif toc_pattern == "Label + Title + Number":
                                match = re.search(r'^([A-Za-z]+\s*\d+)\s+(.*?)\s+(\d{1,3})$', text)
                            
                            if match:
                                if toc_pattern == "Number + Title":
                                    title = match.group(2).strip(" .-_")
                                    page_num = match.group(1)
                                elif toc_pattern == "Label + Title + Number":
                                    title = f"{match.group(1)} {match.group(2)}".strip(" .-_")
                                    page_num = match.group(3)
                                else: # Title + Number
                                    title = match.group(1).strip(" .-_")
                                    page_num = match.group(2)
                                    
                                if len(title) > 2 and not title.isdigit():
                                    extracted_data.append(["1", title, page_num])
                
                if extracted_data:
                    df = pd.DataFrame(extracted_data, columns=["层级 (Level)", "目录标题 (Title)", "对应页码 (Page)"])
                    st.markdown("👇 **以下是机器视觉猜测的结果。为了防止排版诡异导致的错误，你可以在此直接对表格进行删除行/修改文字的操作！**")
                    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
                    
                    csv = edited_df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("📥 导出终版表格为 Excel (CSV)", data=csv, file_name='extracted_toc_visual.csv', mime='text/csv', type="primary")
                else:
                    st.error("😭 页面找到了，但排版实在太诡异了，正则规则没能把标题和页码配对上。建议回炉重造或直接求助。")


# ================= TAB 3: 智能目录搜索DEMO (Visual Debugger) =================
with tab3:
    st.header("🔍 智能目录视觉探测引擎 (Debug Mode)")
    st.info("💡 这是一个可视化工具，展示机器是如何在页面上寻找目录项的。红色框代表被正则命中的区域。")
    
    demo_file = st.file_uploader("上传 PDF 开启视觉探测...", type="pdf", key="demo_uploader")
    
    if demo_file:
        input_bytes = demo_file.read()
        doc = fitz.open(stream=input_bytes, filetype="pdf")
        
        st.markdown("---")
        col_ctrl1, col_ctrl2 = st.columns(2)
        
        with col_ctrl1:
            pg_num = st.number_input("请输入要查看的目录页码 (PDF 物理页码)", min_value=1, max_value=len(doc), value=1)
            toc_pattern = st.selectbox("目录排版类型", ["Title + Number", "Number + Title", "Label + Title + Number"], key="toc_pattern_tab3")
        
        if st.button("运行视觉探测 DEMO", type="primary"):
            page_index = pg_num - 1
            page = doc[page_index]
            w, h = page.rect.width, page.rect.height
            
            # 1. 提取块并应用高级分栏合并算法
            blocks = page.get_text("blocks")
            
            # 区域过滤 (上下 8%)
            v_margin = h * 0.08
            filtered_blocks = [b for b in blocks if b[1] > v_margin and b[3] < h - v_margin]
            
            line_segments = [] # 存储 (text, [rects])
            if filtered_blocks:
                # 纵向分组
                filtered_blocks.sort(key=lambda b: b[1])
                lines = []
                current_line = [filtered_blocks[0]]
                for i in range(1, len(filtered_blocks)):
                    prev = current_line[-1]
                    curr = filtered_blocks[i]
                    # V3 优化：压低垂直合并公差 (25% 或最大 8px)
                    bh = curr[3] - curr[1]
                    tol = min(bh * 0.25, 8)
                    if abs(curr[1] - prev[1]) < tol:
                        current_line.append(curr)
                    else:
                        lines.append(current_line)
                        current_line = [curr]
                lines.append(current_line)
                
                # 横向切分 (分栏处理)
                for lb in lines:
                    lb.sort(key=lambda x: x[0])
                    seg = [lb[0]]
                    for i in range(1, len(lb)):
                        prev = seg[-1]
                        curr = lb[i]
                        gap = curr[0] - prev[2]
                        bh = curr[3] - curr[1]
                        if gap > bh * 1.5: # 稍微收紧分栏检测
                            # V3 优化：宽度过滤
                            seg_x0 = min(b[0] for b in seg)
                            seg_x1 = max(b[2] for b in seg)
                            if (seg_x1 - seg_x0) < w * 0.7:
                                text = " ".join([b[4].strip() for b in seg]).replace("\n", " ")
                                rects = [fitz.Rect(b[0], b[1], b[2], b[3]) for b in seg]
                                line_segments.append((text, rects))
                            seg = [curr]
                        else:
                            seg.append(curr)
                    # 处理最后一个片段
                    seg_x0 = min(b[0] for b in seg)
                    seg_x1 = max(b[2] for b in seg)
                    if (seg_x1 - seg_x0) < w * 0.7:
                        text = " ".join([b[4].strip() for b in seg]).replace("\n", " ")
                        rects = [fitz.Rect(b[0], b[1], b[2], b[3]) for b in seg]
                        line_segments.append((text, rects))

            # 2. 匹配并绘图
            zoom = 2
            mat = fitz.Matrix(zoom, zoom)
            
            found_count = 0
            for text, rects in line_segments:
                line = text.strip()
                match = None
                # V3 优化：限制页码位数为 1-3 位
                if toc_pattern == "Title + Number":
                    match = re.search(r'^(.*?)\s+[\.·\-_]*\s*(\d{1,3})$', line)
                elif toc_pattern == "Number + Title":
                    match = re.search(r'^(\d{1,3})\s+[\.·\-_]*\s*(.*)$', line)
                elif toc_pattern == "Label + Title + Number":
                    match = re.search(r'^([A-Za-z]+\s*\d+)\s+(.*?)\s+(\d{1,3})$', line)
                
                if match:
                    if toc_pattern == "Number + Title":
                        title = match.group(2)
                    elif toc_pattern == "Label + Title + Number":
                        title = match.group(2)
                    else:
                        title = match.group(1)
                        
                    if len(title.strip()) > 2 and not title.strip().isdigit():
                        for r in rects:
                            page.draw_rect(r, color=(1, 0, 0), width=1.5)
                        found_count += 1
            
            # 3. 渲染为图片
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            st.success(f"探测完成！在第 {pg_num} 页共命中了 {found_count} 个可能的目录项。")
            st.image(img_data, caption=f"第 {pg_num} 页的视觉探测结果 (红色框为识别出的目录项)", use_container_width=True)
            
            if found_count == 0:
                st.warning("⚠️ 未能在此页探测到任何符合特征的目录项，请检查页码是否正确，或尝试手动模式下的其他页面。")
