import os
import urllib.parse
from flask import Flask, render_template_string, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("ОШИБКА: Не задан GEMINI_API_KEY в Render!")

client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = """
Ты — экспертный ИИ-аналитик Master Trade 👑📊🚀.
Отвечай на любые вопросы по финансовым рынкам, трейдингу, тех-анализу и новостям.

Правила:
1. ОБЯЗАТЕЛЬНО используй много ярких эмодзи (📊, 🚀, 📈, 📉, ⚠️, 🧠, 💡, 🛡️, 💎, 🔥, 💰, 🎯) в КАЖДОМ ответе.
2. При вопросе "стоит ли торговать сейчас" — объясни фазу рынка (флэт/тренд), роль новостей и правила риск-менеджмента 🛡️.
3. Отвечай четко, понятно и по делу 🎯.
4. На нецелевые вопросы отвечай: "Я аналитический ассистент Master Trade 👑. Отвечаю только на темы рынка и трейдинга! 📊📈"
5. Запрещено упоминать администраторов, контакты или сторонние каналы 🚫.
6. В конце сложных разборов пиши: "⚠️ Аналитика носит информационный характер и не является рекомендацией."
"""

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Master Trade — ИИ-помощник & Новости</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background-color: #0b0e14; color: #ffffff; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
        .chat-container { width: 100%; max-width: 600px; background: #131722; border: 1px solid #2a2e39; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.5); display: flex; flex-direction: column; height: 85vh; }
        .header { background: #1e222d; padding: 16px 20px; text-align: center; border-bottom: 1px solid #2a2e39; }
        .header h2 { font-size: 1.2rem; color: #f0b90b; display: flex; align-items: center; justify-content: center; gap: 8px; }
        .header p { font-size: 0.85rem; color: #848e9c; margin-top: 4px; }
        .tabs { display: flex; border-bottom: 1px solid #2a2e39; background: #181c27; }
        .tab-btn { flex: 1; padding: 12px; background: none; border: none; color: #848e9c; font-weight: bold; cursor: pointer; transition: 0.3s; }
        .tab-btn.active { color: #f0b90b; border-bottom: 2px solid #f0b90b; background: #131722; }
        .sub-categories { display: flex; flex-wrap: wrap; gap: 6px; padding: 10px; background: #181c27; border-bottom: 1px solid #2a2e39; justify-content: center; }
        .cat-btn { background: #2a2e39; border: none; color: #d1d4dc; padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; cursor: pointer; transition: 0.2s; }
        .cat-btn:hover, .cat-btn.active { background: #f0b90b; color: #000; font-weight: bold; }
        .chat-messages { flex: 1; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
        .message { max-width: 85%; padding: 12px 16px; border-radius: 12px; font-size: 0.95rem; line-height: 1.4; white-space: pre-wrap; }
        .message.bot { background: #1e222d; align-self: flex-start; border: 1px solid #2a2e39; color: #d1d4dc; }
        .message.user { background: #f0b90b; color: #000; align-self: flex-end; font-weight: 500; }
        .news-card img { width: 100%; border-radius: 8px; margin-bottom: 10px; }
        .input-area { padding: 12px; background: #1e222d; border-top: 1px solid #2a2e39; display: flex; gap: 8px; }
        .input-area input { flex: 1; background: #131722; border: 1px solid #2a2e39; padding: 12px 16px; border-radius: 8px; color: #fff; font-size: 0.95rem; outline: none; }
        .input-area input:focus { border-color: #f0b90b; }
        .send-btn { background: linear-gradient(135deg, #f0b90b, #d4a007); border: none; padding: 0 20px; border-radius: 8px; color: #000; font-weight: bold; cursor: pointer; transition: 0.2s; }
        .send-btn:hover { opacity: 0.9; }
    </style>
</head>
<body>

<div class="chat-container">
    <div class="header">
        <h2>🧠 ИИ-помощник & FAQ Master Trade 👑</h2>
        <p>Анализ рынка, новости и ответы на финансовые вопросы!</p>
    </div>

    <div class="tabs">
        <button class="tab-btn active" onclick="switchTab('ai')">🧠 ИИ Помощник</button>
        <button class="tab-btn" onclick="switchTab('news')">📰 Новости Рынка</button>
    </div>

    <div id="news-categories" class="sub-categories" style="display: none;">
        <button class="cat-btn active" onclick="loadNews('all')">🌐 Все</button>
        <button class="cat-btn" onclick="loadNews('forex')">💱 Форекс</button>
        <button class="cat-btn" onclick="loadNews('crypto')">🪙 Крипта</button>
        <button class="cat-btn" onclick="loadNews('stocks')">📈 Акции</button>
        <button class="cat-btn" onclick="loadNews('commodities')">🛢️ Сырье</button>
    </div>

    <div class="chat-messages" id="messages">
        <div class="message bot">
            Привет! 👋 Я ассистент **Master Trade** 👑📊<br><br>
            Помогу разобраться с текущей ситуацией на рынке, подскажу, стоит ли открывать сделки прямо сейчас, и отвечу на любые вопросы по трейдингу. Задавай вопрос ниже! 👇
        </div>
    </div>

    <div class="input-area" id="input-container">
        <input type="text" id="user-input" placeholder="Напишите вопрос или спросите про рынок..." onkeypress="handleKeyPress(event)">
        <button class="send-btn" onclick="sendMessage()">СПРОСИТЬ</button>
    </div>
</div>

<script>
    let currentTab = 'ai';

    function switchTab(tab) {
        currentTab = tab;
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        const messages = document.getElementById('messages');
        
        if (tab === 'ai') {
            event.target.classList.add('active');
            document.getElementById('news-categories').style.display = 'none';
            document.getElementById('input-container').style.display = 'flex';
            messages.innerHTML = `
                <div class="message bot">
                    Привет! 👋 Я ассистент **Master Trade** 👑📊<br><br>
                    Помогу разобраться с ситуацией на рынке и отвечу на любые вопросы! Напишите ваш вопрос ниже 👇
                </div>
            `;
        } else {
            event.target.classList.add('active');
            document.getElementById('news-categories').style.display = 'flex';
            document.getElementById('input-container').style.display = 'none';
            loadNews('all');
        }
    }

    async function sendMessage() {
        const input = document.getElementById('user-input');
        const text = input.value.trim();
        if (!text) return;

        const messages = document.getElementById('messages');
        messages.innerHTML += `<div class="message user">${text}</div>`;
        input.value = '';
        messages.scrollTop = messages.scrollHeight;

        const loadingId = 'loading-' + Date.now();
        messages.innerHTML += `<div class="message bot" id="${loadingId}">⏳ Анализирую рынок... 🚀</div>`;
        messages.scrollTop = messages.scrollHeight;

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });
            const data = await res.json();
            document.getElementById(loadingId).remove();
            messages.innerHTML += `<div class="message bot">${data.response}</div>`;
        } catch (e) {
            document.getElementById(loadingId).remove();
            messages.innerHTML += `<div class="message bot">⚠️ Ошибка получения ответа 🔄</div>`;
        }
        messages.scrollTop = messages.scrollHeight;
    }

    async function loadNews(category) {
        document.querySelectorAll('.cat-btn').forEach(btn => btn.classList.remove('active'));
        if(event && event.target) event.target.classList.add('active');

        const messages = document.getElementById('messages');
        messages.innerHTML = `<div class="message bot">⏳ Генерирую свежую сводку новостей... 🚀</div>`;

        try {
            const res = await fetch('/api/news', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ category: category })
            });
            const data = await res.json();
            messages.innerHTML = `
                <div class="message bot news-card">
                    <img src="${data.image_url}" alt="News Image">
                    <div>${data.response}</div>
                </div>
            `;
        } catch (e) {
            messages.innerHTML = `<div class="message bot">⚠️ Ошибка загрузки новостей 🔄</div>`;
        }
    }

    function handleKeyPress(e) {
        if (e.key === 'Enter') sendMessage();
    }
</script>

</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_LAYOUT)

@app.route("/api/chat", methods=["POST"])
def api_chat():
    user_msg = request.json.get("message", "")
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=user_msg,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
        )
        return jsonify({"response": response.text})
    except Exception as e:
        return jsonify({"response": "⚠️ Произошла ошибка при обработке запроса 🔄"}), 500

@app.route("/api/news", methods=["POST"])
def api_news():
    category = request.json.get("category", "all")
    prompt = f"Сформируй 2 актуальные главные новости для категории: {category}. Каждая новость должна содержать заголовок, краткий разбор влияния на рынок и вердикт с эмодзи."
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
        )
        encoded_prompt = urllib.parse.quote(f"financial trading news chart {category} neon 8k")
        seed = os.urandom(4).hex()
        image_url = f"https://pollinations.ai/p/{encoded_prompt}?width=800&height=450&seed={seed}"
        
        return jsonify({"response": response.text, "image_url": image_url})
    except Exception as e:
        return jsonify({"response": "⚠️ Не удалось получить новости 🔄", "image_url": ""}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
