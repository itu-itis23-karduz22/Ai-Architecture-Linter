import os
import json
import requests
from openai import OpenAI

def get_pr_diff(repo, pr_number, token):
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3.diff"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text

def parse_diff_for_llm(diff_text):
    """
    Trello Task: 'Only the diff + import lines are sent to the LLM'
    Sadece değişen satırları ve 'import/using' ifadelerini filtreleyerek 
    LLM token maliyetini en aza indirir.
    """
    filtered_lines = []
    for line in diff_text.split('\n'):
        # Dosya yollarını (diff header) veya eklenen/çıkarılan satırları al
        if line.startswith('diff --git') or line.startswith('+++') or line.startswith('---'):
            filtered_lines.append(line)
        elif line.startswith('+') or line.startswith('-'):
            filtered_lines.append(line)
        # Değişmeyen ama bağlam için önemli olan import/using satırlarını al
        elif 'import ' in line or 'using ' in line or 'include ' in line:
            filtered_lines.append(line)
            
    return '\n'.join(filtered_lines)

def analyze_with_llm(diff_content, api_key):
    """
    Trello Task: 'API connection was established to the closed-network LLM'
    Trello Task: 'Structured output is obtained from the LLM'
    Groq API (veya uyumlu OpenAI API) üzerinden LLaMa3 modeline istek atar.
    Sonucu zorunlu JSON olarak döndürür.
    """
    # Proje dokümanında Groq LLaMa3 örnek verildiği için base_url Groq kullanılmıştır.
    # Kapalı ağa geçildiğinde buradaki base_url kendi sunucunuza yönlendirilebilir.
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1" 
    )

    system_prompt = (
        "Sen uzman bir yazılım mimarısın. Sana bir Pull Request'in kod değişiklikleri (diff) verilecek.\n"
        "Görevin sadece SOLID prensipleri, Clean Architecture kuralları ve yeni eklenen bağımlılıklar (import) "
        "üzerinden mimari hataları veya teknik borçları bulmaktır. Basit sytnax hatalarını veya stili görmezden gel.\n"
        "ÇIKTINI SADECE AŞAĞIDAKİ JSON FORMATINDA VER. Başka hiçbir metin ekleme:\n"
        "{\n"
        '  "issues_found": true veya false,\n'
        '  "feedback": "Eğer sorun varsa buraya Markdown formatında detaylı tavsiyeni yaz. Yoksa boş bırak."\n'
        "}"
    )

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant", 
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Git Diff Changes:\n{diff_content}"}
        ],
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)

def comment_on_pr(repo, pr_number, token, feedback):
    """
    Trello Task: 'Automated bot comments are being left on PR'
    PR üzerine GitHub Bot ile mimari yorum bırakır.
    """
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    comment_body = (
        "🤖 **AI Architecture Linter Analizi**\n\n"
        "⚠️ Projenin mimari yapısında veya bağımlılıklarında (dependencies) bazı potansiyel sorunlar tespit ettim:\n\n"
        f"{feedback}\n\n"
        "*(Bu otomatik bir mesajdır. Lütfen mimari standartlarımıza uyduğundan emin ol!)*"
    )
    
    data = {"body": comment_body}
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    print("Yorum başarıyla PR'a eklendi!")

def main():
    # Çevresel değişkenleri CI/CD pipeline'dan alıyoruz
    github_token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    llm_api_key = os.environ.get("LLM_API_KEY")

    if not all([github_token, repo, event_path, llm_api_key]):
        raise ValueError("Gerekli tüm çevresel değişkenler (Environment Variables) sağlanmadı!")

    # PR Numarasını GitHub Event JSON dosyasından oku
    with open(event_path, 'r') as f:
        event_data = json.load(f)
    
    # Event bir PR değilse çık
    if "pull_request" not in event_data:
        print("Bu bir Pull Request event'i değil, işlem yapılmıyor.")
        return
        
    pr_number = event_data["pull_request"]["number"]
    print(f"[{repo}] Analiz başlıyor... PR #{pr_number}")

    # 1. Diff'i çek ve Parse et (Trello: PR diff is successfully parsed)
    raw_diff = get_pr_diff(repo, pr_number, github_token)
    parsed_diff = parse_diff_for_llm(raw_diff)
    
    if not parsed_diff.strip():
        print("İncelenecek anlamlı bir kod değişikliği bulunamadı.")
        return

    # 2. LLM'e gönder (Trello: Sadece diff + import gönderiliyor & JSON alınıyor)
    print("Yapay Zekaya bağlantı kuruluyor ve analiz ediliyor...")
    analysis_result = analyze_with_llm(parsed_diff, llm_api_key)

    # 3. Yorum at (Trello: Automated bot comments are being left on PR)
    if analysis_result.get("issues_found"):
        print("Mimari sorunlar bulundu, PR'a yorum atılıyor...")
        comment_on_pr(repo, pr_number, github_token, analysis_result.get("feedback"))
    else:
        print("Mimari bir sorun bulunamadı. PR temiz!")

if __name__ == "__main__":
    main()
