from glob import glob
import hashlib
import json
import os
import shutil
import datetime
import time

import jinja2
import markdown


jenv = jinja2.Environment(loader=jinja2.FileSystemLoader("static"))

CONFIG_PATH = "config.json"
MANIFEST_PATH = "manifest.json"

CONTENT_PATH = "content"
TEMPLATE_PATH = "static"
PUBLIC_PATH = "docs"

if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
        cfg = json.load(f)

        PUBLIC_PATH = cfg.get("PUBLIC_PATH", PUBLIC_PATH)
        TEMPLATE_PATH = cfg.get("TEMPLATE_PATH", TEMPLATE_PATH)
        CONTENT_PATH = cfg.get("CONTENT_PATH", CONTENT_PATH)


def hash_file(fname):
    h = hashlib.sha256()
    with open(fname, "rb") as f:
        while True:
            b = f.read(h.block_size)
            if not b: break
            h.update(b)
    return h.hexdigest()


def gen_pages(docs):
    print("generating pages...")
    template = jenv.get_template("post.html")
    doc_props = list()
    for d in docs:
        fname = os.path.join(CONTENT_PATH, d, "index.md")

        curtime = time.localtime(time.time())
        with open(fname, "r") as f:
            text = f.read()

        # extract properties in header
        props = dict()
        skipline = 0
        for line in text.split("\n"):
            if not line.startswith("%"): break
            pk, pv = line.split(":", 1)
            pk, pv = pk[1:].strip(), pv.strip()
            props[pk] = pv
            skipline += 1

        if "date" in props:
            date = time.strptime(props["date"], "%Y-%m-%d")
        else:
            date = time.localtime(os.path.getmtime(fname))

        for i, c in enumerate(text):
            if skipline == 0: break
            if c == '\n': skipline -= 1

        body = markdown.markdown(
            text[i:],
            extensions=["fenced_code"],
        )

        fdir = os.path.join(PUBLIC_PATH, d)
        if not os.path.exists(fdir):
            os.mkdir(fdir)

        tfmt = "%Y-%m-%d, %H:%M:%S"

        context = {
            "doc": {
                "date": time.strftime(tfmt, date),
                "time": time.strftime(tfmt, curtime),
                "html": body,
                **props,
            },
        }
        html = template.render(context)

        with open(os.path.join(fdir, "index.html"), "w") as f:
            f.write(html)

        doc_props.append({**props, "date": date, "time": curtime, "id": d})

    return doc_props


def del_pages(keys):
    for k in keys:
        path = os.path.join(PUBLIC_PATH, k)
        if os.path.exists(path):
            shutil.rmtree(path)
        else:
            print(f"warning: did not find directory \"{path}\" to delete")


def gen_toc(doc_props):
    tfmt = "%Y-%m-%d"
    template = jenv.get_template("toc.html")
    context = {
        "toc": sorted([
            {
                "id": k,
                "title": v.get("title", v.get("date", "")),
                "url": f"/{k}",
                "date": time.strftime(tfmt, time.struct_time(v["date"])),
                "desc": v["desc"],
            }
            for k, v in doc_props.items()
        ], key=lambda x: ["date"]),
    } if len(doc_props) != 0 else dict()

    html = template.render(context)

    with open(os.path.join(PUBLIC_PATH, "index.html"), "w") as f:
        f.write(html)


def main():
    print("building site...")

    if not os.path.exists(PUBLIC_PATH):
        os.mkdir(PUBLIC_PATH)

    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, "r") as f:
            try:
                manifest = json.load(f)
            except Exception as e:
                print("error: failed to load manifest; reason: " + e.what())
                print("starting with a fresh manifest...")
                manifest = dict()
    else:
        print("no manifest found. creating empty manifest.")
        manifest = dict()

    manifest_keys = set(manifest)

    files = glob(os.path.join(CONTENT_PATH, "*", "index.md"))
    found_files = {x.split("/")[1]: {"path": x} for x in files}
    found_keys = set(found_files)

    # print(
    #     f"found {len(files)} article" 
    #     + ("s" if len(files) != 1 else "")
    #     + f" under \"{CONTENT_PATH}\"."
    # )

    common_keys = found_keys & manifest_keys
    new_keys = found_keys - manifest_keys
    del_keys = manifest_keys - found_keys

    found_hashes = {f.split("/")[1]: hash_file(f) for f in files}
    manifest_hashes = {k: v["hash"] for k, v in manifest.items()}

    upd_keys = {
        k for k, v in manifest_hashes.items()
        if k in found_hashes and v != found_hashes[k]
    }

    print(
        f"{len(new_keys)} new post" + ("s" if len(new_keys) != 1 else "")
        + f"; {len(upd_keys)} update" + ("s" if len(upd_keys) != 1 else "")
        + f"; {len(del_keys)} deletion" + ("s" if len(del_keys) != 1 else "") + "."
    )

    if len(del_keys) != 0:
        print(f"deleting {len(del_keys)} pages.")
        del_pages(del_keys)

    if len(new_keys) + len(upd_keys) == 0:
        doc_props = gen_pages(new_keys | upd_keys)
        doc_props = {
            **{k: v for k, v in manifest.items() if k not in del_keys},
            **{doc["id"]: {"hash": found_hashes[doc["id"]], **doc} for doc in doc_props},
        }
    else:
        doc_props = dict()

    print("generating table of contents.")
    gen_toc(doc_props)

    print("writing updated manifest.")
    with open(MANIFEST_PATH, "w") as f:
        json.dump(doc_props, f)

    print("done.")

if __name__ == "__main__":
    main()
