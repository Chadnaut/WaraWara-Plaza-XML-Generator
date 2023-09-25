import io, os, sys, msvcrt, hashlib, argparse, html, re, configparser, zlib, base64, xml.etree.cElementTree as ET
from PIL import Image
from datetime import datetime

# --------------------------------------------------
# Arguments

parser = argparse.ArgumentParser(description="WaraWara Plaza XML Generator v0.1")
parser.add_argument("input", help="input file")
parser.add_argument("output", help="output file")
parser.add_argument("-f", "--force", help="force overwrite", action="store_true")

# --------------------------------------------------
# Globals

args = parser.parse_args()
input_file = args.input
output_file = args.output
input_path_ext = input_file[-3:].lower()
output_path_ext = output_file[-3:].lower()
force_overwrite = args.force
output_dir = os.path.dirname(output_file) + "/"

image_path = "images/"
max_path_len = 10000
topic_image_size = (128, 128)
post_image_size = (320, 120)
zlib_level = 6
topic_count = 10
CR = "\n"

config = configparser.ConfigParser(allow_no_value=True)
post_index = 0

result_defaults = {
    "version": "1",
    "request_name": "topics",
    "expire": "2100-01-01 10:00:00",
}

post_painting_defaults = {
    "format": "tga",
    "content": "",
    "size": "153618",
}

# --------------------------------------------------
# General Helpers


def is_dec(text):
    return text != None and re.search("^\d+$", text) != None


def hex_to_dec(text):
    """Convert hex to decimal if text starts with 0, otherwise return text"""
    return str(int(text, 16)) if text != None and len(text) and text[0] == "0" else text


def dec_to_hex(text):
    """Convert decimal to hex if text is all digits, otherwise return 0"""
    return hex(int(text)).replace("0x", "00") if is_dec(text) else "0"


def strip_quotes(text):
    """Strips quotes and spaces from text"""
    return text.strip("\"' \t\r\n")


def split_str(v):
    """Strip quotes plus split text arount carriage-return"""
    return strip_quotes(v).split("\n")


def escape_body(text):
    """Escape post body text from xml"""
    return text.replace("\n", "&#13;").replace('"', "&quot;")


