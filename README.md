# WaraWara Plaza XML Generator v0.3

**USE AT YOUR OWN RISK - EDITING NAND CAN BRICK YOUR SYSTEM - READ ALL INSTRUCTIONS & GBATEMP THREAD FIRST**

- Simple topic & post editing
- Link icons & paintings to local images
- Automatic image conversion and sizing
- Convert from `ini` to `xml` and back

## Requirements

- [Python](https://www.python.org/downloads/)
- [Pillow](https://pillow.readthedocs.io/en/latest/installation.html#basic-installation)

## Usage

```pwsh
# ini to xml
python plaza.py config.ini 1stNUP.xml

# xml to ini
python plaza.py 1stNUP.xml config.ini
# Note: this creates ./images/ for exported assets

# use -f to force overwrite
python plaza.py -f 1stNUP.xml config.ini
```

## Walkthrough

First you will need to generate a `config.ini`, either from your own XML or one of the `samples/` provided:

- `1stNUP.base.xml` - As seen in the GBATEMP thread
- `1stNUP.default.xml` - From a factory reset WiiU
- `1stNUP.min.xml` - Custom trimmed XML

I recommend using the `min.xml` as it contains only the essential items and produces the smallest XML:

```pwsh
python plaza.py samples/1stNUP.min.xml test/config.ini
```

The file `test/config.ini` will be created, as well as the folder `test/images` which contains the exported images. Edit the `topic.#` sections in `test/config.ini` to change what gets displayed:

### Topics

```ini
[topic.0]
title_id = 0005000012345678
name = MyTitle
icon = images/myicon.png
posts = "
    My Post Content 1
    My Post Content 2
    images/myimage.png
    "
```

- `title_id` corresponds to the game, may be hex or dec format
- `name` may contain specials [', ", #, /]
- `icon` path to an image, if empty will search `images/` for title_id
- `posts` each line contains a separate message (should be ~60 characters to prevent cropping), or a path to an image

Topic icons may be copied from the WiiU directly, for example:
- `/storage_usb/usr/title/00050000/12345678/meta/iconTex.tga`

All images are run through the image library which resizes & converts them as necessary, so in theory *any* image size and format can be used.

When you're done editing generate XML for deployment:

```pwsh
python plaza.py test/config.ini test/1stNUP.xml
```

## Advanced Configuration

### Plaza

```ini
[plaza]
quirks = 0
quotes = 0
disinherit = 1
prune = 1
```

- `quirks` generates 1:1 *default* xml, which has formatting errors
- `quotes` generates very close *base* xml, which has unnecessary `&quot;`
- `disinherit` generates very close *base* xml, which omits `title_id` from posts
- `prune` removes xml elements that are empty or contain "0"

The only important setting `prune`, the others are purley for legacy xml reproduction.

### People

```ini
[people]
person = "
    AwAAQJkt7s+FJgPA1sdZ9YphpRp2gAAAgl... ScreenName1
    AwAAME4NX6Ef9jiRlZ8zCEDSiojFNQAAqG... ScreenName2
    "
```

- `person` each line contains a separate `mii` code plus an optional screen name separate by a space (no spaces allowed in the name)

People are selected for topic posts in the order they appear. The mii code is not editable as it is protected by a checksum. Note that screen names are not actually used...

### Defaults

```ini
[result.default]
# data for the root result element, should probably leave as-is

[topic.default]
# defaults for all topics
modified_at =
# if empty will use the current datetime

[post.#]
# used if a post has unique values, such as replay_count or feeling_id

[post.default]
# defaults for all posts
created_at =
# if empty will use the current datetime

[post.painting]
# defaults for all post paintings

[post.data]
# defaults for all post data

[screenshot.default]
# defaults for all post screenshots

[topic_tag.default]
# defaults for all post topic_tag
```

These sections contain default values for the XML - some are *essential*, but many may be omitted and the XML will still work fine.

## Potential Issues

Be sure to read the GBATEMP thread before using this XML, there *may* be complications with WiiU's that have never been on the Miiverse.

Improperly formatted image content prevents the XML element from being recognised:

  - For Mii pictures this means the Mii will simply not appear
  - For Topic icons this means the Plaza will **freeze**

I had freezes occur many times during development. Using Tiramisu on a 5.5.5 E WiiU I simply hard-reboot into the homebrew launcher (hold X while powering on) and replaced the XML with the last good version.

I have experienced no freezes since I added the image library to the script.

## Credits

Thanks to MikaDubbz & CaramelKat for making this possible

- [gbatemp](https://gbatemp.net/threads/i-permanently-gave-wara-wara-plaza-life-again-injected-it-full-of-my-personality-and-you-can-too.562257) - technique founder and guide
- [WaraWaraPlazaBase64Encoder](https://github.com/CaramelKat/WaraWaraPlazaBase64Encoder) - image formatting
- [archiverse](https://archiverse.guide/) - miiverse backup, great paintings in here