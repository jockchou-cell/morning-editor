好的，这是我的后端代码，帮我修改，我作为一个不会写代码的人，希望部署操作过程不要有太复杂
import streamlit as st
from openai import OpenAI
import urllib.parse
import time
import requests
import random

# 页面配置
st.set_page_config(page_title="朝起拾要·全能工作室", layout="wide", page_icon="☀️")

# --- 1. 初始化保险箱 ---
if 'article_cache' not in st.session_state:
    st.session_state['article_cache'] = ""
if 'news_cache' not in st.session_state:
    st.session_state['news_cache'] = []
if 'input_cache' not in st.session_state:
    st.session_state['input_cache'] = ""

# --- 2. 侧边栏：朝起拾要 ---
with st.sidebar:
    st.title("☀️ 朝起拾要")
    st.divider()
    
    # 智能 Key 检测
    ds_key = st.secrets.get("ds_key")
    if ds_key:
        st.success("✅ DeepSeek API 已自动配置")
    else:
        ds_key = st.text_input("DeepSeek API Key", type="password")
        st.info("💡 提示：在云端配置 Secrets 后，此框将消失。")

    st.caption("核心模型：DeepSeek-V3 | 绘图引擎：Pollinations Cloud")
    
    st.divider()
    st.subheader("🖼️ 视觉实验室")
    img_mode = st.radio("获取方式", ["AI 快速出图", "搜索无版权图片"])
    
    if img_mode == "AI 快速出图":
        user_prompt = st.text_area("粘贴图片提示词 (英文)", placeholder="例如: Cyberpunk electric car...")
        if st.button("立即出图 🎨"):
            if not user_prompt:
                st.warning("请填入提示词")
            else:
                with st.spinner("AI 正在云端渲染，请稍候..."):
                    # 彻底清洗，防止非法字符中断 URL
                    clean_p = "".join(e for e in user_prompt if e.isalnum() or e == " ")
                    encoded = urllib.parse.quote(clean_p.strip())
                    seed = random.randint(1, 1000000)
                    # 采用 HTTPS 负载均衡地址，增加成功率
                    img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=512&seed={seed}&nologo=true"
                    # 这里改用 markdown 方式，有时比 st.image 在云端更稳
                    st.markdown(f"![Generated Image]({img_url})")
                    st.caption("✨ 生成成功，长按或右键图片另存为。")
    else:
        st.link_button("Pixabay (图库)", "https://pixabay.com/")
        st.link_button("Pexels (素材)", "https://www.pexels.com/zh-cn/")

# --- 3. 主界面：内容编辑 ---
st.header("内容编辑")

# 热点展示区
st.subheader("🔥 实时全网热点")
if st.button("🔄 刷新实时热点"):
    with st.spinner("正在通过全球节点同步热搜..."):
        # 换用对海外 IP 响应更友好的百度热搜镜像
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        urls = [
            "https://api.oick.cn/api/baidu", # 备用源1
            "https://tenapi.cn/v2/webhot"     # 备用源2
        ]
        
        success = False
        for url in urls:
            try:
                resp = requests.get(url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    # 根据不同接口结构提取前10条
                    if "oick" in url:
                        # 镜像源通常返回列表，此处取前10
                        st.session_state['news_cache'] = [item['title'] for item in data[:10]]
                    else:
                        st.session_state['news_cache'] = [item['name'] for item in data['data'][:10]]
                    st.success("同步成功！")
                    success = True
                    break
            except:
                continue
        
        if not success:
            st.error("云端网络波动，建议点击下方媒体链接手动摘取。")

# 渲染按钮
if st.session_state['news_cache']:
    cols = st.columns(2)
    for i, n in enumerate(st.session_state['news_cache']):
        if cols[i % 2].button(f"📌 {n}", key=f"btn_{i}", use_container_width=True):
            st.session_state['input_cache'] = n
            st.rerun()
else:
    st.info("💡 云端同步受限，建议前往最真实的信源：")
    c1, c2, c3, c4 = st.columns(4)
    c1.link_button("36氪", "https://36kr.com/technology")
    c2.link_button("IT之家", "https://www.ithome.com/")
    c3.link_button("汽车之家", "https://www.autohome.com.cn/")
    c4.link_button("微博热搜", "https://s.weibo.com/top/summary")

st.divider()

# 编辑区
raw_input = st.text_area("在此粘贴素材或编辑：", value=st.session_state['input_cache'], height=200)

if st.button("一键生成爆款文 🔥"):
    if not ds_key:
        st.error("请配置 API Key")
    elif not raw_input:
        st.warning("素材内容为空。")
    else:
        client = OpenAI(api_key=ds_key, base_url="https://api.deepseek.com")
        try:
            with st.spinner("主编正在疯狂写作..."):
                sys_msg = "你是一个10万粉科技主编。风格犀利口语化。结构：3个标题、引言、正文、点评。500字以上。"
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": raw_input}]
                )
                st.session_state['article_cache'] = response.choices[0].message.content
        except Exception as e:
            st.error(f"生成失败：{e}")

# 展示结果
if st.session_state['article_cache']:
    st.markdown("---")
    st.markdown(st.session_state['article_cache'])