def datetime_now():
    """Return datetime string"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# --------------------------------------------------
# File Helpers


def create_path(path):
    """Create path if none exists"""
    dir = os.path.dirname(path)
    if not os.path.isdir(dir):
        os.makedirs(dir, exist_ok=True)
    return path


def can_overwrite(path):
    """Prompt to overwrite if path exists, unless arg.force is True"""
    if not os.path.isfile(path) or force_overwrite:
        return True
    print(f"{path} exists, overwrite (Y/N)? ", end="", flush=True)
    while True:
        if msvcrt.kbhit():
            key_stroke = msvcrt.getch().decode("utf-8").lower()
            if key_stroke == "y" or key_stroke == chr(13):
                print("Y")
                return True
            print("N")
            return False


# --------------------------------------------------
# Image Helpers


def image_paths(v):
    """Create a list of possible image paths"""
    v1 = strip_quotes(v)
    v2 = hex_to_dec(v1)
    v3 = dec_to_hex(v2)
    return [
        f"{output_dir}{v1}",
        f"{output_dir}{image_path}{v1}.tga",
        f"{output_dir}{image_path}{v1}.png",
        f"{output_dir}{image_path}{v2}.tga",
        f"{output_dir}{image_path}{v2}.png",
        f"{output_dir}{image_path}{v3}.tga",
        f"{output_dir}{image_path}{v3}.png",
    ]


def get_valid_image(v):
    """Return first valid path, or None"""
    paths = list(filter(os.path.isfile, image_paths(v)))
    return paths[0] if len(paths) else None


def image_bytes(path, size):
    """Return formatted image as TGA bytes"""
    b = io.BytesIO()
    with Image.open(path) as im:
        im = im.convert("RGBA")
        im = im.resize(size)
        im.save(b, format="TGA", compression=None)
    return b.getvalue()


def encode_image(value, size):
    """Encode image for xml embedding"""
    if value == None:
        sys.exit("Missing image")
    if len(value) > max_path_len:
        return value
    path = get_valid_image(value)
    if path == None:
        sys.exit(f"Invalid image: {value}")
    return base64.b64encode(zlib.compress(image_bytes(path, size), zlib_level)).decode()


def export_image(value, path):
    """Decode embedded image and save to path"""
    export_path = f"{output_dir}{path}"
    if can_overwrite(export_path):
        with Image.open(io.BytesIO(zlib.decompress(base64.b64decode(value)))) as im:
            im.save(create_path(export_path))
    return path


# --------------------------------------------------
# INI Helpers


def get_config_section(section):
    """Return config section if it exists, or None"""
    return config[section] if config.has_section(section) else None


def prune_config(config):
    """Remove sections that do not have options"""
    for section in list(config):
        s = get_config_section(section)
        if s == None or len(s) == 0:
            config.remove_section(section)


def add_config_section(section, element, skip=[]):
    """Create a new config section and fill with element tag & text values"""
    if not config.has_section(section):
        config.add_section(section)
    for e in list(element):
        text = "" if len(e) > 0 or e.text == None or e.tag in skip else e.text
        config.set(section, e.tag, text.strip())
    return get_config_section(section)


def add_config_default(section, elements=[], skip=[]):
    """Create a default config section using first element and clear matching section with identical values"""
    for element in reversed(list(elements)):
        default = add_config_section(f"{section}.default", element, skip)
    for i in range(0, len(elements)):
        for key in default:
            name = f"{section}.{i}"
            if (
                config.has_section(name)
                and config.has_option(name, key)
                and config.get(name, key) == default[key]
            ):
                config.remove_option(f"{section}.{i}", key)
    return default


def add_section_icon(section, option, element):
    """Create icon option from topic element"""
    icon = element.find("icon").text.strip()
    title_id = element.find("title_id").text.strip()
    config.set(section, option, export_image(icon, f"{image_path}{title_id}.png"))


def add_section_posts(section, option, elements):
    """Create list of body / images from post elements"""
    items = []
    for post in elements:
        painting = get_sub_text(post, "painting/content")
        body = get_sub_text(post, "body", "")
        items.append(
            export_image(
                painting,
                f"{image_path}painting.{hashlib.md5(painting.encode()).hexdigest()}.png",
            )
            if painting
            else escape_body(body)
        )
    config.set(section, option, f'"{CR}{CR.join(items)}{CR}"')


def add_section_people(section, option, elements):
    """Create list of mii / screen_name from post elements"""
    person = []
    for post in elements:
        mii = get_sub_text(post, "mii", "")
        screen_name = get_sub_text(post, "screen_name", "")
        person.append(f"{mii} {screen_name}")
    config.set(section, option, f'"{CR}{CR.join(person)}{CR}"')


# --------------------------------------------------
# XML Helpers


def set_element_section(element, section, ignore=[]):
    """Copy options from section to element subelements"""
    if section != None:
        for key in section:
            if not key in ignore:
                sub = element.find(key)
                if sub == None:
                    sub = ET.SubElement(element, key)
                sub.text = section.get(key)
    return element


def get_subelement(element, name):
    """Return subelement, create if none"""
    sub = element.find(name)
    return sub if sub != None else ET.SubElement(element, name)


def get_sub_text(element, name, default=None):
    """Return subelement text, or default if none"""
    sub = element.find(name)
    return (sub.text if sub != None else default) or default


def set_sub_text(element, name, text):
    """Set subelement text, create subelement if none"""
    if not text == None:
        get_subelement(element, name).text = text


def set_sub_datetime(element, name):
    """Update element text with datetime if it exists and is empty"""
    sub = element.find(name)
    if sub != None and sub.text == "":
        set_sub_text(element, name, datetime_now())


def set_sub_defaults(element, defaults):
    """Set sub text values if they dont exist"""
    for key in defaults:
        if element.find(key) == None:
            set_sub_text(element, key, defaults[key])


# --------------------------------------------------
# XML Elements


def post_painting(element, value):
    """Embed image into post painting content"""
    if get_valid_image(value) != None:
        painting = element.find("painting")
        if painting == None:
            painting = ET.SubElement(element, "painting")
            set_sub_defaults(painting, post_painting_defaults)
        set_sub_text(element, "body", "")
        set_sub_text(painting, "content", encode_image(value, post_image_size))
    return element


def post_additional(element, name, index):
    """Add additional section values to the element"""
    for section in config:
        if section[0:5] == f"{name}.":
            prop = section[5:]
            if prop != "default" and not re.search("^\d+$", prop):
                set_element_section(get_subelement(element, prop), config[section])
    set_element_section(element, get_config_section(f"{name}.{index}"))


def post_inherit(element, source, tags):
    """Copy source values into the element"""
    for tag in tags:
        for e in element.findall(f".//{tag}"):
            e.text = get_sub_text(source, tag)


def person_element(body, topic):
    """Create a person element"""
    global post_index
    people = split_str(get_config_section("people").get("person", ""))
    person = people[post_index % len(people)].split(" ")
    mii = person[0]
    screen_name = person[1] if len(person) > 1 else None
    person = ET.Element("person")
    posts = ET.SubElement(person, "posts")
    post = ET.SubElement(posts, "post")
    set_element_section(post, get_config_section("post.default"))
    set_sub_text(post, "body", body)
    set_sub_text(post, "mii", mii)
    set_sub_text(post, "screen_name", screen_name)
    set_sub_datetime(post, "created_at")
    post_additional(post, "post", post_index)
    post_painting(post, body)
    if get_config_section("plaza").get("disinherit") != "1":
        post_inherit(post, topic, ["title_id", "community_id"])
    post_index += 1
    return person


def topic_element(section):
    """Create topic element from config section"""
    topic = ET.Element("topic")
    set_element_section(topic, get_config_section("topic.default"))
    set_element_section(topic, section, ["posts"])
    title_id = hex_to_dec(get_sub_text(topic, "title_id"))
    icon = encode_image(get_sub_text(topic, "icon") or title_id, topic_image_size)
    set_sub_text(topic, "title_id", title_id)
    set_sub_text(topic, "icon", icon)
    set_sub_datetime(topic, "modified_at")
    people = get_subelement(topic, "people")
    posts = section.get("posts")
    if posts != None:
        for body in [html.unescape(item) for item in split_str(posts)]:
            people.append(person_element(body, topic))
    return topic


def result_element():
    """Create result element from config"""
    result = ET.Element("result")
    set_element_section(result, get_config_section("result.default"))
    set_sub_defaults(result, result_defaults)
    topics = get_subelement(result, "topics")
    for name in [f"topic.{i}" for i in range(0, topic_count)]:
        topic = get_config_section(name)
        if topic == None:
            sys.exit(f"Missing topic: {name}")
        topics.append(topic_element(topic))
    return result


# --------------------------------------------------
# Formatting


def add_quirks(xml):
    """Add malformed XML as found in the original xml"""
    return (
        xml.replace("<topics>", "<topics>\n")
        .replace("              <app_data>", "\n              <app_data>")
        .replace("  </post>", " </post>")
        .replace("</people>", "</people>\n")
        .replace("</topic>", "</topic>\n", 8)
        .replace("  </topics>", "\n  </topics>")
        + "\n"
    )


def add_quotes(xml):
    """Add unnecessary &quot; to xml"""
    return xml.replace('"', "&quot;")


def prune_paintings(element):
    """Remove painting elements that dont have content"""
    for post in element.findall(".//post"):
        for painting in post.findall("painting"):
            content = painting.find("content")
            if content == None or content.text == "":
                post.remove(painting)


def prune_elements(element):
    """Remove empty or zero value elements"""
    for child in list(element):
        if len(child) > 0:
            prune_elements(child)
        else:
            if child.text == None or child.text == "" or child.text == "0":
                element.remove(child)


def has_quirks(path):
    """True if file has malformed xml"""
    with open(path, "r") as f:
        lines = f.readlines()
        for line in lines:
            if line == "\n":
                return True
    return False


def has_quotes(path):
    """Tree if file has &quot;"""
    with open(path, "r") as f:
        lines = f.readlines()
        for line in lines:
            if re.search("&quot;", line):
                return True
    return False


def has_prune(result):
    """False is xml contains empty painting"""
    contents = result.findall("topics/topic/people/person/posts/post/painting/content")
    for content in contents:
        if content.text == None:
            return False
    return True


def has_inherit(result):
    """True if post title_id equals topic title_id"""
    inherit = True
    for topic in result.findall("topics/topic"):
        title_id = get_sub_text(topic, "title_id")
        for post in topic.findall("people/person/posts/post"):
            inherit = inherit and get_sub_text(post, "title_id") == title_id
    return inherit


def create_plaza_xml():
    """Return xml content from global config"""
    plaza = get_config_section("plaza")
    tree = ET.ElementTree(result_element())
    result = tree.getroot()
    if plaza.get("prune") == "1":
        prune_paintings(result)
        prune_elements(result)
    ET.indent(tree, space="  ", level=0)
    xml = ET.tostring(
        result, encoding="utf-8", method="xml", short_empty_elements=False
    ).decode()
    if plaza.get("quirks") == "1":
        xml = add_quirks(xml)
    if plaza.get("quotes") == "1":
        xml = add_quotes(xml)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml


# --------------------------------------------------
# Reading & Writing


def read_plaza_ini(path):
    """Load ini into global config"""
    config.read(path)


def read_plaza_xml(path):
    """Read plaza xml into global config"""
    topic_skip = ["icon", "title_id", "name"]
    post_skip = ["body", "mii", "title_id", "screen_name"]

    tree = ET.parse(path)
    result = tree.getroot()
    topics = result.findall("topics/topic")
    posts = result.findall("topics/topic/people/person/posts/post")

    config.add_section("plaza")
    config.set("plaza", f"; Source: {path}")
    config.set("plaza", f"; Generated: {datetime_now()}")
    config.set("plaza", "quirks", "1" if has_quirks(path) else "0")
    config.set("plaza", "quotes", "1" if has_quotes(path) else "0")
    config.set("plaza", "disinherit", "0" if has_inherit(result) else "1")
    config.set("plaza", "prune", "1" if has_prune(result) else "0")

    for i, topic in enumerate(topics):
        section = f"topic.{i}"
        topic_posts = topic.findall("people/person/posts/post")
        add_config_section(section, topic, ["icon"])
        add_section_icon(section, "icon", topic)
        add_section_posts(section, "posts", topic_posts)

    config.add_section("people")
    add_section_people("people", "person", posts)

    add_config_section("result.default", result)
    add_config_default("topic", topics, topic_skip)

    for i, post in enumerate(posts):
        add_config_section(f"post.{i}", post, post_skip)
    add_config_default("post", posts, post_skip)

    for e in list(filter(len, posts[0])):
        add_config_section(
            f"post.{e.tag}", posts[0].find(e.tag), ["title_id", "content"]
        )

    prune_config(config)


def write_plaza_ini(path):
    """Write config ini to path"""
    if can_overwrite(path):
        with open(create_path(path), "w", encoding="utf-8") as f:
            config.write(f)


def write_plaza_xml(path):
    """Write plaza xml to path"""
    if can_overwrite(create_path(path)):
        xml = create_plaza_xml()
        with open(path, "w") as f:
            f.write(xml)


# --------------------------------------------------
# Main


def main():
    if input_path_ext == "ini":
        read_plaza_ini(input_file)
    elif input_path_ext == "xml":
        read_plaza_xml(input_file)
    else:
        sys.exit(f"Invalid input: {input_file}")

    if output_path_ext == "ini":
        write_plaza_ini(output_file)
    elif output_path_ext == "xml":
        write_plaza_xml(output_file)
    else:
        sys.exit(f"Invalid output: {output_file}")

    print(f"Generated {output_file} from {input_file}")


# --------------------------------------------------

main()
