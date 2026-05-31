import hashlib
import json
import mimetypes
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import unquote, urlparse

import requests
from tqdm import tqdm
from yt_dlp import YoutubeDL

BASE_URL = "https://video.zerexa.cn"
CONFIG_FILE = "config.json"
SMALL_FILE_LIMIT = 100 * 1024 * 1024
CHUNK_SIZE = 8 * 1024 * 1024
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

SESSION = requests.Session()
SESSION.trust_env = False


CATEGORY_LIST = [
    "General / Vlog", "General / Daily", "General / Other",
    "Tech / Programming", "Tech / AI", "Tech / Hardware", "Tech / Mobile", "Tech / Cybersecurity",
    "Music / Original", "Music / Cover", "Music / Instrumental", "Music / MV", "Music / Live",
    "Games / Gameplay", "Games / Esports", "Games / Review", "Games / Mobile Games", "Games / Indie",
    "Life / Cooking", "Life / Fitness", "Life / Home", "Life / Relationships", "Life / Pets",
    "Entertainment / Variety", "Entertainment / Reaction", "Entertainment / Challenge", "Entertainment / Prank", "Entertainment / Unboxing",
    "Sports / Football", "Sports / Basketball", "Sports / Outdoor", "Sports / Martial Arts", "Sports / Extreme",
    "Food / Recipe", "Food / Restaurant", "Food / Street Food", "Food / Baking", "Food / Drinks",
    "Travel / City", "Travel / Nature", "Travel / Road Trip", "Travel / International", "Travel / Tips",
    "Fashion / Outfit", "Fashion / Makeup", "Fashion / Skincare", "Fashion / Haul", "Fashion / Styling",
    "Education / Science", "Education / History", "Education / Language", "Education / Math", "Education / DIY",
    "News / World", "News / Tech News", "News / Finance", "News / Politics", "News / Environment",
    "Anime / Review", "Anime / AMV", "Anime / Discussion", "Anime / Cosplay", "Anime / Manga",
    "Film / Review", "Film / Short Film", "Film / Behind the Scenes", "Film / Documentary", "Film / Trailer",
    "Comedy / Sketch", "Comedy / Stand-up", "Comedy / Memes", "Comedy / Parody", "Comedy / Satire", "Comedy / Abstract",
    "Fitness / Workout", "Fitness / Yoga", "Fitness / Nutrition", "Fitness / Weight Loss", "Fitness / Running",
    "Science / Physics", "Science / Biology", "Science / Space", "Science / Chemistry", "Science / Engineering",
    "Cars / Review", "Cars / Modification", "Cars / Racing", "Cars / EV", "Cars / Maintenance"
]


