import streamlit as st
from src.run_agent import load_system_prompt, ask_agent, memory

# ------------------ INIT SESSION ------------------
if "is_logged_in" not in st.session_state:
    st.session_state.is_logged_in = False
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "login"

if "is_logged_in" not in st.session_state:
    st.session_state.is_logged_in = False

if "active_tab" not in st.session_state:
    st.session_state.active_tab = "login"

# user_id lưu id (int) từ DB khi login thành công; None nếu chưa login
if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "username" not in st.session_state:
    st.session_state.username = ""

# messages cho chat UI
if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "active_conversation_id" not in st.session_state:
    st.session_state.active_conversation_id = None

# ---------- AUTH UI (sidebar) ----------
st.sidebar.title("👤 Tài khoản")
if not st.session_state.is_logged_in:
    tab_login, tab_register = st.sidebar.tabs(["🔑 Đăng nhập", "📝 Đăng ký"])

    # ---- LOGIN ----
    with tab_login:
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            user_id_db = memory.authenticate_user(username, password)
            if user_id_db:
                st.session_state.is_logged_in = True
                st.session_state.user_id = user_id_db
                st.session_state.username = username
                # khi login lần đầu, tạo conversation mặc định nếu chưa có
                # memory._get_or_create_conversation(st.session_state.user_id)
                st.success("Đăng nhập thành công!")
                st.rerun()
            else:
                st.error("Sai username hoặc password")

    # ---- REGISTER ----
    with tab_register:
        new_username = st.text_input("New Username", key="reg_username")
        new_password = st.text_input("New Password", type="password", key="reg_password")
        if st.button("Register"):
            ok = memory.register_user(new_username, new_password)
            if ok:
                st.success("Tạo tài khoản thành công! Vui lòng đăng nhập.")
                # st.session_state.active_tab = "login"
                # st.rerun()
            else:
                st.error("Username đã tồn tại")
                # xóa input để nhập lại
                st.session_state.reg_username = ""
                st.session_state.reg_password = ""
                st.rerun()
else:
    # đã login -> show tên + nút logout
    st.sidebar.markdown(f"**Xin chào:** `{st.session_state.username}`")
    if st.sidebar.button("🚪 Đăng xuất"):
        # clear only keys we want (tránh xóa config quan trọng)
        for k in ["is_logged_in","user_id","username","messages","active_conversation_id"]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()

# ---------- MAIN APP ----------
st.set_page_config(page_title="Finance AI Assistant", page_icon="📈", layout="wide")
st.title("🤖 Finance ReAct AI Agent")

# Sidebar: lịch sử chat (chỉ truy vấn DB khi user đã login and has user_id)
st.sidebar.markdown("---")
st.sidebar.subheader("📜 Lịch sử chat")
if st.session_state.user_id is None:
    st.sidebar.info("Vui lòng đăng nhập để xem lịch sử chat")
else:
    # Nút tạo hội thoại mới
    if st.sidebar.button("➕ Cuộc trò chuyện mới"):
        # Xóa session messages
        st.session_state.messages = []
        # # Tạo conversation mới trong DB
        new_conv_id = memory.create_conversation(
            st.session_state.user_id,
            title=""
        )
        st.session_state.active_conversation_id = new_conv_id
        st.rerun()

    convs = memory.get_conversations(st.session_state.user_id)  # now safe: user_id exists\
    if not convs:
        st.sidebar.info("Chưa có lịch sử")
    else:
        for conv in convs:
            label = conv['title'] if not conv['created_at'] else f"{conv['title']} ({conv['created_at']:%d/%m %H:%M})"
            if st.sidebar.button(label, key=f"load_{conv['id']}"):
                msgs = memory.get_conversation_messages(conv['id'])
                st.session_state.messages = [{"role": m["role"], "content": m["content"]} for m in msgs]
                st.session_state.active_conversation_id = conv['id']
                st.rerun()

# --- Chat mode ---
if "user_id" not in st.session_state or st.session_state.user_id is None:
    st.warning("Vui lòng đăng nhập để sử dụng chat.")   
else:
    system_prompt = load_system_prompt()
    st.subheader("💬 Chat với AI Agent")
    
    for msg in st.session_state.messages:
        with st.chat_message("user" if msg["role"] == "user" else "assistant"):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Nhập câu hỏi..."):

        # Lưu tin nhắn user vào DB
        # memory.add_message_by_conversation(st.session_state.active_conversation_id, "user", prompt)

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Đang xử lý..."):
                if st.session_state.active_conversation_id is None:
                    # Nếu không có, tạo một cuộc hội thoại mới
                    st.session_state.active_conversation_id = memory.create_conversation(st.session_state.user_id, title="")
                answer, observations, trace, conv_id = ask_agent(st.session_state.user_id, prompt, system_prompt=system_prompt, conversation_id=st.session_state.active_conversation_id)
                # st.session_state.active_conversation_id = conv_id
                st.markdown(answer)
                
        st.session_state.messages.append({"role": "assistant", "content": answer})
