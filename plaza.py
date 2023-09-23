import io, os, sys, argparse, html, re, configparser, zlib, base64, xml.etree.cElementTree as ET
from PIL import Image
from datetime import datetime

# --------------------------------------------------
# Constants

img_path = "icons/"
max_path_len = 10000
topic_image_size = (128, 128)
post_image_size = (320, 120)

# --------------------------------------------------
# Arguments

parser = argparse.ArgumentParser(description="WaraWara Plaza XML Generator v0.1")
parser.add_argument("-i", "--input", help="configuration file", default="config.ini")
parser.add_argument(
    "-o", "--output", help="output file", nargs="?", default=None, const="1stNUP.xml"
)
parser.add_argument("-f", "--force", help="force overwrite", action="store_true")
args = parser.parse_args()

if not os.path.isfile(args.input):
    sys.exit(f"{args.input} not found")

if args.output and os.path.isfile(args.output) and not args.force:
    if input(f"{args.output} exists, overwrite (Y/N) ? ").upper() != "Y":
        sys.exit("Aborted")

# --------------------------------------------------
# Helpers


def hex_to_dec(v):
    return str(int(v, 16)) if v[0] == "0" else v


def dec_to_hex(v):
    return hex(int(v)).replace("0x", "00") if re.search("^\d+$", v) else "0"


def strip_quotes(v):
    return v.strip("\"' \t\r\n")


def split_str(v):
    return strip_quotes(v).split("\n")


def now_if_empty(v):
    return v or datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def image_paths(v):
    v1 = strip_quotes(v)
    v2 = hex_to_dec(v1)
    v3 = dec_to_hex(v2)
    return [
        v1,
        f"{img_path}{v1}.tga",
        f"{img_path}{v1}.png",
        f"{img_path}{v2}.tga",
        f"{img_path}{v2}.png",
        f"{img_path}{v3}.tga",
        f"{img_path}{v3}.png",
    ]


def valid_image_path(v):
    paths = list(filter(os.path.isfile, image_paths(v)))
    if len(paths) == 0:
        sys.exit(f"Invalid image: {v}")
    return paths[0]


def image_bytes(path, size):
    b = io.BytesIO()
    with Image.open(path) as im:
        im = im.convert("RGBA")
        im = im.resize(size)
        im.save(b, format="TGA", compression=None)
    return b.getvalue()


def encode_image(value, size):
    if len(value) > max_path_len:
        return value
    data = image_bytes(valid_image_path(value), size)
    return base64.b64encode(zlib.compress(data, 6)).decode("ascii")


def topic_image(value):
    return encode_image(value, topic_image_size)


def post_image(value):
    return encode_image(value, post_image_size)


def default_elements(target, source):
    for key, val in source.items():
        ET.SubElement(target, key).text = val
    return target


def optional_text(element, sub, text):
    e = element.find(sub)
    if e != None:
        e.text = text


# --------------------------------------------------
# Classes


class Topic:
    def __init__(self, data):
        self.name = data.get("name")
        self.title_id = hex_to_dec(data.get("title_id"))
        self.community_id = data.get("community_id", "0")
        self.is_recommended = data.get("is_recommended", "0")
        self.icon = topic_image(data.get("icon", self.title_id))
        self.reply_count = data.get("reply_count", "0").split(",")
        self.posts = [html.unescape(item) for item in split_str(data.get("posts"))]


class Person:
    def __init__(self, mii, screen_name=""):
        self.mii = mii
        self.screen_name = screen_name


# --------------------------------------------------
# Parse config

config = configparser.ConfigParser()
config.read(args.input)

result_default = config["result.default"]
topic_default = config["topic.default"]
post_default = config["post.default"]
painting_default = config["painting.default"]

topic_data = [Topic(config[f"topic.{i}"]) for i in range(0, 10)]
people_data = [
    Person(*item.split(" ")) for item in split_str(config["people"].get("person"))
]
people_index = 0

# --------------------------------------------------
# XML Elements


def next_person():
    global people_index
    person = people_data[people_index % len(people_data)]
    people_index += 1
    return person


def post_painting(post, body):
    has_image = os.path.isfile(body)
    p = post.find("painting")
    if has_image and p == None:
        p = ET.SubElement(post, "painting")
    if p != None:
        default_elements(p, painting_default)
    if has_image:
        post.find("body").text = ""
        p.find("content").text = post_image(body)
    return post


def person_element(body, reply_count=0):
    person = ET.Element("person")
    posts = ET.SubElement(person, "posts")
    post = ET.SubElement(posts, "post")
    default_elements(post, post_default)
    data = next_person()
    post.find("body").text = body
    post.find("mii").text = data.mii
    post.find("screen_name").text = data.screen_name
    post.find("created_at").text = now_if_empty(post.find("created_at").text)
    post_painting(post, body)
    optional_text(post, "reply_count", reply_count)
    return person


def topic_element(data: Topic):
    topic = ET.Element("topic")
    default_elements(topic, topic_default)
    topic.find("icon").text = data.icon
    topic.find("name").text = data.name
    topic.find("title_id").text = data.title_id
    topic.find("is_recommended").text = data.is_recommended
    topic.find("modified_at").text = now_if_empty(topic.find("modified_at").text)
    optional_text(topic, "community_id", data.community_id)
    p = topic.find("people")
    for i, body in enumerate(data.posts):
        p.append(person_element(body, data.reply_count[i % len(data.reply_count)]))
    return topic


def result_element():
    result = ET.Element("result")
    default_elements(result, result_default)
    topics = result.find("topics")
    for data in topic_data:
        topics.append(topic_element(data))
    return result


# --------------------------------------------------
# Output

tree = ET.ElementTree(result_element())
ET.indent(tree, space="  ", level=0)
xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(
    tree.getroot(), encoding="utf-8", method="xml", short_empty_elements=False
).decode("ascii")

if args.output != None:
    with open(args.output, "w") as f:
        f.write(xml)
    print(f"Generated {args.output} from {args.input}")
else:
    print(xml)
