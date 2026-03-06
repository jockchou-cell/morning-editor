import streamlit as st
import requests
import urllib.parse
import random
from openai import OpenAI

# 1. 页面配置
st.set_page_config(page_title="朝起拾要·全能工作室", layout="wide", page_icon="☀️")

# --- 初始化状态 (持久化存储) ---
if 'article_cache' not in st.session_state:
    st.session_state['article_cache'] = ""
if 'news_cache' not in st.session_state:
    st.session_state['news_cache'] = []
if 'input_cache' not in st.session_state:
    st.session_state['input_cache'] = ""

# --- 2. 侧边栏配置 ---
with st.sidebar:
    st.title("☀️ 朝起拾要")
    st.divider()
    
    # 智能 Key 检测 (修复 Secret 报错)
    ds_key = st.secrets.get("ds_key") 
    if ds_key:
        st.success("✅ API 已从云端自动配置")
    else:
        ds_key = st.text_input("DeepSeek API Key (本地运行请在此填入)", type="password")

    st.divider()
    st.subheader("🖼️ 视觉实验室")
    user_prompt = st.text_area("粘贴图片提示词 (英文)", placeholder="例如: Cyberpunk city...")
    if st.button("立即出图 🎨"):
        if user_prompt:
            with st.spinner("AI 渲染中..."):
                clean_p = "".join(e for e in user_prompt if e.isalnum() or e == " ")
                encoded = urllib.parse.quote(clean_p.strip())
                img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=512&seed={random.randint(1,99999)}&nologo=true"
                st.markdown(f"![Generated Image]({img_url})")
        else:
            st.warning("提示词为空")

# --- 3. 主界面：内容编辑 ---
st.header("内容编辑")

st.subheader("🔥 实时全网热点")
if st.button("🔄 刷新实时热搜"):
    with st.spinner("正在同步全球热搜数据..."):
        headers = {'User-Agent': 'Mozilla/5.0'}
        # 聚合多个备用源以提高稳定性
        urls = ["https://api.oick.cn/api/baidu", "https://tenapi.cn/v2/webhot"]
        temp_news = []
        
        for url in urls:
            try:
                resp = requests.get(url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    # --- 增强型数据解析逻辑 ---
                    # 适配列表格式 (oick)
                    if isinstance(data, list):
                        temp_news = data[:10]
                    # 适配带 data 键的字典格式 (tenapi)
                    elif isinstance(data, dict) and 'data' in data:
                        temp_news = data['data'][:10]
                    # 适配直接返回数据的字典格式
                    elif isinstance(data, dict):
                        temp_news = list(data.values())[:10]
                    
                    if temp_news:
                        st.session_state['news_cache'] = temp_news
                        st.success(f"成功从源 {url.split('/')[2]} 同步热点！")
                        break
            except Exception as e:
                continue
        
        if not temp_news:
            st.error("云端同步暂时受限，请尝试手动摘取。")
            st.session_state['news_cache'] = []

st.divider()

# --- 4. 核心：二选一展示逻辑 ---
# 只有当 news_cache 真正有内容时才展示热点列表
if st.session_state['news_cache']:
    st.caption("✅ 点击标题导入素材，点击 [原文] 跳转网页")
    for i, item in enumerate(st.session_state['news_cache']):
        # 自动提取标题：尝试 title 或 name 键
        title = ""
        if isinstance(item, dict):
            title = item.get('title') or item.get('name') or "未知标题"
            link = item.get('url') or f"https://www.baidu.com/s?wd={urllib.parse.quote(title)}"
        else:
            title = str(item)
            link = f"https://www.baidu.com/s?wd={urllib.parse.quote(title)}"
        
        c_btn, c_link = st.columns([0.85, 0.15])
        if c_btn.button(f"📌 {title}", key=f"nb_{i}", use_container_width=True):
            st.session_state['input_cache'] = title
            st.rerun()
        c_link.link_button("原文 🔗", link)
    
    if st.button("🗑️ 清除热搜结果"):
        st.session_state['news_cache'] = []
        st.rerun()
else:
    # 只有热搜为空时才展示快捷导航链接
    st.info("💡 当前未同步热搜，建议前往以下信源摘取：")
    c1, c2, c3 = st.columns(3)
    c4, c5, c6 = st.columns(3)
    c1.link_button("36氪科技", "https://36kr.com/technology")
    c2.link_button("IT之家", "https://www.ithome.com/")
    c3.link_button("汽车之家", "https://www.autohome.com.cn/")
    c4.link_button("虎扑热榜", "https://bbs.hupu.com/all-groot")
    c5.link_button("界面新闻", "https://www.jiemian.com/")
    c6.link_button("今日头条", "https://www.toutiao.com/")

st.divider()

# --- 5. 编辑与生成区 ---
raw_input = st.text_area("在此粘贴素材或编辑：", value=st.session_state['input_cache'], height=200)

if st.button("开始文章构思 🔥"):
    if not ds_key:
        st.error("请配置 API Key")
    elif not raw_input:
        st.warning("素材内容为空")
    else:
        client = OpenAI(api_key=ds_key, base_url="https://api.deepseek.com")
        try:
            with st.spinner("才思泉涌中..."):
                # 确保字符串完整闭合
                sys_msg = "你是一个顶级主编。风格犀利。结构：5个标题、引言、正文（加粗核心句）、总结。末尾附带：[IMG_PROMPT]: 英文绘图词"
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": raw_input}]
                )
                st.session_state['article_cache'] = response.choices[0].message.content
        except Exception as e:
            st.error(f"生成失败: {e}")

# --- 6. 结果展示 ---
if st.session_state['article_cache']:
    st.markdown("---")
    st.caption("点击右上角图标即可复制全文：")
    # 使用 st.code 实现稳定的一键复制
    st.code(st.session_state['article_cache'], language="markdown")
    st.markdown("### 内容预览")
    st.markdown(st.session_state['article_cache'])