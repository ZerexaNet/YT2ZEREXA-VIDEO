import os
import json
import hashlib
import requests
from tqdm import tqdm
from yt_dlp import YoutubeDL

BASE_URL = "https://video.zerexa.cn"
CONFIG_FILE = "config.json"
CHUNK_SIZE = 8 * 1024 * 1024


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
    return {
        "Authorization": f"Bearer {token}",
    }


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


def download_video(url, out_dir="downloads", cookies=None):
    os.makedirs(out_dir, exist_ok=True)

    opts = {
        "outtmpl": f"{out_dir}/%(title).80s.%(ext)s",
        "format": "bv*+ba/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
    }

    if cookies:
        opts["cookiefile"] = cookies

    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)

        filename = ydl.prepare_filename(info)
        filename = os.path.splitext(filename)[0] + ".mp4"

        title = info.get("title") or "未命名视频"
        description = info.get("description") or ""
        source_url = info.get("webpage_url") or url

        return filename, title, description, source_url


def login(username, password):
    res = requests.post(
        f"{BASE_URL}/api/auth/login_api",
        json={
            "username": username,
            "password": password
        },
        timeout=30,
    )

    if not res.ok:
        print("登录失败，状态码：", res.status_code)
        print("后端返回：", res.text)
        raise RuntimeError("登录失败")

    data = res.json()

    if not data.get("success"):
        raise RuntimeError(f"登录失败：{data}")

    return data["token"]

def check_hash(token, file_hash):
    res = requests.post(
        f"{BASE_URL}/api/videos/upload/check-hash",
        headers=auth_headers(token),
        json={"hash": file_hash},
        timeout=30,
    )

    res.raise_for_status()
    return res.json()


def init_upload(token, filename):
    res = requests.post(
        f"{BASE_URL}/api/videos/upload/init",
        headers=auth_headers(token),
        json={"filename": os.path.basename(filename)},
        timeout=30,
    )

    res.raise_for_status()
    return res.json()


def proxy_put_upload(token, key, path):
    size = os.path.getsize(path)

    with open(path, "rb") as f, tqdm(
        total=size,
        unit="B",
        unit_scale=True,
        desc="直传上传",
    ) as bar:

        class ProgressReader:
            def read(self, n=-1):
                data = f.read(n)
                bar.update(len(data))
                return data

        res = requests.post(
            f"{BASE_URL}/api/videos/upload/proxy-put",
            params={"key": key},
            headers={
                **auth_headers(token),
                "Content-Type": "application/octet-stream",
            },
            data=ProgressReader(),
            timeout=600,
        )

    res.raise_for_status()


def upload_chunk(token, upload_id, key, part_number, data):
    res = requests.post(
        f"{BASE_URL}/api/videos/upload/chunk",
        params={
            "uploadId": upload_id,
            "key": key,
            "partNumber": part_number,
        },
        headers={
            **auth_headers(token),
            "Content-Type": "application/octet-stream",
        },
        data=data,
        timeout=600,
    )

    res.raise_for_status()
    return res.json()["part"]


def multipart_upload(token, upload_id, key, path):
    parts = []
    size = os.path.getsize(path)

    with open(path, "rb") as f, tqdm(
        total=size,
        unit="B",
        unit_scale=True,
        desc="分片上传",
    ) as bar:
        part_number = 1

        while True:
            chunk = f.read(CHUNK_SIZE)

            if not chunk:
                break

            part = upload_chunk(token, upload_id, key, part_number, chunk)
            parts.append(part)

            bar.update(len(chunk))
            part_number += 1

    return parts


def complete_upload(token, upload_id, key, video_id, parts, title, description, category):
    res = requests.post(
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
        timeout=60,
    )

    res.raise_for_status()
    return res.json()


def finalize_direct_upload(token, key, video_id, title, description, category, source_url, file_hash):
    res = requests.post(
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
        timeout=60,
    )

    res.raise_for_status()
    return res.json()


def move_one(url, manual_category, config, token):
    print(f"\n开始处理：{url}")

    path, title, description, source_url = download_video(
        url,
        cookies=config.get("cookies")
    )

    category = manual_category or detect_category(title, description)

    print(f"标题：{title}")
    print(f"分类：{category}")
    print(f"来源：{source_url}")

    print("正在计算 SHA256...")
    file_hash = sha256_file(path)

    print("正在检查秒传...")
    hash_result = check_hash(token, file_hash)

    if hash_result.get("exists"):
        print("服务器已存在，跳过上传：")
        print(json.dumps(hash_result, ensure_ascii=False, indent=2))

        if not config.get("keep", False):
            os.remove(path)

        return

    print("正在初始化上传...")
    init = init_upload(token, path)

    key = init["key"]
    video_id = init["videoId"]

    if init.get("directUpload"):
        print("使用直传模式...")
        proxy_put_upload(token, key, path)

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
        parts = multipart_upload(token, upload_id, key, path)

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

    if not config.get("keep", False):
        os.remove(path)
        print("已删除本地文件。")


def main():
    config = load_config()

    print("正在登录...")
    token = login(config["username"], config["password"])
    print("登录成功。")

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