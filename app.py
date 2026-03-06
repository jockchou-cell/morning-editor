# --- 3. 主界面：内容编辑 ---
st.header("内容编辑")

st.subheader("🔥 实时全网热点")

# 刷新按钮：点击时清空旧缓存并抓取新数据
if st.button("🔄 刷新实时热搜"):
    with st.spinner("正在同步全球热点数据..."):
        headers = {'User-Agent': 'Mozilla/5.0'}
        # 尝试两个稳定的镜像接口
        urls = ["https://api.oick.cn/api/baidu", "https://tenapi.cn/v2/webhot"]
        success = False
        
        for url in urls:
            try:
                resp = requests.get(url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    # 关键修复：直接存入原始数据（包含标题和链接）
                    if "oick" in url:
                        # 镜像源返回格式：[{"title": "...", "url": "..."}, ...]
                        st.session_state['news_cache'] = data[:10]
                    else:
                        # TenAPI 返回格式：{"data": [{"name": "...", "url": "..."}, ...]}
                        st.session_state['news_cache'] = data['data'][:10]
                    
                    st.success("热点同步成功！")
                    success = True
                    break
            except: continue
        
        if not success:
            st.error("同步失败，请使用下方快捷链接。")
            st.session_state['news_cache'] = [] # 失败则清空

st.divider()

# --- 核心逻辑：严谨的“二选一”展示 ---
if st.session_state['news_cache']:
    # 情况 A：缓存中有数据，展示热点列表，隐藏快捷网站
    st.caption("✅ 已获取最新热点（点击标题导入素材，点击'原文'跳转）")
    
    for i, item in enumerate(st.session_state['news_cache']):
        # 兼容不同接口的字段名
        title = item.get('title') or item.get('name')
        link = item.get('url') or f"https://www.baidu.com/s?wd={urllib.parse.quote(title)}"
        
        col_btn, col_link = st.columns([0.85, 0.15])
        
        # 点击标题：将文字填入下方编辑框
        if col_btn.button(f"📌 {title}", key=f"news_btn_{i}", use_container_width=True):
            st.session_state['input_cache'] = title
            st.rerun()
            
        # 点击原文：直接跳转到新闻详情页
        col_link.link_button("原文 🔗", link)
    
    if st.button("🗑️ 清除热点，返回快捷导航"):
        st.session_state['news_cache'] = []
        st.rerun()

else:
    # 情况 B：缓存为空，展示 6 个媒体快捷链接
    st.info("💡 当前未同步热搜，建议前往以下信源摘取素材：")
    c1, c2, c3 = st.columns(3)
    c4, c5, c6 = st.columns(3)
    c1.link_button("36氪科技", "https://36kr.com/technology")
    c2.link_button("IT之家", "https://www.ithome.com/")
    c3.link_button("汽车之家", "https://www.autohome.com.cn/")
    c4.link_button("虎扑热榜", "https://bbs.hupu.com/all-groot")
    c5.link_button("界面新闻", "https://www.jiemian.com/")
    c6.link_button("今日头条", "https://www.toutiao.com/")