CATEGORY_KEYWORDS = {
    "Tech / AI": ["ai", "gpt", "chatgpt", "人工智能", "机器学习", "深度学习", "llm"],
    "Tech / Programming": ["python", "java", "c++", "编程", "代码", "程序", "开发", "programming", "coding"],
    "Tech / Hardware": ["cpu", "gpu", "显卡", "处理器", "硬件", "主板", "内存"],
    "Tech / Mobile": ["iphone", "android", "手机", "小米", "华为", "三星", "pixel"],
    "Tech / Cybersecurity": ["网络安全", "黑客", "漏洞", "渗透", "security", "hacker"],
    "Games / Gameplay": ["gameplay", "实况", "通关", "我的世界", "minecraft", "原神", "游戏"],
    "Games / Esports": ["电竞", "比赛", "esports", "tournament"],
    "Games / Review": ["游戏评测", "game review"],
    "Games / Mobile Games": ["手游", "mobile game"],
    "Games / Indie": ["独立游戏", "indie game"],
    "Music / Original": ["原创歌曲", "original song"],
    "Music / Cover": ["cover", "翻唱"],
    "Music / Instrumental": ["instrumental", "纯音乐", "伴奏"],
    "Music / MV": ["mv", "music video"],
    "Music / Live": ["live", "演唱会", "现场"],
    "Anime / AMV": ["amv"],
    "Anime / Review": ["番剧", "动画评测", "anime review"],
    "Anime / Discussion": ["动漫讨论", "anime discussion"],
    "Anime / Cosplay": ["cosplay"],
    "Anime / Manga": ["漫画", "manga"],
    "Film / Trailer": ["trailer", "预告片"],
    "Film / Review": ["影评", "movie review", "film review"],
    "Film / Documentary": ["纪录片", "documentary"],
    "Film / Short Film": ["短片", "short film"],
    "Food / Recipe": ["recipe", "菜谱", "做饭", "烹饪"],
    "Food / Restaurant": ["餐厅", "restaurant"],
    "Food / Street Food": ["街头美食", "street food"],
    "Food / Baking": ["烘焙", "baking"],
    "Food / Drinks": ["饮品", "drink", "coffee"],
    "Travel / City": ["城市旅行", "city tour"],
    "Travel / Nature": ["自然", "风景", "nature"],
    "Travel / Road Trip": ["自驾", "road trip"],
    "Travel / International": ["出国", "international travel"],
    "Travel / Tips": ["旅行攻略", "travel tips"],
    "Education / Science": ["科普", "science"],
    "Education / History": ["历史", "history"],
    "Education / Language": ["英语", "语言", "language"],
    "Education / Math": ["数学", "math"],
    "Education / DIY": ["diy", "手工", "教程"],
    "News / Tech News": ["科技新闻", "tech news"],
    "News / Finance": ["财经", "finance"],
    "News / Politics": ["政治", "politics"],
    "News / Environment": ["环境", "environment"],
    "News / World": ["新闻", "news"],
    "Comedy / Memes": ["meme", "梗", "鬼畜"],
    "Comedy / Sketch": ["短剧", "sketch"],
    "Comedy / Stand-up": ["脱口秀", "stand-up"],
    "Comedy / Parody": ["恶搞", "parody"],
    "Comedy / Satire": ["讽刺", "satire"],
    "Fitness / Workout": ["健身", "workout"],
    "Fitness / Yoga": ["瑜伽", "yoga"],
    "Fitness / Nutrition": ["营养", "nutrition"],
    "Fitness / Weight Loss": ["减肥", "weight loss"],
    "Fitness / Running": ["跑步", "running"],
    "Sports / Football": ["足球", "football", "soccer"],
    "Sports / Basketball": ["篮球", "basketball", "nba"],
    "Sports / Outdoor": ["户外", "outdoor"],
    "Sports / Martial Arts": ["武术", "格斗", "martial arts"],
    "Sports / Extreme": ["极限运动", "extreme sports"],
    "Science / Physics": ["物理", "physics"],
    "Science / Biology": ["生物", "biology"],
    "Science / Space": ["太空", "宇宙", "space"],
    "Science / Chemistry": ["化学", "chemistry"],
    "Science / Engineering": ["工程", "engineering"],
    "Cars / Review": ["汽车评测", "car review"],
    "Cars / Modification": ["改装车", "modification"],
    "Cars / Racing": ["赛车", "racing"],
    "Cars / EV": ["电车", "新能源", "ev", "tesla"],
    "Cars / Maintenance": ["修车", "保养", "maintenance"],
}


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def resolve_file_path(path):
    if not path:
        return None
    if os.path.isabs(path):
        return path
    if os.path.exists(path):
        return path
    return os.path.join(SCRIPT_DIR, path)


def resolve_cookie_file(config):
    configured = (config.get("cookies") or "").strip()
    configured_path = resolve_file_path(configured)
    if configured_path and os.path.exists(configured_path):
        return configured_path

    local_cookie = os.path.join(SCRIPT_DIR, "cookies.txt")
    if os.path.exists(local_cookie):
        return local_cookie
    return None


