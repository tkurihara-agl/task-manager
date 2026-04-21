# ============================================================
# app.py - Streamlit フロントエンド
# ============================================================
# 起動方法:
#   cd reference/frontend
#   streamlit run app.py
#
# 事前にバックエンドを起動しておくこと:
#   cd reference/backend && uvicorn main:app --reload --port 8000

import streamlit as st
import requests
from datetime import datetime, date

# バックエンドのURL
API_BASE = "http://localhost:8000"


# ============================================================
# API クライアント関数
# ============================================================

def api_get(path: str, token: str = None) -> dict | list | None:
    """GETリクエストを送る"""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        res = requests.get(f"{API_BASE}{path}", headers=headers, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"APIエラー: {e}")
        return None


def api_post(path: str, data: dict, token: str = None) -> dict | None:
    """POSTリクエストを送る"""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        res = requests.post(f"{API_BASE}{path}", json=data, headers=headers, timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.HTTPError as e:
        # バックエンドからのエラーメッセージを表示
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        st.error(f"エラー: {detail}")
        return None
    except Exception as e:
        st.error(f"APIエラー: {e}")
        return None


def api_put(path: str, data: dict, token: str = None) -> dict | None:
    """PUTリクエストを送る"""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        res = requests.put(f"{API_BASE}{path}", json=data, headers=headers, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"APIエラー: {e}")
        return None


def api_delete(path: str, token: str = None) -> bool:
    """DELETEリクエストを送る"""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        res = requests.delete(f"{API_BASE}{path}", headers=headers, timeout=10)
        res.raise_for_status()
        return True
    except Exception as e:
        st.error(f"APIエラー: {e}")
        return False


# ============================================================
# セッション状態の初期化
# ============================================================

def init_session_state():
    """st.session_state の初期値を設定する"""
    if "token" not in st.session_state:
        st.session_state.token = None         # JWTトークン（ログイン中はここに入る）
    if "username" not in st.session_state:
        st.session_state.username = None       # ログイン中のユーザー名
    if "page" not in st.session_state:
        st.session_state.page = "login"        # 現在のページ


# ============================================================
# ログイン・ユーザー登録画面
# ============================================================

def render_auth_page():
    """ログイン・ユーザー登録画面を表示する"""
    st.title("Task Manager")

    # タブでログインと登録を切り替え
    tab_login, tab_register = st.tabs(["ログイン", "ユーザー登録"])

    # ---- ログインタブ ----
    with tab_login:
        with st.form("login_form"):
            username = st.text_input("ユーザー名")
            password = st.text_input("パスワード", type="password")
            submitted = st.form_submit_button("ログイン", use_container_width=True)

            if submitted and username and password:
                result = api_post("/auth/login", {
                    "username": username,
                    "password": password,
                })
                if result:
                    # トークンをセッションに保存
                    st.session_state.token = result["access_token"]
                    st.session_state.username = username
                    st.session_state.page = "dashboard"
                    st.rerun()

    # ---- ユーザー登録タブ ----
    with tab_register:
        with st.form("register_form"):
            new_username = st.text_input("ユーザー名（3文字以上）")
            new_email = st.text_input("メールアドレス")
            new_password = st.text_input("パスワード（6文字以上）", type="password")
            submitted = st.form_submit_button("登録", use_container_width=True)

            if submitted and new_username and new_email and new_password:
                result = api_post("/auth/register", {
                    "username": new_username,
                    "email": new_email,
                    "password": new_password,
                })
                if result:
                    st.success("登録完了！ログインタブからログインしてください。")


# ============================================================
# ダッシュボード（メイン画面）
# ============================================================

def update_task_field(task_id: int, field_name: str, widget_key: str):
    """
    selectbox変更時のコールバック関数

    on_changeに渡すことで、画面描画の「前」にAPIを呼ぶ。
    これにより、画面は常に最新のDB状態で描画される（1回で済む）。

    引数:
        task_id     : 更新対象のタスクID
        field_name  : 更新するフィールド名（"status" または "priority"）
        widget_key  : selectboxのkey（session_stateから新しい値を取り出すため）
    """
    new_value = st.session_state[widget_key]
    token = st.session_state.token
    api_put(f"/tasks/{task_id}", {field_name: new_value}, token=token)


def render_dashboard():
    """ダッシュボード（タスク一覧・統計）を表示する"""
    token = st.session_state.token

    # ---- サイドバー ----
    with st.sidebar:
        st.title(f"Task Manager")
        st.caption(f"ログイン中: {st.session_state.username}")
        st.divider()

        # ログアウトボタン
        if st.button("ログアウト", use_container_width=True):
            st.session_state.token = None
            st.session_state.username = None
            st.session_state.page = "login"
            st.rerun()

        st.divider()

        # ---- フィルタリング ----
        st.subheader("フィルター")
        filter_status = st.selectbox(
            "ステータス",
            ["すべて", "todo", "in_progress", "done"],
        )
        filter_priority = st.selectbox(
            "優先度",
            ["すべて", "high", "medium", "low"],
        )
        filter_search = st.text_input("キーワード検索")

    # ---- 統計情報 ----
    stats = api_get("/tasks/stats", token=token)
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("全タスク", stats["total"])
        with col2:
            st.metric("未着手", stats["todo"])
        with col3:
            st.metric("進行中", stats["in_progress"])
        with col4:
            st.metric("完了", stats["done"])

    st.divider()

    # ---- 新規タスク作成 ----
    with st.expander("新しいタスクを作成", expanded=False):
        with st.form("create_task_form"):
            title = st.text_input("タイトル")
            description = st.text_area("説明（任意）")
            col1, col2, col3 = st.columns(3)
            with col1:
                priority = st.selectbox("優先度", ["medium", "high", "low"])
            with col2:
                status_val = st.selectbox("ステータス", ["todo", "in_progress", "done"])
            with col3:
                due_date = st.date_input("期限（任意）", value=None)

            submitted = st.form_submit_button("作成", use_container_width=True)

            if submitted and title:
                task_data = {
                    "title": title,
                    "description": description,
                    "priority": priority,
                    "status": status_val,
                }
                # 期限が設定されている場合のみ追加
                if due_date:
                    task_data["due_date"] = datetime.combine(due_date, datetime.min.time()).isoformat()

                result = api_post("/tasks", task_data, token=token)
                if result:
                    st.success("タスクを作成しました！")
                    st.rerun()

    st.divider()

    # ---- タスク一覧 ----
    st.subheader("タスク一覧")

    # フィルターパラメータを構築
    params = ""
    param_parts = []
    if filter_status != "すべて":
        param_parts.append(f"status={filter_status}")
    if filter_priority != "すべて":
        param_parts.append(f"priority={filter_priority}")
    if filter_search:
        param_parts.append(f"search={filter_search}")
    if param_parts:
        params = "?" + "&".join(param_parts)

    tasks = api_get(f"/tasks{params}", token=token)

    if not tasks:
        st.info("タスクはまだありません。上の「新しいタスクを作成」から追加してください。")
        return

    # タスクをカードとして表示
    # Streamlitはウィジェット操作のたびにスクリプト全体が再実行される仕様のため、
    # selectboxの変更を検知したら即座にAPIを呼んで更新する方式にしている。
    # 「更新ボタン」を廃止することで、クリック数が減って操作が軽快になる。
    for task in tasks:
        # ステータス・優先度に応じたアイコン
        status_emoji = {"todo": "📋", "in_progress": "🔄", "done": "✅"}.get(task["status"], "📋")
        priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task["priority"], "🟡")

        with st.expander(f"{status_emoji} {priority_emoji} {task['title']}"):
            # 説明
            if task["description"]:
                st.write(task["description"])
                st.divider()

            # 操作エリア: ステータス・優先度・削除
            col_status, col_priority, col_due, col_delete = st.columns([2, 2, 2, 1])

            with col_status:
                # ステータス変更（on_changeで画面描画前にAPI送信）
                # - 変更検知してから画面描画する通常のrerunだと、
                #   「古い統計表示 → API送信 → 再rerun → 新しい統計表示」で2回描画されてしまう
                # - on_changeコールバックを使うと、描画の前にAPIが呼ばれるので1回で済む
                status_options = ["todo", "in_progress", "done"]
                status_key = f"status_{task['id']}"
                st.selectbox(
                    "ステータス",
                    status_options,
                    index=status_options.index(task["status"]),
                    key=status_key,
                    on_change=update_task_field,
                    args=(task["id"], "status", status_key),
                )

            with col_priority:
                # 優先度変更（on_changeで画面描画前にAPI送信）
                priority_options = ["low", "medium", "high"]
                priority_key = f"priority_{task['id']}"
                st.selectbox(
                    "優先度",
                    priority_options,
                    index=priority_options.index(task["priority"]),
                    key=priority_key,
                    on_change=update_task_field,
                    args=(task["id"], "priority", priority_key),
                )

            with col_due:
                # 期限の表示（読み取り専用）
                if task.get("due_date"):
                    st.text_input(
                        "期限",
                        value=task["due_date"][:10],
                        disabled=True,
                        key=f"due_{task['id']}",
                    )
                else:
                    st.text_input(
                        "期限",
                        value="未設定",
                        disabled=True,
                        key=f"due_{task['id']}",
                    )

            with col_delete:
                # 削除ボタンは高さを合わせるためラベルを空白で揃える
                st.write("")
                st.write("")
                if st.button("🗑 削除", key=f"delete_{task['id']}", type="secondary"):
                    if api_delete(f"/tasks/{task['id']}", token=token):
                        st.rerun()


# ============================================================
# アプリのエントリーポイント
# ============================================================

def main():
    st.set_page_config(
        page_title="Task Manager",
        page_icon="✅",
        layout="wide",
    )

    init_session_state()

    # ログイン状態に応じて画面を切り替え
    if st.session_state.token:
        render_dashboard()
    else:
        render_auth_page()


if __name__ == "__main__":
    main()
