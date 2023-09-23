# WaraWara Plaza XML Generator v0.2

**USE AT YOUR OWN RISK - EDITING NAND CAN BRICK YOUR SYSTEM - READ ALL INSTRUCTIONS & GBATEMP THREAD FIRST**

## Usage

Requires:
- [Python](https://www.python.org/downloads/)
- [Pillow](https://pillow.readthedocs.io/en/latest/installation.html#basic-installation)
- May need to run as administrator when installing
- May need to replace `python3` with `python`

```pwsh
# output to terminal
python plaza.py

# default files config.ini 1stNUP.xml
python plaza.py -o

# specify files
python plaza.py -i config.ini -o output.xml

# force output overwrite
python plaza.py -i config.ini -o output.xml -f
```

## Package Contents

- `config/` - sample config
- `icons/` - contains topic icons
- `painting/` - contains post paintings
- `config.ini` - config to generate xml - edit as necessary
- `plaza.py` - this is where the magic happens!
- `README.md` - you are here

## Configuration

### Topics

```ini
[topic.0]
name = YourTitleHere
title_id = 0000000000000001
icon = images/icon.tga
is_recommended = 0
posts = "
    My Post Content 1
    My Post Content 2
    My Post Content 3
    "
```

Requires `[topic.0]` through `[topic.9]`
- `name` may contain specials [', ", #, /]
- `title_id` may be hex or dec format (converted to dec for XML)
- `community_id` (optional) community id
- `icon` (optional) path to image (any format), or pre-formatted base64 tga (not recommended)
- `is_recommended` (optional) set to 1 to display a highlighted frame
- `reply_count` (optional) comma delimited count for post replies (not recommended)
- `feeling_id` (optional) comma delimited ids for post feelings (not recommended)
- `posts` each line contains a separate message

If `icon` is omitted the `icons/` folder will be scanned for [png, tga] files matching the `title_id` [dec, hex] - the XML will not build if no image is found.

The `community_id`, `reply_count` and `feeling_id` are used to generate XML similar to the original XML, and are not required for normal use.

Posts should be around 60 characters, anything over usually gets cropped.

### People

```ini
[people]
person = "
    AwAAQJkt7s+FJgPA1sdZ9YphpRp2gAAAgl... ScreenName1
    AwAAME4NX6Ef9jiRlZ8zCEDSiojFNQAAqG... ScreenName2
    "
```

- `person` each line contains a separate `mii` code plus screen name separate by a space (no spaces allowed in the name)

People are selected for topic posts in the order they appear. The mii code is not editable as it is protected by a checksum. Note that screen names are not actually used - there must be a separate list somewhere...

### Defaults

```ini
[result.default]
[topic.default]
[post.default]
[painting.default]
[data.default]
[screenshot.default]
[topic_tag.default]
...
```

These sections contain default values for the XML - some are *essential*, but many may be omitted and the XML will still work fine.

- `modified_at` if empty will use the current datetime
- `created_at` if empty will use the current datetime

## Config

- `config/base.ini` generates *near-identical* XML to the orignal GBATEMP thread
  - Some image base64 code is different
  - Some special characters in the post body dont require escaping
  - Post title_ids now match topic title_ids
- `config/original.ini` generates *near-identical* XML to a factory reset WiiU
  - Empty lines and incorrect indentation fixed
- `config.ini` generates heavily trimmed XML with example content

## Images

Topic icon images may be copied from the WiiU directly, for example:
- `/storage_usb/usr/title/0050000/********/meta/iconTex.tga`

All images are run through the image library to resize & convert them as necessary, so in theory *any* image size and format can be used.

## Known Limitations

- WiiU requires XML to have full closing `<tags></tags>` - short-hand `<tags />` are not allowed
- Improperly formatted image content prevents the parent element from being recognised:
  - For Mii pictures this means the Mii simply will not appear
  - For Topic icons this means the Plaza will **freeze**

If the system freezes hard-reboot into the homebrew launcher (with Tiramisu hold X while powering on) and replace the XML with the last good version.

## Credits

Thanks to MikaDubbz & CaramelKat for making this possible

- [gbatemp](https://gbatemp.net/threads/i-permanently-gave-wara-wara-plaza-life-again-injected-it-full-of-my-personality-and-you-can-too.562257) - technique founder and guide
- [WaraWaraPlazaBase64Encoder](https://github.com/CaramelKat/WaraWaraPlazaBase64Encoder) - image formatting
- [archiverse](https://archiverse.guide/) - miiverse backup, great paintings in here