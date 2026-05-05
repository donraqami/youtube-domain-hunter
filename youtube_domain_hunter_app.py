import streamlit as st
import re
import csv
import io
import socket
import time
import urllib.parse
from datetime import datetime

import requests

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="YouTube Expired Domain Hunter",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ============================================================
# CUSTOM CSS FOR GATED LOGIN LOOK
# ============================================================
st.markdown("""
<style>
    .main { background-color: #0f1117; }
    .stTextInput > div > div > input { background-color: #1a1d29; color: #ffffff; border: 1px solid #30354a; }
    .stTextArea > div > div > textarea { background-color: #1a1d29; color: #ffffff; border: 1px solid #30354a; }
    .stButton > button { background-color: #ff4b4b; color: white; border-radius: 8px; padding: 0.6rem 1.5rem; font-weight: 600; border: none; }
    .stButton > button:hover { background-color: #ff6b6b; }
    .stProgress > div > div > div { background-color: #ff4b4b; }
    h1, h2, h3 { color: #ffffff !important; }
    p, label, .stMarkdown { color: #b0b3c7 !important; }
    .success-box { background-color: #1a3a1a; border: 1px solid #2d5a2d; border-radius: 8px; padding: 1rem; color: #4ade80; }
    .error-box { background-color: #3a1a1a; border: 1px solid #5a2d2d; border-radius: 8px; padding: 1rem; color: #f87171; }
    .login-card { background-color: #1a1d29; border: 1px solid #30354a; border-radius: 12px; padding: 2rem; max-width: 420px; margin: 0 auto; }
    .stats-card { background-color: #1a1d29; border: 1px solid #30354a; border-radius: 8px; padding: 1rem; text-align: center; }
    .stats-number { font-size: 2rem; font-weight: 700; color: #ff4b4b; }
    .stats-label { font-size: 0.85rem; color: #8b8fa8; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE INIT
# ============================================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'results' not in st.session_state:
    st.session_state.results = []
if 'scanning' not in st.session_state:
    st.session_state.scanning = False

# ============================================================
# GATED AUTH (Simple Password Gate — Upgrade to Supabase later)
# ============================================================
DEMO_USERS = {
    "demo@example.com": "demo123",
    "admin@hunter.app": "admin2026"
}

def show_login():
    st.markdown("<div style='text-align:center; margin-top:3rem;'>", unsafe_allow_html=True)
    st.markdown("<h1>🎯 YouTube Expired Domain Hunter</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#8b8fa8; font-size:1.1rem;'>Find expired domains hiding in YouTube video descriptions</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align:center; margin-bottom:1.5rem;'>🔐 Member Login</h3>", unsafe_allow_html=True)

        # FIXED: Use 1 column for the login form, centered via CSS
        email = st.text_input("Email", placeholder="you@example.com", key="login_email")
        password = st.text_input("Password", type="password", placeholder="••••••••", key="login_password")

        if st.button("Sign In", use_container_width=True):
            if email in DEMO_USERS and DEMO_USERS[email] == password:
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.rerun()
            else:
                st.markdown("<div class='error-box'>❌ Invalid email or password</div>", unsafe_allow_html=True)

        st.markdown("<p style='text-align:center; color:#5a5e75; font-size:0.8rem; margin-top:1rem;'>Demo: demo@example.com / demo123</p>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center; margin-top:3rem; color:#5a5e75; font-size:0.85rem;">
        <p>🔒 Gated access • CSV export • DNS availability check</p>
        <p>Built for domain hunters & SEO professionals</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def extract_urls(text):
    url_pattern = re.compile(
        r'https?://(?:[-\w.])+(?::\d+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?',
        re.IGNORECASE
    )
    return url_pattern.findall(text)

def clean_domain(url):
    try:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return None

def is_major_platform(domain):
    platforms = {
        'youtube.com', 'youtu.be', 'google.com', 'goo.gl',
        'facebook.com', 'fb.me', 'fb.com', 'instagram.com',
        'twitter.com', 'x.com', 't.co', 'linkedin.com',
        'pinterest.com', 'tiktok.com', 'reddit.com',
        'amazon.com', 'amzn.to', 'ebay.com',
        'paypal.com', 'stripe.com', 'shopify.com',
        'wikipedia.org', 'wikimedia.org',
        'apple.com', 'microsoft.com', 'github.com',
        'wordpress.com', 'blogspot.com', 'medium.com',
        'mailchimp.com', 'convertkit.com', 'substack.com',
        'bit.ly', 'tinyurl.com', 't.ly', 'short.io',
        'discord.com', 'discord.gg', 'telegram.org',
        'spotify.com', 'soundcloud.com', 'vimeo.com',
        'dropbox.com', 'drive.google.com', 'docs.google.com',
    }
    return domain in platforms or any(domain.endswith('.' + p) for p in platforms)

def check_domain_availability(domain):
    try:
        socket.setdefaulttimeout(3)
        socket.gethostbyname(domain)
        return 'taken'
    except socket.gaierror:
        return 'likely_available'
    except socket.timeout:
        return 'timeout'
    except Exception:
        return 'error'

def get_video_details(video_id, api_key):
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {'part': 'snippet,statistics', 'id': video_id, 'key': api_key}
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if 'items' in data and len(data['items']) > 0:
            return data['items'][0]
    except Exception as e:
        return None
    return None

def search_youtube_videos(query, api_key, max_results=50):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        'part': 'id,snippet', 'q': query, 'type': 'video',
        'maxResults': max_results, 'key': api_key, 'order': 'relevance'
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        if 'items' in data:
            return data['items']
    except Exception as e:
        return []
    return []

def extract_video_id(url_or_id):
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return None

# ============================================================
# MAIN APP (After Login)
# ============================================================

def show_app():
    # Header
    col1, col2 = st.columns([6, 2])
    with col1:
        st.markdown("<h2>🎯 YouTube Expired Domain Hunter</h2>", unsafe_allow_html=True)
    with col2:
        if st.button("🚪 Logout", type="secondary"):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.rerun()

    st.markdown(f"<p style='color:#8b8fa8;'>Welcome back, <b>{st.session_state.user_email}</b></p>", unsafe_allow_html=True)
    st.divider()

    # --- CONFIGURATION ---
    with st.expander("⚙️ Configuration", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            api_key = st.text_input(
                "YouTube Data API Key",
                type="password",
                placeholder="AIza...",
                help="Get free key at console.cloud.google.com → YouTube Data API v3"
            )
        with col2:
            max_results = st.slider("Max videos per query", 10, 50, 25)

        st.markdown("<p style='color:#5a5e75; font-size:0.8rem;'>💡 Free quota: 10,000 API calls/day. Each search = 100 units, each video detail = 1 unit.</p>", unsafe_allow_html=True)

    st.divider()

    # --- INPUTS ---
    st.markdown("<h3>📥 Enter Search Queries or Video URLs</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:#8b8fa8;'>One per line. Can be search phrases, video URLs, or video IDs.</p>", unsafe_allow_html=True)

    inputs_text = st.text_area(
        "",
        placeholder="best plumbing tools 2019\nhttps://youtube.com/watch?v=ABC123\nroofing contractor tips",
        height=120
    )

    col1, col2, col3 = st.columns([2, 2, 6])
    with col1:
        start_scan = st.button("🚀 Start Hunt", use_container_width=True, disabled=st.session_state.scanning)
    with col2:
        clear_btn = st.button("🧹 Clear", use_container_width=True)
        if clear_btn:
            st.session_state.results = []
            st.rerun()

    # --- SCANNING ---
    if start_scan and api_key and inputs_text.strip():
        st.session_state.scanning = True
        st.session_state.results = []

        # Parse inputs
        raw_inputs = [line.strip() for line in inputs_text.strip().split('\n') if line.strip()]
        video_ids = []
        search_queries = []
        for inp in raw_inputs:
            vid = extract_video_id(inp)
            if vid:
                video_ids.append(vid)
            else:
                search_queries.append(inp)

        total_targets = len(video_ids) + len(search_queries)
        progress_bar = st.progress(0)
        status_text = st.empty()

        all_domains = set()
        results = []
        processed = 0

        # Process direct videos
        for vid in video_ids:
            processed += 1
            progress = processed / max(total_targets, 1)
            progress_bar.progress(min(progress, 0.99))
            status_text.markdown(f"<p style='color:#8b8fa8;'>🔍 Fetching video: <code>{vid}</code> ({processed}/{total_targets})</p>", unsafe_allow_html=True)

            video = get_video_details(vid, api_key)
            if video:
                snippet = video.get('snippet', {})
                stats = video.get('statistics', {})
                title = snippet.get('title', 'Unknown')
                desc = snippet.get('description', '')
                channel = snippet.get('channelTitle', 'Unknown')
                published = snippet.get('publishedAt', '')[:10]
                views = stats.get('viewCount', '0')

                urls = extract_urls(desc)
                for url in urls:
                    domain = clean_domain(url)
                    if not domain or is_major_platform(domain) or domain in all_domains:
                        continue
                    all_domains.add(domain)
                    status = check_domain_availability(domain)
                    time.sleep(0.2)

                    results.append({
                        'domain': domain,
                        'full_url': url,
                        'availability': status,
                        'video_title': title,
                        'video_id': vid,
                        'channel': channel,
                        'published': published,
                        'views': views,
                        'found_at': datetime.now().strftime('%Y-%m-%d %H:%M')
                    })

            time.sleep(0.5)

        # Process search queries
        for query in search_queries:
            processed += 1
            progress = processed / max(total_targets, 1)
            progress_bar.progress(min(progress, 0.99))
            status_text.markdown(f"<p style='color:#8b8fa8;'>🔍 Searching: <b>{query}</b> ({processed}/{total_targets})</p>", unsafe_allow_html=True)

            videos = search_youtube_videos(query, api_key, max_results)
            for item in videos:
                vid = item['id']['videoId']
                snippet = item['snippet']
                title = snippet.get('title', 'Unknown')
                desc = snippet.get('description', '')
                channel = snippet.get('channelTitle', 'Unknown')
                published = snippet.get('publishedAt', '')[:10]

                urls = extract_urls(desc)
                for url in urls:
                    domain = clean_domain(url)
                    if not domain or is_major_platform(domain) or domain in all_domains:
                        continue
                    all_domains.add(domain)
                    status = check_domain_availability(domain)
                    time.sleep(0.2)

                    results.append({
                        'domain': domain,
                        'full_url': url,
                        'availability': status,
                        'video_title': title,
                        'video_id': vid,
                        'channel': channel,
                        'published': published,
                        'views': 'unknown',
                        'found_at': datetime.now().strftime('%Y-%m-%d %H:%M')
                    })

                time.sleep(0.3)

        progress_bar.progress(1.0)
        status_text.markdown("<div class='success-box'>✅ Scan complete!</div>", unsafe_allow_html=True)
        st.session_state.results = results
        st.session_state.scanning = False
        time.sleep(0.5)
        st.rerun()

    elif start_scan and not api_key:
        st.markdown("<div class='error-box'>❌ Please enter your YouTube Data API key in Configuration</div>", unsafe_allow_html=True)
    elif start_scan and not inputs_text.strip():
        st.markdown("<div class='error-box'>❌ Please enter at least one search query or video URL</div>", unsafe_allow_html=True)

    # --- RESULTS ---
    if st.session_state.results:
        results = st.session_state.results

        st.divider()
        st.markdown("<h3>📊 Results</h3>", unsafe_allow_html=True)

        # Stats cards
        available = [r for r in results if r['availability'] == 'likely_available']
        taken = [r for r in results if r['availability'] == 'taken']
        errors = [r for r in results if r['availability'] in ('error', 'timeout')]

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <div class='stats-card'>
                <div class='stats-number'>{len(results)}</div>
                <div class='stats-label'>Total Domains</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class='stats-card'>
                <div class='stats-number' style='color:#4ade80;'>{len(available)}</div>
                <div class='stats-label'>Likely Available</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class='stats-card'>
                <div class='stats-number' style='color:#60a5fa;'>{len(taken)}</div>
                <div class='stats-label'>Taken / Active</div>
            </div>
            """, unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div class='stats-card'>
                <div class='stats-number' style='color:#fbbf24;'>{len(errors)}</div>
                <div class='stats-label'>Errors</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Filter tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🎯 Available", "🔒 Taken", "⚠️ Errors", "📋 All"])

        def show_table(data, tab):
            if not data:
                tab.markdown("<p style='color:#5a5e75;'>No results in this category.</p>", unsafe_allow_html=True)
                return

            df_data = []
            for r in data:
                status_emoji = {
                    'likely_available': '🟢',
                    'taken': '🔴',
                    'error': '🟡',
                    'timeout': '⏱️'
                }.get(r['availability'], '⚪')

                df_data.append({
                    'Status': f"{status_emoji} {r['availability']}",
                    'Domain': r['domain'],
                    'Video': r['video_title'][:45] + '...' if len(r['video_title']) > 45 else r['video_title'],
                    'Channel': r['channel'],
                    'Published': r['published'],
                    'Views': r['views'],
                    'URL': r['full_url']
                })

            tab.dataframe(df_data, use_container_width=True, hide_index=True)

        show_table(available, tab1)
        show_table(taken, tab2)
        show_table(errors, tab3)
        show_table(results, tab4)

        # CSV Export
        st.divider()
        st.markdown("<h3>💾 Export</h3>", unsafe_allow_html=True)

        if results:
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=['domain', 'full_url', 'availability', 'video_title', 'video_id', 'channel', 'published', 'views', 'found_at'])
            writer.writeheader()
            writer.writerows(results)
            csv_bytes = output.getvalue().encode('utf-8')

            col1, col2 = st.columns([2, 4])
            with col1:
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_bytes,
                    file_name=f"expired_domains_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with col2:
                st.markdown(f"<p style='color:#5a5e75; padding-top:0.5rem;'>File: <code>expired_domains_{datetime.now().strftime('%Y%m%d_%H%M')}.csv</code> ({len(results)} rows)</p>", unsafe_allow_html=True)

# ============================================================
# ROUTING
# ============================================================
if not st.session_state.logged_in:
    show_login()
else:
    show_app()