def resolve_auth_cookie_file(config):
    configured = (
        config.get("auth_cookies")
        or config.get("auth_cookie_file")
        or config.get("zerexa_cookies")
        or ""
    ).strip()
    configured_path = resolve_file_path(configured)
    if configured_path and os.path.exists(configured_path):
        return configured_path

    local_cookie = os.path.join(SCRIPT_DIR, "zerexa_cookies.txt")
    if os.path.exists(local_cookie):
        return local_cookie
    return None


def is_jwt_like(value):
    value = (value or "").strip()
    return value.count(".") == 2 and value.startswith("eyJ") and len(value) > 40


def token_from_json_cookie(data):
    if isinstance(data, dict):
        if data.get("name") == "token" and data.get("value"):
            return data["value"]
        for key in ("cookies", "items"):
            token = token_from_json_cookie(data.get(key))
            if token:
                return token
        return None
    if isinstance(data, list):
        for item in data:
            token = token_from_json_cookie(item)
            if token:
                return token
    return None


def extract_auth_token_from_cookie_file(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read().strip()
    if not text:
        raise RuntimeError(f"站点 cookie 文件为空：{path}")

    if is_jwt_like(text):
        return text

    if text.startswith("{") or text.startswith("["):
        try:
            token = token_from_json_cookie(json.loads(text))
            if token:
                return unquote(str(token).strip())
        except json.JSONDecodeError:
            pass

    for segment in text.replace("\n", ";").split(";"):
        segment = segment.strip()
        if segment.startswith("token="):
            return unquote(segment.split("=", 1)[1].strip())

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 7 and parts[-2] == "token":
            return unquote(parts[-1].strip())

    raise RuntimeError("没有在站点 cookie 文件中找到 token。请从 video.zerexa.cn 登录后导出 token cookie。")


def load_auth_token(config):
    auth_cookie = resolve_auth_cookie_file(config)
    if not auth_cookie:
        raise RuntimeError('缺少站点登录 cookie。请在 config.json 设置 "auth_cookies": "zerexa_cookies.txt"。')

    token = extract_auth_token_from_cookie_file(auth_cookie)
    if not is_jwt_like(token):
        raise RuntimeError("站点 cookie 中的 token 格式不正确，请重新导出。")

    SESSION.cookies.set("token", token, domain="video.zerexa.cn", path="/")
    res = SESSION.get(f"{BASE_URL}/api/users/me", headers=auth_headers(token), timeout=30)
    if not res.ok:
        print("站点 cookie 验证失败，状态码：", res.status_code)
        print("后端返回：", res.text)
        raise RuntimeError("站点 cookie 无效或已过期，请重新登录并导出。")

    data = res.json()
    username = data.get("username") or data.get("user", {}).get("username") or "未知用户"
    uid = data.get("uid") or data.get("user", {}).get("uid") or "-"
    print(f"已导入站点登录 cookie：@{username} (UID: {uid})")
    return token


def detect_category(title, description):
    text = f"{title} {description}".lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text:
                return category
    return "General / Other"


def parse_input(line):
    if "|" in line:
        url, category = line.split("|", 1)
        category = category.strip()
        if category not in CATEGORY_LIST:
            print(f"分类不存在，改为自动分类：{category}")
            category = None
        return url.strip(), category
    return line.strip(), None


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class YDLLogger:
    def debug(self, msg):
        text = str(msg or "").strip()
        if not text:
            return
        if text.startswith("[download]") or text.startswith("[youtube]") or text.startswith("[info]") or text.startswith("[Merger]"):
            print(text)

    def warning(self, msg):
        print(f"[yt-dlp warning] {msg}")

    def error(self, msg):
        print(f"[yt-dlp error] {msg}")


def download_video(url, out_dir="downloads", cookies=None, download_threads=8, proxy=None):
    os.makedirs(out_dir, exist_ok=True)
    last_status = {"value": ""}

    def progress_hook(d):
        status = d.get("status")
        if status == "downloading":
            downloaded = d.get("downloaded_bytes", 0)
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            speed = d.get("speed") or 0
            eta = d.get("eta")
            line = (
                f"[download] {downloaded / 1024 / 1024:.1f}MB"
                + (f"/{total / 1024 / 1024:.1f}MB" if total else "")
                + (f"  {speed / 1024 / 1024:.2f}MB/s" if speed else "")
                + (f"  ETA {eta}s" if eta is not None else "")
            )
        elif status == "finished":
            line = "[download] 下载完成，正在合并/整理文件..."
        else:
            line = f"[download] 状态：{status}"

        if line != last_status["value"]:
            print(line)
            last_status["value"] = line

    opts = {
        "outtmpl": f"{out_dir}/%(title).80s.%(ext)s",
        "format": "bv*+ba/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "concurrent_fragment_downloads": download_threads,
        "continuedl": True,
        "nopart": False,
        "retries": 10,
        "fragment_retries": 10,
        "extractor_retries": 5,
        "socket_timeout": 30,
        "http_chunk_size": 10485760,
        "progress_hooks": [progress_hook],
        "logger": YDLLogger(),
    }
    if cookies:
        opts["cookiefile"] = cookies
    if proxy:
        opts["proxy"] = proxy

    with YoutubeDL(opts) as ydl:
        print("正在解析视频信息...")
        start = time.time()
        info = ydl.extract_info(url, download=False)
        print(f"信息解析完成，用时 {time.time() - start:.1f}s")
        title = info.get("title") or "未命名视频"
        print(f"准备下载：{title}")
        ydl.process_ie_result(info, download=True)
        filename = ydl.prepare_filename(info)
        filename = os.path.splitext(filename)[0] + ".mp4"
        description = info.get("description") or ""
        source_url = info.get("webpage_url") or url
        thumbnail = info.get("thumbnail") or ""
        return filename, title, description, source_url, thumbnail


def check_hash(token, file_hash):
    res = SESSION.post(
        f"{BASE_URL}/api/videos/upload/check-hash",
        headers=auth_headers(token),
        json={"hash": file_hash},
        timeout=60,
    )
    res.raise_for_status()
    return res.json()


def init_upload(token, filename):
    res = SESSION.post(
        f"{BASE_URL}/api/videos/upload/init",
        headers=auth_headers(token),
        json={"filename": os.path.basename(filename)},
        timeout=60,
    )
    res.raise_for_status()
    return res.json()


def get_presign_put_url(token, key):
    res = SESSION.get(
        f"{BASE_URL}/api/videos/upload/presign-put",
        params={"key": key},
        headers=auth_headers(token),
        timeout=60,
    )
    res.raise_for_status()
    data = res.json()
    return data.get("putUrl") or data.get("url")


def direct_put_upload(token, key, path):
    put_url = get_presign_put_url(token, key)
    size = os.path.getsize(path)

    with open(path, "rb") as f, tqdm(
        total=size,
        unit="B",
        unit_scale=True,
        desc="直传上传",
    ) as bar:

        class ProgressReader:
            def __init__(self, raw, total):
                self.raw = raw
                self.total = total

            def read(self, n=-1):
                data = self.raw.read(n)
                bar.update(len(data))
                return data

            def __len__(self):
                return self.total

        res = requests.put(
            put_url,
            data=ProgressReader(f, size),
            headers={
                "Content-Type": "video/mp4",
                "Content-Length": str(size),
            },
            timeout=1800,
        )

    res.raise_for_status()


def pick_image_extension(content_type, image_url):
    guessed = mimetypes.guess_extension((content_type or "").split(";")[0].strip())
    if guessed in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        return ".jpg" if guessed == ".jpe" else guessed

    parsed = urlparse(image_url or "")
    ext = os.path.splitext(parsed.path)[1].lower()
    if ext in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        return ext
    return ".jpg"


def download_thumbnail(image_url, video_path):
    if not image_url:
        return None

    res = SESSION.get(image_url, stream=True, timeout=120)
    res.raise_for_status()

    ext = pick_image_extension(res.headers.get("Content-Type"), image_url)
    image_path = os.path.splitext(video_path)[0] + f".cover{ext}"

    with open(image_path, "wb") as f:
        for chunk in res.iter_content(chunk_size=1024 * 256):
            if chunk:
                f.write(chunk)

    return image_path


def upload_cover(token, video_id, image_path):
    if not image_path or not os.path.exists(image_path):
        return None

    content_type = mimetypes.guess_type(image_path)[0] or "application/octet-stream"
    with open(image_path, "rb") as f:
        res = SESSION.post(
            f"{BASE_URL}/api/videos/{video_id}/cover",
            headers=auth_headers(token),
            files={
                "cover": (
                    os.path.basename(image_path),
                    f,
                    content_type,
                )
            },
            timeout=300,
        )

    res.raise_for_status()
    return res.json()


def upload_chunk(token, upload_id, key, part_number, data):
    last_error = None
    for attempt in range(1, 6):
        try:
            # 获取预签名 URL
            sign_res = SESSION.get(
                f"{BASE_URL}/api/videos/upload/presign-part",
                params={"key": key, "uploadId": upload_id, "partNumber": part_number},
                headers=auth_headers(token),
                timeout=60,
            )
            sign_res.raise_for_status()
            put_url = sign_res.json()["url"]

            # 直接 PUT 到 S3
            res = requests.put(
                put_url,
                data=data,
                headers={
                    "Content-Type": "application/octet-stream",
                    "Content-Length": str(len(data)),
                },
                timeout=1800,
            )
            if not res.ok:
                print(f"分片 {part_number} 上传失败：{res.status_code}")
            res.raise_for_status()
            etag = res.headers.get("ETag", "")
            return {"PartNumber": part_number, "ETag": etag}
        except Exception as e:
            last_error = e
            print(f"分片 {part_number} 第 {attempt}/5 次失败：{e}")
    raise last_error


def multipart_upload(token, upload_id, key, path, threads=4):
    size = os.path.getsize(path)
    total_parts = (size + CHUNK_SIZE - 1) // CHUNK_SIZE
    parts = []

    def read_part(part_number):
        offset = (part_number - 1) * CHUNK_SIZE
        with open(path, "rb") as f:
            f.seek(offset)
            data = f.read(CHUNK_SIZE)
        return part_number, data

    def worker(part_number):
        part_number, data = read_part(part_number)
        part = upload_chunk(token, upload_id, key, part_number, data)
        return part, len(data)

    with tqdm(total=size, unit="B", unit_scale=True, desc=f"分片上传 {threads}线程") as bar:
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = [executor.submit(worker, part_number) for part_number in range(1, total_parts + 1)]
            for future in as_completed(futures):
                part, uploaded_size = future.result()
                parts.append(part)
                bar.update(uploaded_size)

    parts.sort(key=lambda x: x["PartNumber"])
    return parts


def complete_upload(token, upload_id, key, video_id, parts, title, description, category):
    res = SESSION.post(
        f"{BASE_URL}/api/videos/upload/complete",
        headers=auth_headers(token),
        json={
            "uploadId": upload_id,
            "key": key,
            "videoId": video_id,
            "parts": parts,
            "title": title,
            "description": description,
            "category": category,
        },
        timeout=120,
    )
    res.raise_for_status()
    return res.json()


def finalize_direct_upload(token, key, video_id, title, description, category, source_url, file_hash):
    res = SESSION.post(
        f"{BASE_URL}/api/videos/upload/finalize",
        headers=auth_headers(token),
        json={
            "key": key,
            "videoId": video_id,
            "title": title,
            "description": description,
            "category": category,
            "source_url": source_url,
            "file_hash": file_hash,
        },
        timeout=120,
    )
    res.raise_for_status()
    return res.json()


def move_one(url, manual_category, config, token):
    print(f"\n开始处理：{url}")

    cookie_file = resolve_cookie_file(config)
    if cookie_file:
        print(f"使用 cookies：{cookie_file}")

    path, title, description, source_url, thumbnail = download_video(
        url,
        cookies=cookie_file,
        download_threads=config.get("download_threads", 8),
        proxy=config.get("proxy"),
    )

    category = manual_category or detect_category(title, description)
    print(f"标题：{title}")
    print(f"分类：{category}")
    print(f"来源：{source_url}")
    print(f"封面：{thumbnail}")

    cover_path = None
    if thumbnail:
        try:
            print("正在下载封面...")
            cover_path = download_thumbnail(thumbnail, path)
        except Exception as e:
            print(f"封面下载失败，继续上传视频：{e}")

    print("正在计算 SHA256...")
    file_hash = sha256_file(path)

    print("正在检查秒传...")
    hash_result = check_hash(token, file_hash)
    if hash_result.get("exists"):
      print("服务器已存在，跳过上传：")
      print(json.dumps(hash_result, ensure_ascii=False, indent=2))
      if not config.get("keep", False) and os.path.exists(path):
          os.remove(path)
      return

    print("正在初始化上传...")
    init = init_upload(token, path)
    key = init["key"]
    video_id = init["videoId"]
    size = os.path.getsize(path)

    if init.get("directUpload") or size < SMALL_FILE_LIMIT:
        print("使用直传模式...")
        direct_put_upload(token, key, path)
        print("正在写入数据库...")
        result = finalize_direct_upload(
            token=token,
            key=key,
            video_id=video_id,
            title=title,
            description=description,
            category=category,
            source_url=source_url,
            file_hash=file_hash,
        )
    else:
        print("使用分片上传模式...")
        upload_id = init["uploadId"]
        parts = multipart_upload(
            token,
            upload_id,
            key,
            path,
            threads=config.get("upload_threads", 4),
        )
        print("正在完成上传...")
        result = complete_upload(
            token=token,
            upload_id=upload_id,
            key=key,
            video_id=video_id,
            parts=parts,
            title=title,
            description=description,
            category=category,
        )

    print("上传完成：")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if cover_path:
        try:
            print("正在上传封面...")
            cover_result = upload_cover(token, result.get("id") or video_id, cover_path)
            print("封面上传完成：")
            print(json.dumps(cover_result, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"封面上传失败，但视频已成功：{e}")

    if not config.get("keep", False) and os.path.exists(path):
        os.remove(path)
        print("已删除本地文件。")
    if cover_path and (not config.get("keep", False)) and os.path.exists(cover_path):
        os.remove(cover_path)
        print("已删除本地封面文件。")


def main():
    config = load_config()

    print("正在导入站点登录 cookie...")
    token = load_auth_token(config)
    print("站点登录 cookie 验证成功。")

    print("\n请输入视频链接，一行一个。")
    print("可手动指定分类：链接 | 分类名(不填写会自动分类)")
    print("例如：https://www.youtube.com/xxxx | Tech / AI")
    print("输入空行开始执行。\n")

    tasks = []
    while True:
        line = input("> ").strip()
        if not line:
            break
        url, manual_category = parse_input(line)
        if url:
            tasks.append((url, manual_category))

    if not tasks:
        print("没有输入链接。")
        return

    for i, (url, manual_category) in enumerate(tasks, 1):
        print(f"\n========== {i}/{len(tasks)} ==========")
        try:
            move_one(url, manual_category, config, token)
        except Exception as e:
            print(f"处理失败：{url}")
            print(e)

    print("\n全部任务结束。")


if __name__ == "__main__":
    main()
